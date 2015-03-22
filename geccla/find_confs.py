#!/usr/bin/python

import argparse
import os
import sys

from logger import log

from confusions.artordet_finder import ArtOrDetFinder
from confusions.null_finder import NullFinder
from confusions.basic_finder import BasicFinder

from confusions import format_conf


def main():
    args = parse_user_arguments()
    
    if args.artordet:
        finder = ArtOrDetFinder()
        confs = finder.find_confusion_artordets(args.input_file)
    elif args.ngrams_prefix:
        finder = NullFinder(args.confusion_set)
        confs = finder.find_confusion_nulls(args.input_file, 
                                            args.ngrams_prefix,
                                            'tok awc'.split())
    else:
        finder = BasicFinder(args.confusion_set)
        confs = finder.find_confusion_words(args.input_file)

    for conf in confs:
        print format_conf(conf)


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Finds examples of " \
        "words from confusion set.")
    
    parser.add_argument('input_file', type=str, help="input corpus")

    parser.add_argument('-c', '--confusion-set', type=str, 
        help="confusion set as comma-separated list of words")
    parser.add_argument('-n', '--ngrams-prefix', type=str,
        help="prefix for files with list of n-grams")
    parser.add_argument('--artordet', action='store_true',
        help="enable enhanced finding rules for articles and determiners")
    
    args = parser.parse_args()

    if not args.confusion_set and not args.artordet:
        raise ArgumentError("argument --confusion-set or --artordet is required")
    if not args.confusion_set and args.ngrams_prefix:
        raise ArgumentError("argument --ngrams-prefix requires --confusion-set")

    if args.artordet:
        args.confusion_set = 'a,the,'
    return args


if __name__ == '__main__':
    main()
