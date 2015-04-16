#!/usr/bin/python

import argparse

from classification import FORMATS

from prediction import parse_pred_file
from evaluation import contingency_table
from evaluation import metrics


def main():
    args = parse_user_arguments()

    preds = parse_pred_file(args.pred_file, args.format, args.confusion_set)

    tp, tn, fp, fn, xyz = contingency_table(args.cnfs_file, preds, 
                                            args.threshold, args.difference)
    all = tn + fp + fn + tp + xyz
    
    print "### Evaluation of file {}".format(args.cnfs_file)
    print ""

    print "threshold   : %.4f " % (args.threshold or 0)
    print "difference  : %.4f " % (args.difference or 0)
    print ""

    print "# Statistics:"
    print "Prevalence  : %.4f" % metrics.prevalence(tp, tn, fp + xyz, fn)
    print "Bias        : %.4f" % metrics.bias(tp, tn, fp + xyz, fn)
    print "Changes     : %d" % (tp + fp)
    print ""

    print "# WAS evaluation scheme:"
    print "TN x/x/x    : %.4f (%d)" % (tn/float(all), tn)
    print "FP x/x/y    : %.4f (%d)" % (fp/float(all), fp)
    print "FN x/y/x    : %.4f (%d)" % (fn/float(all), fn)
    print "TP x/y/y    : %.4f (%d)" % (tp/float(all), tp)
    print "*  x/y/z    : %.4f (%d)" % (xyz/float(all), xyz)
    print ""

    if args.edit_counts:
        print "# Simple accuracy:"
        acc, aa, ab, skipped = metrics.edits_count(tp, tn, fp, fn, xyz)
        print "All edits   : %.4f" % acc
        print "A-A edits   : %.4f" % aa
        print "A-B edits   : %.4f" % ab
        print "A-B skipped : %.4f" % skipped
        print ""

    if args.detection_task:
        print "# Detection task:"
        print "Accuracy    : %.4f" % metrics.accuracy(tp + xyz, tn, fp, fn)
        print "Specificity : %.4f" % metrics.specificity(tp + xyz, tn, fp, fn)
        print "Fall-out    : %.4f" % metrics.fall_out(tp + xyz, tn, fp, fn)
        print "Precision   : %.4f" % metrics.precision(tp + xyz, tn, fp, fn)
        print "Recall      : %.4f" % metrics.recall(tp + xyz, tn, fp, fn)
        print "F0.5        : %.4f" % metrics.fscore(tp + xyz, tn, fp, fn)
        print ""
    
    print "# Correction task:"
    print "Accuracy    : %.4f" % metrics.accuracy(tp, tn, fp + xyz, fn)
    print "Specificity : %.4f" % metrics.specificity(tp, tn, fp + xyz, fn)
    print "Fall-out    : %.4f" % metrics.fall_out(tp, tn, fp + xyz, fn)
    print "Precision   : %.4f" % metrics.precision(tp, tn, fp + xyz, fn)
    print "Recall      : %.4f" % metrics.recall(tp, tn, fp + xyz, fn)
    print "F0.5        : %.4f" % metrics.fscore(tp, tn, fp + xyz, fn)
    print ""
  
def parse_user_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('cnfs_file', help=".cnfs file")
    parser.add_argument('pred_file', help="classifier predictions")

    req = parser.add_argument_group("required arguments")
    req.add_argument('-c', '--confusion-set', required=True,
        help="confusion set as comma-separated list of words")
    req.add_argument('-f', '--format', required=True, choices=FORMATS,
        help="prediction data format")

    eval = parser.add_argument_group("evaluation arguments")
    eval.add_argument('-t', '--threshold', type=float,
        help="minimum classifier confidence")
    eval.add_argument('-d', '--difference', type=float,
        help="minimum difference between best and second classifier label "
        "confidences") 

    out = parser.add_argument_group("output arguments")
    out.add_argument('-a', '--all', action='store_true',
        help="show all evaluation metrics and informations")
    out.add_argument('--was-scheme', action='store_true',
        help="show Written-Annotation-System evaluation scheme")
    out.add_argument('--edit-counts', action='store_true',
        help="show simple edit counts")
    out.add_argument('--detection-task', action='store_true',
        help="show evaluation for detection task")

    args = parser.parse_args()
    if args.all:
        args.was_scheme = true
        args.edit_counts = true
        args.detection_task = true
    return args


if __name__ == '__main__':
    main()
