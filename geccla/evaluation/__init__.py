import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from prediction import iterate_confs_and_preds
from evaluation import metrics

from logger import log


def evaluate(cnfs_file, preds, thr, dif):
    """
    Evaluates classifier's predictions according to F_0.5 score.
    """
    tp, tn, fp, fn, xyz = contingency_table(cnfs_file, preds, thr, dif)

    return (metrics.precision(tp, tn, fp + xyz, fn),
            metrics.recall(tp, tn, fp + xyz, fn),
            metrics.fscore(tp, tn, fp + xyz, fn))

def contingency_table(cnfs_file, preds, thr=None, dif=None):
    """
    Returns a tuple (TP, TN, FP, FN, XYZ), where XYZ for correction task
    is equal to FP and for detection task is equal to TP.
    """
    log.info("contingency table values for: {}".format(cnfs_file))

    tp, fp, tn, fn, xyz = 0, 0, 0, 0, 0
    results = iterate_confs_and_preds(cnfs_file, preds, thr, dif, lowercase=True)

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

    log.info("TP = {} TN = {} FP = {} FN = {} xyz = {}" \
        .format(tp, tn, fp, fn, xyz))

    return (tp, tn, fp, fn, xyz)
