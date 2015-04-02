#!/usr/bin/python

import argparse

from confusions.null_finder import NullFinder


def main():
    args = parse_user_arguments()
    finder = NullFinder(args.confusion_set, not args.no_clean)

    finder.train_ngrams(args.input_file, args.ngrams_prefix, 
                        args.left_context, args.right_context, 
                        args.min_count, 
                        args.levels)


def parse_user_arguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('input_file', type=str, help="input corpus")

    main = parser.add_argument_group("required arguments")
    main.add_argument('-c', '--confusion-set', type=str, required=True, 
        help="confusion set as comma-separated list of words")
    main.add_argument('-n', '--ngrams-prefix', type=str, required=True,
        help="prefix for files with list of n-grams")
    main.add_argument('-l', '--levels', type=str, default='tok,awc',
        help="levels of n-grams extraction as comma-separated list")

    train = parser.add_argument_group("training arguments")
    train.add_argument('--min-count', type=int, default=5,
        help="minimum frequency of n-grams to be important")
    train.add_argument('--left-context', type=int, default=1, 
        help="size of left context")
    train.add_argument('--right-context', type=int, default=3, 
        help="size of right context")
    train.add_argument('--no-clean', action='store_true', 
        help="do not remove temporary files")

    args = parser.parse_args()

    args.levels = list(set(args.levels.split(',')))

    if not all(lvl in NullFinder.LEVELS for lvl in args.levels):
        raise ArgumentError("allowed values for --levels argument are {}" \
            .format(', '.join(NullFinder.LEVELS)))

    return args

if __name__ == '__main__':
    main()
