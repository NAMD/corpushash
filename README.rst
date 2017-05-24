##########
corpushash
##########

The ``corpushash`` library enables the performance of common NLP tasks on
sensitive documents without disclosing their contents. This is done by
hashing every token in the corpus along with a salt.

protocol
========

1. the client --- in her own secure environment --- takes her classified 
documents and does the linguistic pre-processing (removal of stopwords, 
tokenization, etc.)

2. the client then hashes the tokens: she creates random salts for every 
different token and hashes the concatenation of token+salt. the client keeps a 
dictionary of the salts used for every token.

3. the client sends the hashed tokens to the analyst for linguistic processing. 
as there is a biunivocal correspondence between every hashed token and 
plaintext token, NLP can occur in the same way as with any plaintext corpus.

4. once the NLP is over, the analyst sends the results to the client, who then 
uses the dictionary to recover the plaintext tokens and thus the results' 
meaning.


the library
===========

The library requires as input:

- a tokenized ``corpus`` as a nested list, whose elements are themselves
  nested lists of the tokens of each document in the corpus.

  each list corresponds to a document structure: its chapters,
  paragraphs, sentences. you decide how the nested list is to be
  created or structured, as long as the input is a nested list with
  strings as their bottom-most elements..

- ``corpus_path``, a path to a directory where the output files are to
  be stored.

The output includes:

- a ``.json`` file for every document in the ``corpus``, named sequentially as 
  positive integers, e.g., the first document being ``0.json``, stored in 
  ``corpus_path/public/$(timestamp-of-hash)/``.

- two ``.json`` dictionaries stored in ``corpus_path/private``. they are
  used to decode the ``.json`` files or the NLP results.

install
=======

the package demands python ⩾3, but has no external dependencies.

using pip:

.. code-block:: shell

    pip3 install corpushash

or from repository (most up-to-date):

.. code-block:: bash

    pip3 install git+https://github.com/NAMD/corpushash.git

or manually:

.. code-block:: shell

    git clone https://github.com/NAMD/corpushash.git
    cd corpushash
    python3 setup.py install

usage
=====

this will hash each word in the first four verses of the `zen of python 
<https://www.python.org/dev/peps/pep-0020/>`_ to the same .json document:

.. code-block:: python

    import corpushash as ch
    example_corpus = [[
                     ['Beautiful', 'is', 'better', 'than', 'ugly'],
                     ['Explicit', 'is', 'better', 'than', 'implicit'],
                     ['Simple', 'is', 'better', 'than', 'complex'],
                     ['Complex', 'is', 'better', 'than', 'complicated'],
                     ['Flat', 'is', 'better', 'than', 'nested']
                     ]]
    hashed_corpus = ch.CorpusHash(example_corpus, 'output_directory')

this will hash each word in the first four verses of the zen of python to **four** 
different .json documents, as if they were different documents:

.. code-block:: python

    import corpushash as ch
    example_corpus = [
                     ['Beautiful', 'is', 'better', 'than', 'ugly'],
                     ['Explicit', 'is', 'better', 'than', 'implicit'],
                     ['Simple', 'is', 'better', 'than', 'complex'],
                     ['Complex', 'is', 'better', 'than', 'complicated'],
                     ['Flat', 'is', 'better', 'than', 'nested']
                     ]
    hashed_corpus = ch.CorpusHash(example_corpus, 'output_directory')

so be careful when constructing your nested lists! check the tutorial at 
``notebooks/tutorial.ipynb``.

notes
=====

- probability of collision is extremely low (check the `preprint <TBD>`_), but 
  still we check for them, so they are not an issue.

- hashing the tokens is not the same as encrypting them. as the same token 
  always maps to the same hash, the resulting hashed corpus is subject to 
  frequency analysis. even if a pre-processed text is almost uncomprehensible to 
  a reader (specially if stopwords are removed), there probably is still a 
  degree of trust in the analyst. she is usually someone who has no incentive 
  to attempt a decipherment of the text or someone who has a lesser (but by no 
  means inexisting) security clearance. this vulnerability will be investigated 
  in the future.

- memory complexity is estimated to be at most double the size of the biggest 
  document in the corpus.

credits
=======

@odanoburu & @fccoelho

license
=======

LGPL 3, check the ``LICENSE.md`` file for full content.
