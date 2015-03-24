import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import itertools

from collections import OrderedDict
from prediction import parse_pred_file
from evaluation import evaluate

EPSILON = 0.00001
PRECISION = 5


def run_grid_search(format, 
                    cnfs_file, pred_file, grid_file=None,
                    num_of_steps=10):
    
    if grid_file:
        grid_io = open(grid_file, 'w+')
        grid_io.write("# thr\tdif\tP\nR\nF0.5")

    param_sets = calculate_param_sets(format, pred_file, num_of_steps)
    results = {}

    for thr, dif in param_sets:
        prec, rec, fscore = evaluate(format, cnfs_file, pred_file, thr, dif)
        
        results[(thr, dif)] = fscore

        if grid_file and fscore != 0.0:
            grid_io.write("{thr}\t{dif}\t{prec}\t{rec}\t{fscore}\n" \
                .format(thr=thr, dif=dif, prec=prec, rec=rec, fscore=fscore))
    
    best_results = find_best_results(results)

    if grid_file:
        for (thr, dif), fscore in best_results.iteritems():
            grid_io.write("{thr}\t{dif}\t_\t_\t{fscore}\n" \
                .format(thr=thr, dif=dif, fscore=fscore))
        grid_io.close()

    return best_results.keys()[0]


def calculate_param_sets(format, pred_file, num_of_steps):
    log.debug("number of steps: {}".format(number_of_steps))

    min_thr, max_thr, min_dif, max_dif = find_minmax_params(format, pred_file)
    
    log.debug("min/max threshold: {}/{}".format(min_thr, max_thr))
    log.debug("min/max difference: {}/{}".format(min_dif, max_dif))

    thr_step = (max_thr - min_thr) / float(number_of_steps)
    dif_step = (max_dif - min_dif) / float(number_of_steps)

    log.debug("threshold step: {}".format(thr_step))
    log.debug("difference step: {}".format(dif_step))

    thrs = sorted(list(set([0.0] + __frange(min_thr, max_thr, thr_step))))
    difs = sorted(list(set([0.0] + __frange(min_dif, max_dif, dif_step))))

    return itertools.product(thrs, difs)

def find_minmax_threshold_and_difference(format, pred_file):
    predictions = parse_predictions(pred_file, format)

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
