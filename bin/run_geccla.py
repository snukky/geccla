#!/usr/bin/python

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from classification import ALGORITHMS
from classification import algorithm_to_format

import cmd
import config

from logger import log


CONFUSION_SET = None
ALGORITHM = None
FORMAT = None


def main():
    global CONFUSION_SET, ALGORITHM, FORMAT
    args = parse_user_arguments()

    CONFUSION_SET = args.confusion_set
    ALGORITHM = args.algorithm
    FORMAT = algorithm_to_format(ALGORITHM)


    if not os.path.exists(args.work_dir):
        os.makedirs(args.work_dir)
    log.info("working directory: {}".format(args.work_dir))

    if args.train:
        log.info("TRAINING ON FILE: {}".format(args.train))
        train_file = cmd.filebase_path(args.work_dir, args.train)
        
        if args.cnfs:
            log.info("using confusion file: {}.cnfs".format(train_file))
            cmd.ln(args.train, train_file + '.cnfs')

            if os.path.exists(args.train + '.freq'):
                log.info("...and frequencies: {}.cnfs.freq".format(train_file))
                cmd.ln(args.train + '.freq', train_file + '.cnfs.freq')
        else:
            cmd.ln(args.train, train_file + '.txt')

            train_nulls(train_file)
            find_confusions(args.cnf_opts, train_file, parallel=True)
            extract_features(train_file, args.ext_opts)
        
        print_confusion_statistics(train_file)
        vectorize_features(args.vec_opts, train_file)
        train_classifier(args.model, args.cls_opts, train_file)

        args.cnf_opts += " -n {}.ngrams".format(train_file)
        args.vec_opts += " -v {}.cnfs.feat".format(train_file)
        create_setting_file(args)

    if args.run:
        for i, file in enumerate(args.run):
            log.info("RUNNING ON FILE: {}".format(file))
            run_file = cmd.filebase_path(args.work_dir, file)
            
            cmd.ln(file, run_file + '.txt')

            find_confusions(args.cnf_opts, run_file, parallel=args.eval)
            extract_features(run_file, args.ext_opts)
            vectorize_features(args.vec_opts, run_file)
            run_classifier(args.model, args.cls_opts, run_file)

            inject_predictions(args.evl_opts, run_file)

    if args.eval:
        for i, file in enumerate(args.run):
            log.info("EVALUATING FILE: {}".format(file))
            run_file = cmd.filebase_path(args.work_dir, file)

            evaluate_predictions(args.evl_opts, run_file)

            if args.grid_search:
                new_evl_opts = run_grid_search(run_file)

                cmd.ln(filepath + '.in', filepath + '.best.in')
                cmd.ln(filepath + '.cnfs', filepath + '.best.cnfs')
                cmd.ln(filepath + '.pred', filepath + '.best.pred')

                evaluate_predictions(new_evl_opts, run_file + '.best')
                inject_predictions(new_evl_opts, run_file + '.best')

    if args.conll_eval:
        for i, file in enumerate(args.run):
            log.info("CoNLL EVALUATION ON FILE: {}".format(file))
            run_file = cmd.filebase_path(args.work_dir, file)
        
            evaluate_on_conll_data(run_file, args.conll_eval[i])

            if args.grid_search:
                evaluate_on_conll_data(run_file + '.best', args.conll_eval[i])

            if args.conll_grid_search:
                new_evl_opts = run_conll_grid_search(run_file, args.conll_eval[i])

                cmd.ln(filepath + '.in', filepath + '.m2best.in')
                cmd.ln(filepath + '.cnfs', filepath + '.m2best.cnfs')
                cmd.ln(filepath + '.pred', filepath + '.m2best.pred')
                
                if args.eval:
                    evaluate_predictions(new_evl_opts, run_file + '.m2best')

                inject_predictions(new_evl_opts, run_file + '.m2best')
                evaluate_on_conll_data(run_file + '.m2best', args.conll_eval[i])

    for i, file in enumerate(args.run):
        run_file = cmd.filebase_path(args.work_dir, file)
        if args.eval:
            log.info("\n" + cmd.run("cat {0}.eval".format(run_file)))
        if args.grid_search:
            log.info("\n" + cmd.run("cat {0}.best.eval".format(run_file)))


