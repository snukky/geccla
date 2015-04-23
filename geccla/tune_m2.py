#!/usr/bin/python

import argparse

from classification import FORMATS

from evaluation.maxmatch import run_m2_grid_search


def main():
    args = parse_user_arguments()

    result = run_m2_grid_search(
                 args.confusion_set, args.format, 
                 args.input_file, args.cnfs_file, args.pred_file, 
                 args.m2_file,
                 args.grid_file, args.work_dir,
                 (args.thr_steps, args.dif_steps),
                 args.no_deep)
    print "\t".join(map(str, result))


def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Estimates -t and -d" \
        " parameters for evaluation script using grid search.")

    parser.add_argument('input_file', help="input text file")
    parser.add_argument('cnfs_file', help=".cnfs file")
    parser.add_argument('pred_file', help=".pred file")

    req = parser.add_argument_group("required arguments")
    req.add_argument('-c', '--confusion-set', required=True,
        help="confusion set as comma-separated list of words")
    req.add_argument('-f', '--format', required=True, choices=FORMATS, 
        help="prediction data format")

    conll = parser.add_argument_group("M2 arguments")
    conll.add_argument('-m2', '--m2-file', type=str,
        help="gold standard file in M2 format")
    #conll.add_argument('-o', '--orig-file', type=str,
        #help="source side of M^2 file with original tokenization and casing")

    eval = parser.add_argument_group("evaluation arguments")
    eval.add_argument('--thr-steps', type=int, default=20,
        help="number of steps for threshold")
    eval.add_argument('--dif-steps', type=int, default=1,
        help="number of steps for difference")
    eval.add_argument('--no-deep', action='store_false',
        help="do not run grid search twice")

    parser.add_argument('-g', '--grid-file', type=str,
        help="file to store grid search table")
    parser.add_argument('-w', '--work-dir', type=str,
        help="working dir")

    return parser.parse_args()

if __name__ == '__main__':
    main()
