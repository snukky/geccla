#!/usr/bin/python

import argparse

from classification import FORMATS
from evaluation import print_complete_evaluation


def main():
    args = parse_user_arguments()
    print_complete_evaluation(args.confusion_set, args.format,
                              args.cnfs_file, args.pred_file, 
                              args.threshold, args.difference)

  
def parse_user_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('cnfs_file', help=".cnfs file")
    parser.add_argument('pred_file', help="classifier predictions")

    req = parser.add_argument_group("required arguments")
    req.add_argument('-c', '--confusion-set', required=True,
        help="confusion set as comma-separated list of words")
    req.add_argument('-f', '--format', required=True, choices=FORMATS,
        help="prediction data format")

    eval = parser.add_argument_group("evaluation arguments")
    eval.add_argument('-t', '--threshold', type=float,
        help="minimum classifier confidence")
    eval.add_argument('-d', '--difference', type=float,
        help="minimum difference between best and second classifier label "
        "confidences") 

    return parser.parse_args()


if __name__ == '__main__':
    main()