def train_nulls(filepath):
    log.debug("training <null> positions from file: {}.txt".format(filepath))

    if result_is_ready('{}.ngrams.tok'.format(filepath)) \
            and result_is_ready('{}.ngrams.pos'.format(filepath)) \
            and result_is_ready('{}.ngrams.awc'.format(filepath)):
        return 

    assert_file_exists(filepath + '.txt')

    cmd.run("{root}/train_nulls.py -c {cs} -l tok,pos,awc -n {fp}.ngrams {fp}.txt" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, fp=filepath))

def find_confusions(options, filepath, parallel=False):
    log.debug("finding confusion examples from file: {}.txt".format(filepath))

    if result_is_ready('{}.cnfs.empty'.format(filepath)):
        return

    assert_file_exists(filepath + '.txt')
    input_file = filepath + '.txt'

    err_file = filepath + '.in'
    input_is_parallel = cmd.is_parallel_file(input_file)

    if parallel and not input_is_parallel:
        log.error("file is not parallel but you may think it is :(")
        exit()
        
    if input_is_parallel:
        cmd.run("cut -f1 {0} > {1}".format(input_file, err_file))
        cmd.run("cut -f2 {0} > {1}.gold".format(input_file, filepath))
        if parallel:
            err_file = input_file
    else:
        cmd.ln(input_file, err_file)

    if not options:
        options = " -n {}.ngrams".format(filepath) 

    cmd.run("{root}/find_confs.py -c {cs} -l tok,pos,awc {opts} {err_file} > {fp}.cnfs.empty" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, 
                opts=options, err_file=err_file, fp=filepath))

    if parallel:
        cmd.wdiff(filepath + '.in', filepath + '.gold')

def extract_features(filepath, options=''):
    log.debug("extracting features for file {}.cnfs.empty".format(filepath))

    if result_is_ready('{}.cnfs'.format(filepath)):
        return

    assert_file_exists(filepath + '.cnfs.empty')

    cmd.run("{root}/extract_feats.py {opts} {fp}.in {fp}.cnfs.empty > {fp}.cnfs" \
        .format(root=config.ROOT_DIR, opts=options, fp=filepath))

def print_confusion_statistics(filepath):
    stats = cmd.run("{root}/manage_confs.py -c {cs} {fp}.cnfs" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, fp=filepath))
    log.info("training data statistics:\n{}".format(stats))

def vectorize_features(options, filepath):
    log.debug("vectorizing features from file {}.cnfs".format(filepath))

    if result_is_ready('{}.data'.format(filepath)):
        return

    assert_file_exists(filepath + '.cnfs')

    cmd.run("{root}/vectorize_feats.py -c {cs} -f {frm} {opts} {fp}.cnfs {fp}.data" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT,
                opts=options, fp=filepath))

def train_classifier(model, options, filepath):
    log.debug("training {} model from file {}.data".format(ALGORITHM, filepath))

    if result_is_ready(model):
        return

    assert_file_exists(filepath + '.data')

    cmd.run("{root}/run_classifier.py -t -a {alg} -c {cs} -o ' {opts}' {model} {fp}.data" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, alg=ALGORITHM,
                opts=options, model=model, fp=filepath))

def run_classifier(model, options, filepath):
    log.debug("running {} model from file {}.data".format(ALGORITHM, filepath))

    if result_is_ready('{}.pred'.format(filepath)):
        return

    assert_file_exists(model)
    assert_file_exists(filepath + '.data')

    cmd.run("{root}/run_classifier.py -a {alg} -c {cs} -o ' {opts}' {model} {fp}.data -p {fp}.pred" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, alg=ALGORITHM,
                opts=options, model=model, fp=filepath))

def inject_predictions(options, filepath):
    log.debug("injecting predictions {0}.pred into {0}.in".format(filepath))

    if result_is_ready('{}.out'.format(filepath)):
        return

    assert_file_exists(filepath + '.in')
    assert_file_exists(filepath + '.cnfs')
    assert_file_exists(filepath + '.pred')

    cmd.run("{root}/inject_preds.py -c {cs} -f {frm} {opts} {fp}.in {fp}.cnfs {fp}.pred > {fp}.out" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT, 
                opts=options, fp=filepath))
    
    cmd.wdiff(filepath + '.in', filepath + '.out')

