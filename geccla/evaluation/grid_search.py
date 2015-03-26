import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import itertools

from collections import OrderedDict
from prediction import parse_pred_file
from evaluation import evaluate

from logger import log


EPSILON = 0.00001
PRECISION = 5


def run_grid_search(conf_set, format, 
                    cnfs_file, pred_file, grid_file=None,
                    num_of_steps=10):
    
    if grid_file:
        grid_io = open(grid_file, 'w+')
        grid_io.write("# thr\tdif\tP\tR\tF0.5\n")

    preds = parse_pred_file(pred_file, format, conf_set)
    param_sets = calculate_param_sets(preds, num_of_steps)
    results = {}

    for thr, dif in param_sets:
        prec, rec, fscore = evaluate(cnfs_file, preds, thr, dif)
        
        results[(thr, dif)] = fscore

        if grid_file and fscore != 0.0:
            log.debug(__format_grid_line(thr, dif, prec, rec, fscore))
            grid_io.write(__format_grid_line(thr, dif, prec, rec, fscore) + "\n")
    
    best_results = find_best_results(results)

    if grid_file:
        grid_io.write("# best results\n")

        for (thr, dif), fscore in best_results.iteritems():
            grid_io.write(__format_grid_line(thr, dif, fscore=fscore) + "\n")
        grid_io.close()

    (thr, dif), fscore = best_results.items()[0]

    log.info("best result: t={thr:.4f} d={dif:.4f} F0.5={fscore:.4f}" \
        .format(thr=thr, dif=dif, fscore=fscore))

    return (thr, dif, fscore)

def __format_grid_line(thr, dif, prec=None, rec=None, fscore=None):
    if not prec or not rec:
        return "t={thr:.4f} d={dif:.4f} F0.5={fscore:.4f}" \
            .format(thr=thr, dif=dif, fscore=fscore) 
    return "t={thr:.4f} d={dif:.4f} P={prec:.4f} R={rec:.4f} F0.5={fscore:.4f}" \
        .format(thr=thr, dif=dif, prec=prec, rec=rec, fscore=fscore)

def calculate_param_sets(preds, num_of_steps):
    log.debug("number of steps: {}".format(num_of_steps))

    min_thr, max_thr, min_dif, max_dif = find_minmax_params(preds)
    
    log.debug("min/max threshold: {}/{}".format(min_thr, max_thr))
    log.debug("min/max difference: {}/{}".format(min_dif, max_dif))

    thr_step = (max_thr - min_thr) / float(num_of_steps)
    dif_step = (max_dif - min_dif) / float(num_of_steps)

    log.debug("threshold step: {}".format(thr_step))
    log.debug("difference step: {}".format(dif_step))

    thrs = sorted(list(set([0.0] + __frange(min_thr, max_thr, thr_step))))
    difs = sorted(list(set([0.0] + __frange(min_dif, max_dif, dif_step))))

    log.debug("threshold params: {}".format(thrs))
    log.debug("difference params: {}".format(difs))

    return itertools.product(thrs, difs)

def find_minmax_params(predictions):
    min_thr, max_thr = 100.0, -100.0
    min_dif, max_dif = 100.0, -100.0

    for answers in predictions:
        values = sorted([round(val, PRECISION) for val in answers.values()])
        
        if len(values) >= 1 and values[0] is not None:
            thr = values[-1]
            if thr <= min_thr or min_thr is None:
                min_thr = thr
            if thr >= max_thr or max_thr is None:
                max_thr = thr

        if len(values) >= 2:
            dif = values[-1] - values[-2] 
            if dif <= min_dif or min_dif is None:
                min_dif = dif
            if dif >= max_dif or max_dif is None:
                max_dif = dif

    if min_thr is None:
        min_thr = 0.0
    if max_thr is None:
        max_thr = 0.0
    if min_dif is None:
        min_dif = 0.0
    if max_dif is None:
        max_dif = 0.0

    return (min_thr, max_thr, min_dif, max_dif)

def __frange(start, stop, step, eps=EPSILON, prec=PRECISION):
    values = []
    if start > stop:
        return []
    if start == stop:
        return [round(start, prec)]
    val = start
    while val <= stop + eps:
        values.append(round(val, prec))
        val += step
    return values

def find_best_results(results):
    max_fscore = max(results.values())
    best_results = {}

    for (thr, dif), fscore in results.iteritems():
        if fscore == max_fscore:
            best_results[(thr, dif)] = fscore

    # sort by the sum of threshold and difference
    return OrderedDict(
        sorted(best_results.items(), key=lambda p: p[0][1] + p[0][1])
    )
