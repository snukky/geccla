#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from preprocess.letter_case import restore_file_case


def main():
    args = parse_user_arguments()
    for line in restore_case(args.text_file, args.orig_file):
        print line


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Restores text letter case.")

    parser.add_argument("text_file", type=str, 
        help="modified text file with wrong letter case")
    parser.add_argument("orig_file", type=str, 
        help="original text file with desired letter case")

    return parser.parse_args()


if __name__ == "__main__":
    main()
