#!/usr/bin/python

import argparse
import math
import random

from confusions.confusion_matrix import ConfusionMatrix
from confusions.manipulate import impose_error_rate


def main():
    args = parse_user_arguments()

    matrix = ConfusionMatrix(args.cnfs_file, args.confusion_set)
    if args.error_rate:
        impose_error_rate(args.cnfs_file, args.error_rate, matrix, 
            args.in_place, args.shuffle)
    else:
        matrix.print_stats()


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Manages .cnfs files.")

    parser.add_argument('cnfs_file', help=".cnfs file")

    parser.add_argument('-c', '--confusion-set', type=str,
        help="confusion set as comma-separated list of words")
    parser.add_argument('-e', '--error-rate', type=float,
        help="sampling to desired error rate by removing correct examples")
    parser.add_argument('--in-place', action='store_true')
    parser.add_argument('--shuffle', action='store_true')

    return parser.parse_args()


if __name__ == '__main__':
    main()
