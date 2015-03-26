#!/usr/bin/python

import os
import sys
import argparse

from classification import FORMATS
from prediction.output_formatter import OutputFormatter


def main():
    args = parse_user_arguments()

    frm = OutputFormatter(args.confusion_set)
    for line in frm.text_output(args.text_file, args.cnfs_file, args.pred_file, 
                                args.format,
                                args.threshold, args.difference):
        print line


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Injects classifier" \
        " predictions into original text file.")

    parser.add_argument('text_file', help="input text file")
    parser.add_argument('cnfs_file', help=".cnfs file")
    parser.add_argument('pred_file', help="classifier predictions")


    req = parser.add_argument_group("required arguments")
    req.add_argument('-c', '--confusion-set', required=True, type=str, 
        help="confusion set as comma-separated list of words")
    req.add_argument('-f', '--format', required=True, choices=FORMATS,
        help="classifier algorithm")

    eval = parser.add_argument_group("evaluation arguments")
    eval.add_argument('-t', '--threshold', type=float,
        help="minimum classifier confidence")
    eval.add_argument('-d', '--difference', type=float,
        help="minimum confidence difference between best and second"
        " classifier prediction") 

    return parser.parse_args()


if __name__ == '__main__':
    main()
