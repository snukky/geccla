import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from prediction import iterate_confs_and_preds
from prediction import parse_pred_file
from evaluation import metrics

from logger import log


def print_complete_evaluation(conf_set, format, 
                              cnfs_file, pred_file, 
                              thr, dif):

    preds = parse_pred_file(pred_file, format, conf_set)
    tp, tn, fp, fn, xyz = evaluate_by_confusion_matrix(cnfs_file, preds, thr, dif)
    
    print "### evaluation for file {}".format(cnfs_file)
    print ""

    if thr:
        print "threshold   : %.4f " % thr
    if dif:
        print "difference  : %.4f " % dif
    if thr or dif:
        print ""

    print "# Simple accuracy:"
    acc, aa, ab, skipped = metrics.edits_count(tp, tn, fp, fn, xyz)
    print "All edits   : %.4f" % acc
    print "A-A edits   : %.4f" % aa
    print "A-B edits   : %.4f" % ab
    print "A-B skipped : %.4f" % skipped
    print ""

    print "# Detection task:"
    print "Accuracy    : %.4f" % metrics.accuracy(tp + xyz, tn, fp, fn)
    print "Precision   : %.4f" % metrics.precision(tp + xyz, tn, fp, fn)
    print "Recall      : %.4f" % metrics.recall(tp + xyz, tn, fp, fn)
    print "F0.5        : %.4f" % metrics.fscore(tp + xyz, tn, fp, fn)
    print ""
    
    print "# Correction task:"
    print "Accuracy    : %.4f" % metrics.accuracy(tp, tn, fp + xyz, fn)
    print "Precision   : %.4f" % metrics.precision(tp, tn, fp + xyz, fn)
    print "Recall      : %.4f" % metrics.recall(tp, tn, fp + xyz, fn)
    print "F0.5        : %.4f" % metrics.fscore(tp, tn, fp + xyz, fn)
    print ""

def evaluate(cnfs_file, preds, thr, dif):
    """
    Evaluates classifier's predictions according to F_0.5 score.
    """
    tp, tn, fp, fn, xyz = evaluate_by_confusion_matrix(cnfs_file, preds, thr, dif)

    return (metrics.precision(tp, tn, fp + xyz, fn),
            metrics.recall(tp, tn, fp + xyz, fn),
            metrics.fscore(tp, tn, fp + xyz, fn))

def evaluate_by_confusion_matrix(cnfs_file, preds, 
                                 thr=None, dif=None):
    """
    Returns a tuple (TP, TN, FP, FN, XYZ), where XYZ for correction task
    is equal to FP and for detection task is equal to TP.
    """
    log.debug("confusion matrix scores: {}".format(cnfs_file))

    tp, fp, tn, fn, xyz = 0, 0, 0, 0, 0
    results = iterate_confs_and_preds(cnfs_file, preds, thr, dif)

    for err, cor, pred in results:
        # figure 4. WAS evaluation scheme
        if err == cor:
            if cor == pred:
                tn += 1
            else:
                fp += 1
        else:
            if cor == pred:
                tp += 1
            else:
                if err == pred:
                    fn += 1
                else:
                    xyz += 1

    log.debug("TP = {} TN = {} FP = {} FN = {} xyz = {}" \
        .format(tp, tn, fp, fn, xyz))

    return (tp, tn, fp, fn, xyz)
