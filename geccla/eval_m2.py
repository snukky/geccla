#!/usr/bin/python


import argparse

from evaluation.maxmatch import evaluate_m2


def main():
    args = parse_user_arguments()
    prec, rec, fscore = evaluate_m2(args.text_file, args.m2_file)

    print "### M^2 evaluation of {} by {}".format(args.text_file, args.m2_file)
    print ""
    print "Precision   : %.4f" % prec
    print "Recall      : %.4f" % rec
    print "F0.5        : %.4f" % fscore
    print ""
    

def parse_user_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('text_file', help="input text file")
    parser.add_argument('m2_file', help="evaluation file in M2 format")

    #parser.add_argument('-o', '--orig-file', type=str,
        #help="source side of M^2 file with original tokenization and casing")
    #parser.add_argument('-t', '--temp-file', type=str,
        #help="name for temporary files")

    return parser.parse_args()


if __name__ == '__main__':
    main()
