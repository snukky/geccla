import os
import sys
import shutil

if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

from preprocess.letter_case import restore_file_case
from prediction.output_formatter import inject_predictions
from prediction import parse_pred_file

from evaluation.m2scorer_fork import m2scorer
from evaluation.grid_search import grid_search_generator
from evaluation.grid_search import find_minmax_params

import cmd
from logger import log
import config


def run_m2_grid_search(conf_set, format, 
                       text_file, cnfs_file, pred_file, m2_file,
                       grid_file=None, work_dir=None,
                       num_of_steps=10):

    if not work_dir:
        work_dir = os.getpid()
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    cmd.run("cat {} | grep '^S ' | cut -c3- > {}/m2.txt".format(m2_file, work_dir))
    err_file = cmd.cut(work_dir + '/m2.txt', work_dir + '/m2.err')

    preds = parse_pred_file(pred_file, format, conf_set)
    minmax_params = find_minmax_params(preds)

    generator = grid_search_generator(minmax_params, num_of_steps, grid_file)
    
    while True:
        thrdif = generator.next()
        if not thrdif:
            break

        thr, dif = thrdif
        out_file = os.path.join(work_dir, "output.{0:.4f}-{1:.4f}.txt".format(thr, dif))

        inject_predictions(conf_set, format, 
                           text_file, cnfs_file, pred_file, 
                           thr, dif, out_file)
        cmd.wdiff(err_file, out_file)

        prec, rec, fscore =  evaluate_m2(out_file, m2_file)
        generator.send( (prec, rec, fscore) )

    return generator.next()


def evaluate_m2(text_file, m2_file):
    num_of_lines = cmd.wc(text_file)
    num_of_sents = int(cmd.run("grep -c '^S ' {}".format(m2_file)).strip())

    if num_of_lines != num_of_sents:
        log.error("Input file and M2 file differ in number of sentences: "
            "{} != {}".format(num_of_lines, num_of_sents))

    #return m2scorer(text_file, m2_file, 
                    #beta=0.5, max_unchanged_words=3,
                    #forks=config.THREADS)

    result = cmd.run("python {root}/evaluation/m2scorer_fork.py --beta 0.5 "
        "--max_unchanged_words 3 {txt} {m2}" \
        .format(root=config.ROOT_DIR, txt=text_file, m2=m2_file))

    return tuple(float(line.split()[-1]) for line in result.strip().split("\n"))
