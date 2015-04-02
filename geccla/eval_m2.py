#!/usr/bin/python


import argparse

from evaluation.maxmatch import evaluate_m2


def main():
    args = parse_user_arguments()
    prec, rec, fscore = evaluate_m2(args.text_file, args.m2_file, 
                                    args.orig_file, args.temp_file)

    print "{0:.4f}\t{1:.4f}\t{2:.4f}".format(prec, rec, fscore)
    

def parse_user_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('text_file', help="input text file")
    parser.add_argument('m2_file', help="evaluation file in M2 format")

    parser.add_argument('-o', '--orig-file', type=str,
        help="file with original tokenization and letter casing")
    parser.add_argument('-t', '--temp-file', type=str,
        help="name for temporary files")

    return parser.parse_args()


if __name__ == '__main__':
    main()
