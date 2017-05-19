import random
from hypothesis import given
import hypothesis.strategies
from corpushash.hashers import *
import os
import shutil
import urllib
from bs4 import BeautifulSoup

pwd = os.getcwd()
base_path = os.path.dirname(pwd)
test_path = os.path.join(base_path, 'corpus_test')
try:
    shutil.rmtree(test_path)
except FileNotFoundError:
    pass
os.mkdir(test_path)

urls = ["http://www.humancomp.org/unichtm/calblur8.htm", 
        "http://www.humancomp.org/unichtm/unilang8.htm", 
        "http://www.humancomp.org/unichtm/banviet8.htm", 
        "http://www.humancomp.org/unichtm/croattx8.htm", 
        "http://www.humancomp.org/unichtm/danish8.htm", 
        "http://www.humancomp.org/unichtm/esperan8.htm", 
        "http://www.humancomp.org/unichtm/jpndoc8.htm", 
        "http://www.humancomp.org/unichtm/kordoc8.htm", 
        "http://www.humancomp.org/unichtm/neural8.htm", 
        "http://www.humancomp.org/unichtm/russmnv8.htm", 
        "http://www.humancomp.org/unichtm/sample68.htm", 
        "http://www.humancomp.org/unichtm/huseyin8.htm", 
        "http://www.humancomp.org/unichtm/tongtws8.htm", 
        "http://www.humancomp.org/unichtm/armenia8.htm", 
        "http://www.humancomp.org/unichtm/maopoem8.htm", 
        "http://www.humancomp.org/unichtm/linjilu8.htm", 
        "http://www.humancomp.org/unichtm/ulysses8.htm", 
        "http://www.humancomp.org/unichtm/zenbibl8.htm"]
# from http://www.humancomp.org/unichtm/unichtm.htm

def setup_data():
    test_corpus = []
    for url in urls:
        html = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(html)
        for script in soup(["script", "style"]):  # clean
            script.extract()  # rip it out
        text = soup.get_text()
        split_text = text_split(text)
        test_corpus.append(split_text)
    salt_length = random.randint(1, 33)
    salt_choice = random.choice([True, False])
    encoded_corp = CorpusHash(test_corpus, test_path, salt_length=salt_length, 
                              one_salt=salt_choice)
    return encoded_corp


encoded_corp = setup_data()
print('one_salt is {}'.format(encoded_corp.one_salt))



@given(hypothesis.strategies.text())
def test_hash_token_works(s):
    response = hash_token(s)
    assert response


@given(hypothesis.strategies.text())
def test_hash_token_return_token(s):
    hashed_token, _ = hash_token(s)
    assert isinstance(hashed_token, str)
    assert len(hashed_token) == 40


@given(hypothesis.strategies.text())
def test_hash_token_return_salt(s):
    _, salt = hash_token(s)
    assert isinstance(salt, bytes)


def test_dictionary_length():
    encode_dictionary_length = len(encoded_corp.encode_dictionary)
    assert encode_dictionary_length == len(encoded_corp.decode_dictionary)


def test_encode_dictionary_types():
    token = random.choice(list(encoded_corp.encode_dictionary.keys()))
    hashed_token = encoded_corp.encode_dictionary[token]
    assert isinstance(token, str)
    assert isinstance(hashed_token, str)
    assert len(hashed_token) == 40


def test_decode_dictionary_types():
    hashed_token = random.choice(list(encoded_corp.decode_dictionary.keys()))
    token, salt = encoded_corp.decode_dictionary[hashed_token]
    assert isinstance(hashed_token, str)
    assert len(hashed_token) == 40
    assert isinstance(token, str)
    assert isinstance(salt, str)
#    assert len(salt) == encoded_corp.salt_length


def test_encode_decode_dictionaries():
    """
    Choose 10 random tokens. get its hash in encode_dictionary. get the token 
    and salt in decode_dictionary using the hash found in encode_dictionary. 
    check if tokens and hashed tokens are the same.
    """
    for _ in range(10):
        enc_token = random.choice(list(encoded_corp.encode_dictionary.keys()))
        enc_hashed_token = encoded_corp.encode_dictionary[enc_token]
        dec_token, salt = encoded_corp.decode_dictionary[enc_hashed_token]
        assert enc_token == dec_token
        hashed_token, _ = hash_token(enc_token, salt=base64.b85decode(salt))
        assert hashed_token == enc_hashed_token

def test_loading_dictionaries():
    toy_corpus = random.sample(list(encoded_corp.encode_dictionary.keys()), 15)
    second_encoded_corp = CorpusHash([toy_corpus], test_path)
    for token in toy_corpus:
        hashed_token = second_encoded_corp.encode_dictionary[token]
        correct_token, previous_salt_str = encoded_corp.decode_dictionary[hashed_token]
        salt_in_previous_hashing = base64.b85decode(previous_salt_str.encode())
        correct_hashed_token, _ = hash_token(token, salt=salt_in_previous_hashing)
        assert token == correct_token
        assert correct_hashed_token == hashed_token == encoded_corp.encode_dictionary[token]
        salt = second_encoded_corp.decode_dictionary[hashed_token][1]
        assert previous_salt_str == salt


def test_encoding_using_read_hashed_corpus():
    for encoded_document, decoded_document in zip(encoded_corp.read_hashed_corpus(), 
                                                  encoded_corp.corpus):
        for enc_hashed_token, token in zip(walk_nested_list(encoded_document), 
                                            walk_nested_list(decoded_document)):
            hashed_token = encoded_corp._encode_token(token)
            assert hashed_token == enc_hashed_token


def test_decoding():
    for encoded_document, decoded_document in zip(encoded_corp.read_hashed_corpus(),
                                                       encoded_corp.corpus):
        for enc_hashed_token, token in zip(walk_nested_list(encoded_document), 
                                            walk_nested_list(decoded_document)):
            dec_token, salt = encoded_corp.decode_dictionary[enc_hashed_token]
            assert hash_token(token, salt=base64.b85decode(salt))[0] == enc_hashed_token

def test_one_salt():
    if isinstance(encoded_corp.one_salt, bool) and encoded_corp.one_salt:
        # if all salts are the same
        random_key = random.choice(list(encoded_corp.decode_dictionary.keys()))
        comparison_key = encoded_corp.decode_dictionary[random_key][1]
        for key in encoded_corp.decode_dictionary.keys():
            assert comparison_key == encoded_corp.decode_dictionary[key][1]
    elif isinstance(encoded_corp.one_salt, bool) and not encoded_corp.one_salt:
        # if all salts are different
        comparison_salt = 0
        for key in encoded_corp.decode_dictionary.keys():
            salt = encoded_corp.decode_dictionary[key][1]
            assert comparison_salt != salt
            comparison_salt = salt


def test_corpus_size():
    assert encoded_corp.corpus_size == len(os.listdir(encoded_corp.public_path))
