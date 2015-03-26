#!/usr/bin/python

import os
import sys
import shutil
import argparse

import cmd
from preprocess.letter_case import restore_file_case

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from m2scorer_fork import m2scorer


def main():
    args = parse_user_arguments()

    input_file = args.text_file
    temp_file = None

    if args.orig_file:
        #temp_file = input_file + '.nltk'
        #with open(temp_file, 'w+') as file:
            #for line in restore_file_tok(input_file, args.orig_file):
                #file.write(line + "\n")
        #input_file = temp_file

        temp_file = input_file + '.cased'
        with open(temp_file, 'w+') as file:
            for line in restore_file_case(input_file, args.orig_file):
                file.write(line + "\n")
        input_file = temp_file

        if args.temp_file:
            shutil.copy2(temp_file, args.temp_file)
            input_file = args.temp_file

    num_of_lines = cmd.wc(input_file)
    num_of_sents = int(cmd.run("grep -c '^S ' {}".format(args.m2_file)).strip())

    if num_of_lines != num_of_sents:
        log.error("Input file and M2 file differ in number of sentences: "
            "{} != {}".format(num_of_lines, num_of_sents))

    prec, rec, fscore = m2scorer(input_file, args.m2_file, 
                                 beta=0.5, max_unchanged_words=3)

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