def evaluate_predictions(options, filepath):
    log.debug("evaluating predictions {0}.pred on {0}.cnfs".format(filepath))

    assert_file_exists(filepath + '.cnfs')
    assert_file_exists(filepath + '.pred')
    
    cmd.run("echo 'Accuracy evaluation on {0}.pred ({1})' >> {0}.eval" \
        .format(filepath, options))
    cmd.run("{root}/eval_preds.py -c {cs} -f {frm} {opts} {fp}.cnfs {fp}.pred >> {fp}.eval" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT, 
                opts=options, fp=filepath))

def run_grid_search(filepath):
    log.debug("running grid searching on {0}.pred and {0}.cnfs".format(filepath))

    assert_file_exists(filepath + '.cnfs')
    assert_file_exists(filepath + '.pred')

    output = cmd.run("{root}/tune_preds.py -c {cs} -f {frm} -g {fp}.eval.grid {fp}.cnfs {fp}.pred" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT, fp=filepath))

    thr, dif = output.split("\t")[:2]
    log.debug("grid search found threshold options: t={} d={}".format(thr, dif))

    return " -t {} -d {}".format(thr, dif)

def evaluate_on_conll_data(filepath, year):
    log.debug("evaluating on CoNLL {} test sets".format(year))

    assert_file_exists(filepath + '.out')

    for name, m2_file in config.CONLL.TEST_SETS[year].iteritems():
        orig_tok = config.CONLL.ORIGINAL_TOKS[year]
        cmd.run("{root}/eval_m2.py -o {orig} -t {fp}.out.retok {fp}.out {m2} >> {fp}.eval.m2" \
            .format(root=config.ROOT_DIR, orig=orig_tok, m2=m2_file, fp=filepath))
    
    cmd.wdiff(filepath + '.out', filepath + '.out.retok')

    orig_tok = config.CONLL.ORIGINAL_TOKS[year]
    cmd.ln(filepath + '.out.retok', filepath + '.out.conll')
    cmd.wdiff(orig_tok, filepath + '.out.conll')

def run_conll_grid_search():
    log.debug("running CoNLL grid searching on {0}.pred and {0}.cnfs".format(filepath))

    assert_file_exists(filepath + '.in')
    assert_file_exists(filepath + '.cnfs')
    assert_file_exists(filepath + '.pred')

    m2_file = config.CONLL.TEST_SETS[year]['allerrors']
    orig_tok = config.CONLL.ORIGINAL_TOKS[year]

    output = cmd.run("{root}/tune_m2.py -c {cs} -f {frm} -g {fp}.eval.m2.grid -w {fp}.m2gs "
        "--m2 {m2} -o {orig} {fp}.in {fp}.cnfs {fp}.pred" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT, 
                m2=m2_file, orig=orig_tok, fp=filepath))

    thr, dif = output.split("\t")[:2]
    log.debug("CoNLL grid search found threshold options: t={} d={}".format(thr, dif))

    return " -t {} -d {}".format(thr, dif)

def result_is_ready(file):
    if os.path.exists(file):
        if os.stat(file).st_size == 0:
            log.error("result file {} exists but is empty!".format(file))
            exit()
        log.debug("step is skipped as result file {} is ready".format(file))
        return True
    return False


def assert_file_exists(file):
    if not os.path.exists(file):
        log.error("file {} does not exist".format(file))
        exit()
    if os.stat(file).st_size == 0:
        log.error("file {} is empty".format(file))
        exit()


