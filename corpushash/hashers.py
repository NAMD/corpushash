import os
import hashlib
import pickle
import copy
import json
import base64
import datetime
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class CorpusHash:
    """
    turns a tokenized corpus (nested list) into a nested list of the hashes of 
    its tokens. creates a /public and a /private folder in a specified path; in 
    the former the hashed documents are stored in plaintext as a .json, and in 
    the latter the encoding and decoding dictionaries are kept as a pickle.
       you can hash documents from the same corpus at different times using the 
    same dictionaries, as long as the dictionaries are in the specified 
    path/private. if you are doing this and setting one_salt to True, 
    salt_length argument will be ignored.
    """
    def __init__(self, corpus, corpus_path, hash_function='sha256', 
                 salt_length=32, one_salt=False, encoding='utf-8', 
                 indent_json=None):
        """
        takes as corpus a dictionary of nested lists of a variable depth, and 
        hashes its tokens with a random salt. the corpus_path provided is 
        created if not existent. the dictionary and hashed corpus paths are 
        built from the provided corpus_path
        :param corpus: list: nested list, whose elements are themselves nested 
        lists of tokens to be encoded (hashed).
        :param corpus_path: str: defines where outputted files are to be stored.
        :param hash_function: str: defines which hash function to use in the 
        encoding process (the ones available are from the hashlib).
        :param salt_length: int: determines salt length in bytes.
        :param one_salt: bool: determines if tokens will be hashed 
        with the same salt or one for each token. if True, os.urandom generates 
        a salt to be used. if False, os.urandom will generate a salt for each 
        token.
        :param encoding: str: defines in which encoding the outputted files are 
        to be stored in.
        :param indent_json: int: if None, won't indent. if positive integer, 
        will indent using this number of spaces. zero will add \\n, but no 
        indentation. if you don't have nested lists, the default argument (None)
        is probably the best option, for with large corpora indentation and \\n 
        can take up a lot of space.
        """
        self.corpus = corpus
        if not os.path.isdir(corpus_path):
            os.mkdir(corpus_path)
        self.corpus_path = corpus_path
        self.public_path = self._make_public_dir()
        self.encoding = encoding
        self.encode_dictionary_path = os.path.join(self.corpus_path, 
                                                'private/encode_dictionary.json')
        self.decode_dictionary_path = os.path.join(self.corpus_path, 
                                                'private/decode_dictionary.json')
        (self.encode_dictionary, 
                             self.decode_dictionary) = self._load_dictionaries()
        self.encoding = encoding
        if hash_function not in hashlib.algorithms_available:
            raise Exception('hash function {} not available on this computer. '
        'choose another from hashlib.algorithms_available.'.format(hash_function))
        else:
            self.hash_function = hash_function
        self.salt_length = salt_length
        self.one_salt = self.choose_salt(one_salt)
        self.indent_json = indent_json
        self.corpus_size = self.hash_corpus()

    def _make_public_dir(self):
        """
        creates folder in /public where output files will be stored. for each 
        instance of CorpusHash using the same corpus_path, a folder will be 
        created using the current time as its name.
        :return: str: public_hash_path, the folder created
        """
        public_dir_path = os.path.join(self.corpus_path, 'public')
        if not os.path.isdir(public_dir_path):
            os.mkdir(public_dir_path)
        current_time = datetime.datetime.now()
        public_hash_path = os.path.join(self.corpus_path, 'public', 
                                     current_time.strftime('%Y-%m-%d_%H-%M-%S-%f'))
        os.mkdir(public_hash_path)
        return public_hash_path

    def _load_dictionaries(self):
        """
        checks if there already exists encode and decode dictionaries from a 
        previous hashing. if so, loads them. (this is useful if you'll add a 
        document to the corpus, but do not want to hash it all over again). if 
        there are no dictionaries, creates the folders where they'll be saved 
        to after the corpus is hashed, and returns their skeletons (empty 
        dictionaries).
        :return: dict, dict: encode_dictionary, decode_dictionary
        """
        if (os.path.isfile(self.encode_dictionary_path) and 
            os.path.isfile(self.decode_dictionary_path)):
            logger.info('dictionaries from previous hashing found. '
                         'loading them.')
            with open(self.encode_dictionary_path, 'rt') as f:
                encode_dictionary = json.load(f, encoding=self.encoding)
            with open(self.decode_dictionary_path, 'rt') as f:
                decode_dictionary = json.load(f, encoding=self.encoding)
        else:
            encode_dictionary, decode_dictionary = {}, {}
            try:
                os.mkdir(os.path.join(self.corpus_path, 'private'))
            except FileExistsError:
                pass
        return encode_dictionary, decode_dictionary

    def choose_salt(self, one_salt):
        """
        if one_salt is True, searches for the one salt from a previous hashing. 
        else creates a unique salt using os.urandom.
        :param one_salt: bool: choice of unique salt or not
        :return: bytes or None: the unique salt or None if all salts are to be 
        different
        """
        if isinstance(one_salt, bool) and one_salt:
            if any(self.encode_dictionary):
                # get any value, because it must be the one salt.
                return base64.b85decode(next(iter(self.decode_dictionary.values()))[1].encode())
            else:
                return os.urandom(self.salt_length)
        elif isinstance(one_salt, bool) and not one_salt:
            return None
        else:
            raise TypeError('input must be boolean.')

    def hash_corpus(self):
        """
        for each document in the corpus, hashes it according to class arguments, 
        saving its hashed form as a .json in /public, and saving the encode and 
        decode dictionaries to /private.
        :return: True(1) if successful
        """
        for ix, document in enumerate(self.corpus):
            output_document = copy.deepcopy(document)  # copying here because the next method is recursive
            encoded_document = self._hash_document(document, output_document)
            encoded_document_path = os.path.join(self.public_path, 
                                                 '{}.json'.format(ix))
            self._export_work(encoded_document, encoded_document_path)
        corpus_size = ix + 1
        self._export_work(self.encode_dictionary, self.encode_dictionary_path)
        self._export_work(self.decode_dictionary, self.decode_dictionary_path)
        logger.info('{} documents hashed and saved to {}.'.format(corpus_size, 
                                                os.path.join(self.public_path)))
        return corpus_size

    def _hash_document(self, input_document, output_document):
        """
        iterates over input_document, hashes its elements, and substitutes them 
        into output_document (its former copy).
        :param input_document: list: nested list of tokens (nested list of str).
        :param output_document: list: nested list of tokens (nested list of 
        str), a deep copy of input document.
        :return: list: nested list of hashed tokens
        """
        for ix, item in enumerate(input_document):
            if isinstance(item, str):
                output_document[ix] = self._encode_token(item)
            else:
                output_document[ix] = self._hash_document(item, 
                                                            output_document[ix])
        return output_document

    def _encode_token(self, token):
        """
        takes a token as input, if token is in encoding dictionary, looks its 
        hash up and returns it. else, hashes it, checks it for collisions 
        (overkill) while updating en(de)coding dictionaries.
        :param token: str: token.
        :return: str: hashed token
        """
        if token in self.encode_dictionary:
            return self.encode_dictionary[token]
        else:
            hashed_token, salt = hash_token(token, 
                                            hash_function=self.hash_function, 
                                            salt_length=self.salt_length,
                                            salt=self.one_salt)
            while hashed_token in self.decode_dictionary:
                hashed_token, salt = hash_token(token, 
                                               hash_function=self.hash_function,
                                               salt_length=self.salt_length,
                                               salt=None)
            self.decode_dictionary[hashed_token] = (token, 
                                                    base64.b85encode(salt).decode())
            self.encode_dictionary[token] = hashed_token
        return hashed_token

    def _export_work(self, var_to_dump, file_path):
        """
        takes a file to be written (Python object) and a file path, and dumps 
        the file to the file path (which includes name and extension).
        :param var_to_dump: dictionary or nested list of str.
        :param file_path: file path where var_to_dump is to be written. must 
        contain filename and extension.
        :return: None; but files (dictionaries and documents) are created.
        """
        with open(file_path, mode='wt', encoding=self.encoding) as output:
            json.dump(var_to_dump, output, indent=self.indent_json, 
                      ensure_ascii=False)

    def read_hashed_corpus(self):
        """
        reads hashed corpus one document at a time, in order. it uses the fact 
        that files are numbered from 0 to n to sort files.
        :yield: str, list: document name, hashed document as a nested list
        """
        for ix in range(self.corpus_size):
            with open(os.path.join(self.public_path, '{}.json'.format(ix)), 
                      mode='rt', encoding=self.encoding) as hashed_document:
                hashed_document_list = json.load(fp=hashed_document, 
                                                 encoding=self.encoding)
            yield hashed_document_list


