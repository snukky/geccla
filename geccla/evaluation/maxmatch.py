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
                       text_file, cnfs_file, pred_file, m2_file, orig_file,
                       grid_file=None, work_dir=None,
                       num_of_steps=10):

    if not work_dir:
        work_dir = os.getpid()
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    
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

        prec, rec, fscore =  evaluate_m2(out_file, m2_file, orig_file)
        generator.send( (prec, rec, fscore) )

    return generator.next()


def evaluate_m2(text_file, m2_file, orig_file=None, retok_file=None):
    input_file = text_file

    if orig_file:
        #temp_file = input_file + '.nltk'
        #if not os.path.exists(temp_file):
            #log.info("creating file with restored tokenization: {}".format(temp_file))
            #with open(temp_file, 'w+') as file:
                #for line in restore_file_tok(input_file, orig_file):
                    #file.write(line + "\n")
        #input_file = temp_file

        temp_file = input_file + '.cased'
        if not os.path.exists(temp_file):
            log.info("creating file with restored casing: {}".format(temp_file))
            with open(temp_file, 'w+') as file:
                for line in restore_file_case(input_file, orig_file):
                    file.write(line + "\n")
        input_file = temp_file

        if retok_file:
            shutil.copy2(temp_file, retok_file)
            input_file = retok_file

    num_of_lines = cmd.wc(input_file)
    num_of_sents = int(cmd.run("grep -c '^S ' {}".format(m2_file)).strip())

    if num_of_lines != num_of_sents:
        log.error("Input file and M2 file differ in number of sentences: "
            "{} != {}".format(num_of_lines, num_of_sents))

    return m2scorer(input_file, m2_file, 
                    beta=0.5, max_unchanged_words=3,
                    forks=config.THREADS)
