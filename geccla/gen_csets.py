#!/usr/bin/python

import os
import sys
import argparse

from csets.edit_stats import EditStats
from csets.cset_generator import CSetGenerator


from logger import log


def main():
    args = parse_user_args()
    
    stats = EditStats(args.corpus, min_err=args.min_err, 
                                   min_cor=args.min_cor,
                                   no_spaces=args.no_spaces,
                                   no_nulls=True)
    #stats.expand_edit_sets(sum_freqs=args.keep_freqs, 
                           #with_nulls=args.keep_nulls)
    #stats.info()

    gen = CSetGenerator(stats)

    #stats2 = EditStats(args.corpus, min_err=args.min_err, 
                                    #min_cor=args.min_cor,
                                    #no_spaces=args.no_spaces)

    csets = gen.generate_by_coverage(disjoint=args.disjoint, 
                                     req_cover=args.cover)
    for cset in csets:
        freq = 0
        for word1 in cset:
            for word2 in cset:
                if word1 != word2:
                    freq += stats.edits.get(word1, {}).get(word2, 0)
                    freq += stats.edits.get(word2, {}).get(word1, 0)

        print "{}\t{}".format(freq, ','.join(cset))


def parse_user_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("corpus")
    parser.add_argument("--min-err", type=int, default=5)
    parser.add_argument("--min-cor", type=int, default=3)
    parser.add_argument("--no-spaces", action='store_true')

    parser.add_argument("--keep-freqs", action='store_true')
    parser.add_argument("--keep-nulls", action='store_true')
    parser.add_argument("--disjoint", action='store_true')
    parser.add_argument("--cover", type=float, default=0.80)

    return parser.parse_args()

if __name__ == '__main__':
    main()
