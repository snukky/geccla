#!/usr/bin/python

import argparse

from classification import FORMATS
from evaluation.grid_search import run_grid_search


def main():
    args = parse_user_arguments()

    result = run_grid_search(
                 args.confusion_set, args.format,
                 args.cnfs_file, args.pred_file, args.grid_file,
                 (args.thr_steps, args.dif_steps))

    print "\t".join(map(str, result))


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Estimates -t and -d" \
        " parameters for evaluation script using grid search.")

    parser.add_argument('cnfs_file', help=".cnfs file")
    parser.add_argument('pred_file', help=".pred file")

    req = parser.add_argument_group("required arguments")
    req.add_argument('-c', '--confusion-set', required=True,
        help="confusion set as comma-separated list of words")
    req.add_argument('-f', '--format', required=True, choices=FORMATS, 
        help="prediction data format")

    eval = parser.add_argument_group("evaluation arguments")
    eval.add_argument('--thr-steps', type=int, default=20,
        help="number of steps for threshold")
    eval.add_argument('--dif-steps', type=int, default=1,
        help="number of steps for difference")

    parser.add_argument('-g', '--grid-file', type=str,
        help="file to store grid search table")

    return parser.parse_args()

if __name__ == '__main__':
    main()
