#!/usr/bin/env python3
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='corpushash',
      version='0.1.0',
      description='Cryptographic hasher of text document corpora',
      long_description=long_description,
      author='Bruno Cuconato',
      author_email='bcclaro+corpushash@gmail.com',
      url='https://github.com/NAMD/corpushash',
      packages=find_packages(exclude=['tests', 'test_corpus']),
      # install_requires=[''],
      keywords = ['python 3', 'nlp', 'hash', 'hashing'], 
      classifiers=[
          'Development Status :: 3 - Alpha',
          # Indicate who your project is intended for
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Build Tools',
          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
      ],
      )
