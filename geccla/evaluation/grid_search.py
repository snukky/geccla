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
    
    preds = parse_pred_file(pred_file, format, conf_set)
    minmax_params = find_minmax_params(preds)

    generator = grid_search_generator(minmax_params, num_of_steps, grid_file)
    thrdif = None

    while True:
        thrdif = generator.next()
        if not thrdif or len(thrdif) == 3:
            break

        prec, rec, fscore =  evaluate(cnfs_file, preds, *thrdif)
        generator.send( (prec, rec, fscore) )

    if thrdif and len(thrdif) == 3:
        return thrdif
    return generator.next()

def grid_search_generator(min_max_params=(0.0, 1.0, 0.0, 1.0), 
                          num_of_steps=10,
                          grid_file=None):

    if grid_file:
        grid_io = open(grid_file, 'w+')
        grid_io.write("# thr\tdif\tP\tR\tF0.5\n")

    param_sets = calculate_param_sets(min_max_params, num_of_steps)
    results = {}
    response = None

    for n, (thr, dif) in enumerate(param_sets):
        log.debug("param set {:0>3d}: ({}, {})".format(n+1, thr, dif))

        response = yield (thr, dif)
        yield
        log.debug("evaluation response: {}".format(response))

        if response is not None:
            prec, rec, fscore = response
        else:
            fscore = 0.0

        results[(thr, dif)] = fscore

        if grid_file and fscore != 0.0:
            grid_line = __format_grid_line(thr, dif, prec, rec, fscore)

            log.info(grid_line.replace("\t", " "))
            grid_io.write(grid_line + "\n")
    
    yield None
   
    best_results = find_best_results(results)

    if grid_file:
        grid_io.write("# best results\n")

        for (thr, dif), fscore in best_results.iteritems():
            grid_io.write(__format_grid_line(thr, dif, fscore=fscore) + "\n")
        grid_io.close()

    (thr, dif), fscore = best_results.items()[0]

    log.info("best result: t={thr:.4f} d={dif:.4f} F0.5={fscore:.4f}" \
        .format(thr=thr, dif=dif, fscore=fscore))

    yield (thr, dif, fscore)

def __format_grid_line(thr, dif, prec=None, rec=None, fscore=None):
    if not prec or not rec:
        return "t={thr:.4f}\td={dif:.4f}\tF0.5={fscore:.4f}" \
            .format(thr=thr, dif=dif, fscore=fscore) 
    return "t={thr:.4f}\td={dif:.4f}\tP={prec:.4f}\tR={rec:.4f}\tF0.5={fscore:.4f}" \
        .format(thr=thr, dif=dif, prec=prec, rec=rec, fscore=fscore)

def calculate_param_sets(min_max_params=(0.0, 1.0, 0.0, 1.0), num_of_steps=10):
    log.info("number of steps: {}".format(num_of_steps))

    min_thr, max_thr, min_dif, max_dif = min_max_params
    
    log.info("min/max threshold: {}/{}".format(min_thr, max_thr))
    log.info("min/max difference: {}/{}".format(min_dif, max_dif))

    thr_step = (max_thr - min_thr) / float(num_of_steps)
    dif_step = (max_dif - min_dif) / float(num_of_steps)

    log.info("threshold step: {}".format(thr_step))
    log.info("difference step: {}".format(dif_step))

    thrs = [0.0] + sorted(list(__frange(min_thr, max_thr, thr_step)[1:-1]))
    difs = [0.0] + sorted(list(__frange(min_dif, max_dif, dif_step)[1:-1]))

    log.info("threshold params: {}".format(thrs))
    log.info("difference params: {}".format(difs))

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
