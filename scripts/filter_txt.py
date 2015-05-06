#!/usr/bin/python

import sys
import argparse
from difflib import SequenceMatcher

DEBUG = False


def main():
    global DEBUG

    args = parse_user_arguments()
    DEBUG = args.debug
    conf_set = args.confusion_set.strip().split(',')

    with open(args.file) as data:
        for line in data:
            err_sent, cor_sent = line.strip().split("\t")
            new_sent = filter_edits(err_sent, cor_sent, conf_set, 
                                    args.greedy, not args.no_spaces)
            print new_sent

        
def filter_edits(err_sent, cor_sent, conf_set, greedy=False, allow_spaces=True):
    err_toks = err_sent.split()
    cor_toks = cor_sent.split()

    matcher = SequenceMatcher(None, err_toks, cor_toks)
    new_toks = []
 
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        err_tok = ' '.join(err_toks[i1:i2])
        cor_tok = ' '.join(cor_toks[j1:j2])
        
        if tag == 'replace':
            if greedy and (err_tok.lower() in conf_set or cor_tok.lower() in conf_set):
                new_toks.append(cor_tok)
            elif err_tok.lower() in conf_set and cor_tok.lower() in conf_set:
                new_toks.append(cor_tok)
            else:
                new_toks.append(err_tok)
        elif tag == 'insert':
            if cor_tok.lower() in conf_set:
                new_toks.append(cor_tok)
        elif tag == 'delete':
            if err_tok.lower() not in conf_set:
                new_toks.append(err_tok)
        else:
            new_toks.append(err_tok)

    return ' '.join(new_toks)

def debug(msg):
    if DEBUG:
        print >> sys.stderr, msg

def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Extracts errors covered by"
        " specified confusion set. Input is parallel data.")

    parser.add_argument('file', help="parallel file with input and system"
        " sentences")
    parser.add_argument('-c', '--confusion-set', type=str, 
        help="confusion set as comma-separated list of words")
    parser.add_argument('-g', '--greedy', action='store_true',
        help="one word from confusion set in edit pair is sufficient")
    parser.add_argument('-s', '--no-spaces', action='store_true',
        help="do not allow spaces in confusion words (require --greedy)")
    parser.add_argument('--debug', action='store_true', 
        help="show debug")

    return parser.parse_args()

if __name__ == '__main__':
    main()
