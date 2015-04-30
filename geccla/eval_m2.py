#!/usr/bin/python


import argparse

from evaluation.maxmatch import evaluate_m2


def main():
    args = parse_user_arguments()

    print "### M^2 evaluation of {}".format(args.text_file)
    print ""

    for m2_file in args.m2_files:
        print "# according to {}".format(m2_file)

        prec, rec, fscore = evaluate_m2(args.text_file, m2_file)
        print "Precision   : %.4f" % prec
        print "Recall      : %.4f" % rec
        print "F0.5        : %.4f" % fscore
        print ""
    

def parse_user_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('text_file', help="input text file")
    parser.add_argument('m2_files', nargs='+', 
        help="evaluation file(s) in M2 format")

    #parser.add_argument('-o', '--orig-file', type=str,
        #help="source side of M^2 file with original tokenization and casing")
    #parser.add_argument('-t', '--temp-file', type=str,
        #help="name for temporary files")

    return parser.parse_args()


if __name__ == '__main__':
    main()
