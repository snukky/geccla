#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from confusions import parse_conf_line
from evaluation import metrics

from logger import log


def evaluate_nulls_coverage(cnfs_file, gold_cnfs_file):
    system_confs = {}
    with open(cnfs_file) as cnfs_io:
        for i, line in enumerate(cnfs_io):
            n, i, j, err, _, _ = parse_conf_line(line)
            system_confs["{}_{}_{}".format(n, i, j)] = err == '<null>'
    system_values = set(system_confs.keys())

    gold_confs = {}
    with open(gold_cnfs_file) as gold_cnfs_io:
        for i, line in enumerate(gold_cnfs_io):
            n, i, j, err, _, _ = parse_conf_line(line)
            gold_confs["{}_{}_{}".format(n, i, j)] = err == '<null>'
    gold_values = set(gold_confs.keys())
    
    tp, fp, tn, fn = 0, 0, 0, 0

    for val in gold_values.union(system_values):
        if val in gold_values:
            if val in system_values:
                if gold_confs[val] and system_confs[val]:
                    tp += 1
                elif not gold_confs[val] and not system_confs[val]:
                    tn += 1
                else:
                    log.warn("not handled case!")
            else:
                fn += 1
        else:
            if system_confs[val] == True:
                fp += 1
            else:
                log.warn("not handled case!")

    return (tp, tn, fp, fn)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: {} system.cnfs gold.cnfs".format(sys.argv[0])
        exit()

    tp, tn, fp, fn = evaluate_nulls_coverage(sys.argv[1], sys.argv[2])

    prec = metrics.precision(tp, tn, fp, fn)
    rec = metrics.recall(tp, tn, fp, fn)
    fscore = metrics.fscore(tp, tn, fp, fn, 1.0)

    print "# evaluation {} according to {}".format(sys.argv[1], sys.argv[2])
    print "TP/TN/FP/FN : %d/%d/%d/%d" % (tp, tn, fp, fn)
    print "Precision   : %.4f" % prec
    print "Recall      : %.4f" % rec
    print "F1.0        : %.4f" % fscore
