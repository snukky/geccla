#!/usr/bin/python

import os
import sys
import argparse

from logger import log

from confusions.artordet_finder import ArtOrDetFinder
from confusions.null_finder import NullFinder
from confusions.basic_finder import BasicFinder

from confusions import format_conf


def main():
    args = parse_user_arguments()
    
    if args.artordet:
        finder = ArtOrDetFinder(args.confusion_set)
        confs = finder.find_confusion_artordets(args.input_file, args.levels)
    elif args.ngrams_prefix:
        finder = NullFinder(args.confusion_set, awc_dict=args.awc_dict)
        confs = finder.find_confusion_nulls(args.input_file, 
                                            args.ngrams_prefix,
                                            args.levels,
                                            args.min_count)
    else:
        finder = BasicFinder(args.confusion_set, args.left_confusion_set)
        confs = finder.find_confusion_words(args.input_file,
                                            args.all_spaces_as_nulls)

    for conf in confs:
        print format_conf(conf)


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Finds examples of " \
        "words from confusion set.")
    
    parser.add_argument('input_file', type=str, help="input corpus")

    parser.add_argument('-c', '--confusion-set', type=str, 
        help="confusion set as comma-separated list of words")
    parser.add_argument('-b', '--left-confusion-set', type=str,
        help="confusion set for first word in edit pair (by default " \
            "identical with -c)")
    parser.add_argument('-n', '--ngrams-prefix', type=str,
        help="prefix for files with list of n-grams")
    parser.add_argument('-l', '--levels', type=str,
        help="levels of n-grams extraction as comma-separated list "
             "(or numerical value when --artordet is active)")
    parser.add_argument('--min-count', type=int, default=5,
        help="required minimum frequency of ngrams")

    parser.add_argument('--artordet', action='store_true',
        help="enable enhanced finding rules for articles and determiners")
    parser.add_argument('--lazy', action='store_true',
        help="do not add <null> examples if not in confusion set")
    parser.add_argument('--all-spaces-as-nulls', action='store_true',
        help="extract all spaces as <null> examples")
    parser.add_argument('--awc-dict', type=str,
        help="path to file with automatic word clusters")
    
    args = parser.parse_args()

    if not args.confusion_set and not args.artordet:
        raise ArgumentError("argument --confusion-set or --artordet is required")
    if not args.confusion_set and args.ngrams_prefix:
        raise ArgumentError("argument --ngrams-prefix requires --confusion-set")

    if not args.artordet and args.levels:
        args.levels = list(set(args.levels.split(',')))
        if not all(lvl in NullFinder.LEVELS for lvl in args.levels):
            raise ArgumentError("allowed values for --levels argument are {}" \
                .format(', '.join(NullFinder.LEVELS)))

    if args.artordet:
        if not args.confusion_set:
            args.confusion_set = 'a,the,'
        if not args.levels:
            args.levels = 2
        args.levels = int(args.levels)

    elif not args.levels:
        args.levels = 'tok pos awc'.split()

    return args


if __name__ == '__main__':
    main()
