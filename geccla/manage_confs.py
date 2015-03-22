#!/usr/bin/python

import argparse
import math
import random

from confusions.confusion_matrix import ConfusionMatrix
from confusions.manipulate import impose_error_rate

def main():
    args = parse_user_arguments()

    matrix = confusion_matrix(args.confusion_set, args.cnfs_file)
    if args.error_rate:
        impose_error_rate(args.cnfs_file, args.error_rate / 100.0, matrix)
    else:
        matrix.print_stats()


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Manages .cnfs files.")

    parser.add_argument('cnfs_file', help=".cnfs file")

    parser.add_argument('-c', '--confusion-set',
        help="confusion set as comma-separated list of words")
    parser.add_argument('-e', '--error-rate', type=float,
        help="sampling to desired error rate by removin correct examples")

    return parser.parse_args()


if __name__ == '__main__':
    main()