def parse_user_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--train", type=str, 
        help="train classifier on parallel texts")
    parser.add_argument("-r", "--run", type=str, nargs="*", 
        help="run classifier")
    parser.add_argument("-a", "--algorithm", choices=ALGORITHMS, 
        help="classification algorithm")
    parser.add_argument("-m", "--model", required=True, type=str, 
        help="classifier model")
    parser.add_argument('-c', '--confusion-set', type=str, required=True, 
        help="confusion set as comma-separated list of words")

    input = parser.add_argument_group("input/output arguments")
    input.add_argument("--cnfs", action='store_true', 
        help="training data are .cnfs files")
    input.add_argument("-d", "--work-dir", default=str(os.getpid()), type=str, 
        help="working directory")

    eval = parser.add_argument_group("evaluation arguments")
    eval.add_argument("-e", "--eval", action='store_true', 
        help="evaluate inputs; each input file should contain parallel texts")
    eval.add_argument("--grid-search", action='store_true', 
        help="estimates evaluation threshold values using grid search")

    eval.add_argument("--conll-eval", type=str, nargs="*", 
        choices=config.CONLL.TEST_SETS.keys(), 
        help="evaluate on predefined CoNLL Shared Task test set")
    #eval.add_argument("--conll-grid-search", action='store_true', 
        #help="estimates evaluation threshold values using grid search")

    opts = parser.add_argument_group("external scripts' arguments")
    opts.add_argument("--cnf-opts", type=str, default='',
        help="options for finding confusions")
    opts.add_argument("--ext-opts", type=str, default='',
        help="options for feature extraction")
    opts.add_argument("--vec-opts", type=str, default='', 
        help="options for vectorization")
    opts.add_argument("--cls-opts", type=str, default='', 
        help="options for classification algorithm")
    opts.add_argument("--evl-opts", type=str, default='', 
        help="options for evaluation")

    args = parser.parse_args()

    if args.train:
        assert_file_exists(args.train)
            
    if args.run:
        for file in args.run:
            assert_file_exists(file)
        args = load_setting_file(args)

    if args.eval and not args.run:
        raise ArgumentError("argument --eval requires --run")
    if args.conll_eval and not args.run:
        raise ArgumentError("argument --conll-eval requires --run")
    if args.conll_eval and len(args.run) != len(args.conll_eval):
        raise ArgumentError("argument --conll-eval has to be specified once"
            " for each --run file")
    if args.grid_search and not args.eval:
        raise ArgumentError("argument --grid-search requires --eval")
    #if args.conll_grid_search and not args.conll_eval:
        #raise ArgumentError("argument --conll-grid-search requires"
            #" --conll-eval")

    #if args.algorithm not in ALGORITHMS:
        #raise ArgumentError("argument --algorithm with value {}" \
            #" probably requires --default".format(args.algorithm))

    log.debug(args)
    return args

def load_setting_file(args):
    setting_file = args.model + '.settings'
    log.info("loading setting file: {}".format(setting_file))

    if not os.path.exists(setting_file):
        log.warn("setting file {} does not exist".format(setting_file))
        return args

    with open(setting_file) as file:
        for line in file:
            opt, val = line.strip().split('=')

            if opt == 'use' and not args.algorithm:
                log.debug("setting algorithm: {}".format(val))
                args.algorithm = val

            if opt == 'set' and not args.confusion_set:
                log.debug("confusion set: {}".format(val))
                args.confusion_set = val

            elif opt == 'cnf' and not args.cnf_opts:
                log.debug("loading confusion extraction options: {}".format(val))
                args.cnf_opts = val
            elif opt == 'ext' and not args.ext_opts:
                log.debug("loading feature extraction options: {}".format(val))
                args.ext_opts = val
            elif opt == 'vec' and not args.vec_opts:
                log.debug("loading vectorization options: {}".format(val))
                args.vec_opts = val
            elif opt == 'cls' and not args.cls_opts:
                log.debug("loading classification options: {}".format(val))
                args.cls_opts = val
            elif opt == 'evl' and not args.evl_opts:
                log.debug("loading evaluation options: {}".format(val))
                args.evl_opts = val
            else:
                log.warn("unrecognized setting: {}={}".format(opt, val))

    return args

def create_setting_file(args):
    setting_file = args.model + '.settings'
    log.info("creating setting file: {}".format(setting_file))

    with open(setting_file, 'w+') as file:
        file.write("use={}\n".format(args.algorithm))
        file.write("set={}\n".format(args.confusion_set))
        file.write("cnf={}\n".format(args.cnf_opts.strip()))
        file.write("ext={}\n".format(args.ext_opts.strip()))
        file.write("vec={}\n".format(args.vec_opts.strip()))
        file.write("cls={}\n".format(args.cls_opts.strip()))
        file.write("evl={}\n".format(args.evl_opts.strip()))


if __name__ == '__main__':
    main()
