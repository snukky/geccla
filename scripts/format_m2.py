#!/usr/bin/python

import sys
import argparse
from difflib import SequenceMatcher

DEBUG = False
CONFUSED_WORDS = set()


def main():
    global DEBUG

    args = parse_user_arguments()
    DEBUG = args.debug
    conf_set = args.confusion_set.strip().lower().split(',')

    ann_files = [open(file) for file in args.annot]
    err_type = args.error_type or args.confusion_set.replace(',','')

    with open(args.input) as input_file:
        for line in input_file:
            err_sent = line.strip()
            debug(err_sent)
            annots = []

            for ann_file in ann_files:
                cor_sent = ann_file.next().strip()
                anns = filter_annotations(err_sent, cor_sent, conf_set, 
                                          args.greedy, not args.no_spaces)
                annots.append(anns)

            debug(annots)
            print format_m2_line(err_sent, annots, err_type, 
                                 args.noops, args.merge)

    for file in ann_files:
        file.close()

    print >> sys.stderr, "all confused words: {}".format(';'.join(CONFUSED_WORDS))
    clean_cwords = filter(lambda cw: ' ' not in cw, CONFUSED_WORDS)
    print >> sys.stderr, "clean confused words: {}".format(';'.join(clean_cwords))

def format_m2_line(err_sent, annots, category, noops=False, merge=False):
    str = "S {}\n".format(err_sent)

    if noops:
        with_noops = [idx for idx, anns in enumerate(annots) if len(anns) == 0]
        if len(with_noops) == len(annots):
            with_noops = []

    for idx, anns in enumerate(annots):
        if noops and idx in with_noops:
            str += "A -1 -1|||noop|||-NONE-|||-NONE-|||-NONE-|||{ann}\n" \
                .format(ann=idx)
        for i, j, cor in anns:
            skip = False

            if merge:
                for prev_idx in range(idx):
                    for i2, j2, cor2 in annots[prev_idx]:
                        if i == i2 and j == j2 and cor == cor2:
                            skip = True

            if not skip:
                str += "A {i} {j}|||{cat}|||{cor}|||REQUIRED|||-NONE-|||{ann}\n" \
                    .format(i=i, j=j, cat=category, cor=cor, ann=idx)
    return str
        
def filter_annotations(err_sent, cor_sent, 
                       conf_set, 
                       greedy=False, allow_spaces=True):
    global CONFUSED_WORDS

    err_toks = err_sent.split()
    cor_toks = cor_sent.split()

    matcher = SequenceMatcher(None, err_toks, cor_toks)
    annots = []
 
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        err_txt = ' '.join(err_toks[i1:i2])
        cor_txt = ' '.join(cor_toks[j1:j2])

        err_txt_lc = err_txt.lower()
        cor_txt_lc = cor_txt.lower()
        
        if tag == 'replace':
            if greedy and (err_txt_lc in conf_set or cor_txt_lc in conf_set):
                annots.append( (i1, i2, cor_txt) )
                CONFUSED_WORDS.add(err_txt_lc)
                CONFUSED_WORDS.add(cor_txt_lc)

            elif err_txt_lc in conf_set and cor_txt_lc in conf_set:
                annots.append( (i1, i2, cor_txt) )
                CONFUSED_WORDS.add(err_txt_lc)
                CONFUSED_WORDS.add(cor_txt_lc)

        elif tag == 'insert':
            if cor_txt_lc in conf_set:
                annots.append( (i1, i2, cor_txt) )
                CONFUSED_WORDS.add(cor_txt_lc)

        elif tag == 'delete':
            if err_txt_lc in conf_set:
                annots.append( (i1, i2, '') )
                CONFUSED_WORDS.add(err_txt_lc)

    return annots

def debug(msg):
    if DEBUG:
        print >> sys.stderr, msg

def parse_user_arguments():
    parser = argparse.ArgumentParser(description="Creates M2 file from"
      " parallel files with annotations filtered by confusion set")

    parser.add_argument('input', help="file with error sentences")
    parser.add_argument('annot', nargs='+', help="files with corrected sentences")

    parser.add_argument('-c', '--confusion-set', type=str, 
        help="confusion set as a comma-separated list of words")
    parser.add_argument('-t', '--error-type', type=str,
        help="error type name for extracted errors")
    parser.add_argument('-n', '--noops', type=str,
        help="add noop annotations")
    parser.add_argument('-m', '--merge', type=str,
        help="merge identical annotations from different annotators")
    parser.add_argument('-g', '--greedy', action='store_true',
        help="one word from confusion set in edit pair is sufficient")
    parser.add_argument('-s', '--no-spaces', action='store_true',
        help="do not allow spaces in confusion words (require --greedy)")
    parser.add_argument('--debug', action='store_true', 
        help="show debug")

    return parser.parse_args()

if __name__ == '__main__':
    main()