def hash_token(token, hash_function='sha256', salt_length=32, salt=None):
    """
    takes a token and hashes it along with a random salt of given length, 
    according to the specified hash function.
    :param token: str: string of any length
    :param hash_function: str: hash function to use (check hashlib library).
    :param salt_length: int: salt length in bytes.
    :param salt: bytes: only used for tests, specifies which salt to use.
    :return: str, bytes: hashed token (base85-decoded) and the random salt used.
    """
    if salt is None:
        salt = os.urandom(salt_length)
    token_hasher = hashlib.new(hash_function)
    token_hasher.update(token.encode() + salt)
    token_digest = token_hasher.digest()
    token_base85 = base64.b85encode(token_digest)
    hashed_token = token_base85.decode()
    return hashed_token, salt


def walk_nested_list(input_document):
    """
    takes a nested list of strings and yields its elements in order.
    :param input_document: list: a nested list of strings
    :yield: str: the next string
    """
    for item in input_document:
        if isinstance(item, str):
            yield item
        else:
            for subitem in walk_nested_list(item):
                yield subitem


def text_split(text, stripchars=' .()[]{:},"\';'):
    """
    splits a text into a nested list along the strip characters provided. this 
    function is meant for tests. if you need a tokenizer, you should probably 
    use a less naive one.
    :param text: str: text to be split.
    :param stripchars: str: characters to be used as splitting points.
    :return: str: text splitted at specified stripchars
    """
    split_text = []
    for line in text.splitlines():
        sentences = []
        for sentence in line.split('.'):
            words = []
            for word in sentence.split():
                stripped_word = word.strip(stripchars)
                if stripped_word:  # make sure we are adding something
                    words.append(stripped_word)
            if words:
                sentences.append(words)
        if sentences:
            split_text.append(sentences)
    return split_text
