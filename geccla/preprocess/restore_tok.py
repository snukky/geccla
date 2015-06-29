#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../geccla')))

from preprocess.tokenization import restore_file_tok
from preprocess.tokenization import TOK_CONVERTERS


def main():
    args = parse_user_arguments()
    for line in restore_file_tok(args.text_file, args.orig_file,
                                 args.quotes, args.convert):
        print line


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Restores text tokenization.")

    parser.add_argument("text_file", type=str, 
        help="text file with wrong tokenization")
    parser.add_argument("orig_file", type=str, 
        help="original text file with desired tokenization")

    parser.add_argument("-q", "--quotes", action='store_true', 
        help="keep quotes as in original tokenization")
    parser.add_argument("-c", "--convert", choices=TOK_CONVERTERS.keys(), 
        help="retokenize with external detokenizers/tokenizers")

    return parser.parse_args()


if __name__ == "__main__":
    main()
