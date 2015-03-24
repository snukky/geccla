#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from confusions import parse_conf_line
from evaluation import metrics


def evaluate_cnfs_coverage(cnfs_file, gold_cnfs_file):
    values = []
    with open(cnfs_file) as cnfs_io:
        for i, line in enumerate(cnfs_io):
            n, i, j, _, _, _ = parse_conf_line(line)
            values.append("{}_{}_{}".format(n, i, j))
    system_values = set(values)

    values = []
    with open(gold_cnfs_file) as gold_cnfs_io:
        for i, line in enumerate(gold_cnfs_io):
            n, i, j, _, _, _ = parse_conf_line(line)
            values.append("{}_{}_{}".format(n, i, j))
    gold_values = set(values)
    
    tp, fp, tn, fn = 0, 0, 0, 0

    for val in gold_values.union(system_values):
        if val in gold_values:
            if val in system_values:
                tp += 1
            else:
                fn += 1
        else:
            if val in system_values:
                fp += 1
            else:
                tn += 1
    
    return (metrics.precision(tp, tn, fp, fn),
            metrics.recall(tp, tn, fp, fn),
            metrics.fscore(tp, tn, fp, fn, 1.0))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: {} system.cnfs gold.cnfs".format(sys.argv[0])
        exit()

    prec, rec, fscore = evaluate_cnfs_coverage(sys.argv[1], sys.argv[2])

    print "# evaluation {} according to {}".format(sys.argv[1], sys.argv[2])
    print "Precision   : %.4f" % prec
    print "Recall      : %.4f" % rec
    print "F1.0        : %.4f" % fscore
