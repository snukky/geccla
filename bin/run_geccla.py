#!/usr/bin/python

import os
import sys
import argparse
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from classification import ALGORITHMS
from classification import algorithm_to_format
from classification import NON_TUNNED_ALGORITHMS

from features import FEATURE_SETS

from confusion_set import ConfusionSet

from preprocess.artordets import normalize_indef_articles
from preprocess.artordets import restore_indef_articles

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
        train_file = cmd.base_filepath(args.work_dir, args.train)
        
        if args.nrm_articles:
            log.info("normalizing indefinite articles: {}.txt".format(train_file))
            normalize_indef_articles(args.train, train_file + '.txt')
        else:
            cmd.ln(args.train, train_file + '.txt')

        #if null_in_confset():
            #train_nulls(train_file)
            #args.cnf_opts += " -n {}.ngrams".format(train_file)

        find_confusions(args.cnf_opts, train_file, parallel=True)
        print_confusion_statistics(train_file, args.mng_opts)
        extract_features(train_file, args.ext_opts)
        
        vectorize_features(args.vec_opts, train_file)
        train_classifier(args.model, args.cls_opts, train_file)

        args.vec_opts += " -v {}.cnfs.feat".format(train_file)
        create_setting_file(args)

    if args.run:
        for run in args.run:
            log.info("RUNNING ON FILE: {}".format(run))
            run_file = cmd.base_filepath(args.work_dir, run)
        
            if args.m2:
                cmd.ln(run, run_file + '.m2')
                make_m2_parallel(run_file)
            else:
                cmd.ln(run, run_file + '.txt')

            if args.nrm_articles:
                log.info("normalizing indefinite articles: {}.txt".format(train_file))
                shutil.move(run_file + '.txt', run_file + '.txt.nonrm')
                normalize_indef_articles(run_file + '.txt.nonrm', run_file + '.txt')

            find_confusions(args.cnf_opts, run_file, parallel=args.eval)
            print_confusion_statistics(run_file)
            extract_features(run_file, args.ext_opts)

            vectorize_features(args.vec_opts, run_file)
            run_classifier(args.model, args.cls_opts, run_file)

            inject_predictions(args.evl_opts, run_file, args.nrm_articles)

            if args.eval:
                log.info("EVALUATING FILE: {}".format(run))

                evaluate_predictions(args.evl_opts, run_file)
                if args.m2:
                    evaluate_m2(run_file)

    if args.tune:
        log.info("TUNNING ON FILE: {}".format(args.tune))
        tune_file = cmd.base_filepath(args.work_dir, args.tune)

        if args.m2:
            cmd.ln(args.tune, tune_file + '.m2')
            make_m2_parallel(tune_file)
        else:
            cmd.ln(args.tune, tune_file + '.txt')

        find_confusions(args.cnf_opts, tune_file, parallel=True)
        print_confusion_statistics(tune_file)
        extract_features(tune_file, args.ext_opts)

        vectorize_features(args.vec_opts, tune_file)
        run_classifier(args.model, args.cls_opts, tune_file)

        inject_predictions('', tune_file, args.nrm_articles)
         
        log.info("GRID SEARCHING ON FILE: {}".format(args.tune))
        if args.m2:
            new_evl_opts = run_m2_grid_search(tune_file, args.nrm_articles)
        else:
            new_evl_opts = run_grid_search(tune_file)
        
        args.evl_opts = new_evl_opts
        create_setting_file(args)
    
    if args.tune and args.eval:
        for run in args.run:
            log.info("EVALUATING AFTER TUNNING ON FILE: {}".format(run))
            run_file = cmd.base_filepath(args.work_dir, run)

            cmd.ln(run_file + '.cnfs', run_file + '.best.cnfs')
            cmd.ln(run_file + '.pred', run_file + '.best.pred')
            evaluate_predictions(new_evl_opts, run_file + '.best')

            cmd.ln(run_file + '.in', run_file + '.best.in')
            inject_predictions(new_evl_opts, run_file + '.best', args.nrm_articles)

            if args.m2:
                cmd.ln(run_file + '.m2', run_file + '.best.m2')
                evaluate_m2(run_file + '.best')
            
    if args.run:
        for run in args.run:
            run_file = cmd.base_filepath(args.work_dir, run)
            if args.eval:
                log.info("\n" + cmd.run("cat {0}.eval".format(run_file)))
            if args.tune:
                log.info("\n" + cmd.run("cat {0}.best.eval".format(run_file)))


def train_nulls(filepath):
    log.info("training <null> positions from file: {}.txt".format(filepath))

    if result_is_ready('{}.ngrams.tok'.format(filepath)) \
            and result_is_ready('{}.ngrams.pos'.format(filepath)) \
            and result_is_ready('{}.ngrams.awc'.format(filepath)):
        return 

    assert_file_exists(filepath + '.txt')

    cmd.run("{root}/train_nulls.py -c {cs} -l tok,pos,awc -n {fp}.ngrams {fp}.txt" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, fp=filepath))

def find_confusions(options, filepath, parallel=False, confset=None):
    log.info("finding confusion examples from file: {}.txt".format(filepath))

    if not options:
        options = ''

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
        cmd.cut(input_file, err_file)
        cmd.cut(input_file, filepath + '.gold', col=2)
        if parallel:
            err_file = input_file
    else:
        cmd.ln(input_file, err_file)
    
    if ('-c ' not in options) and ('--confusion-set ' not in options):
        options += ' -c {}'.format(CONFUSION_SET)

    cmd.run("{root}/find_confs.py {opts} {err_file} > {fp}.cnfs.empty" \
        .format(root=config.ROOT_DIR, opts=options, err_file=err_file, 
            fp=filepath))

    if parallel:
        cmd.wdiff(filepath + '.in', filepath + '.gold')

def extract_features(filepath, options=''):
    log.info("extracting features for file {}.cnfs.empty".format(filepath))

    if result_is_ready('{}.cnfs'.format(filepath)):
        return

    assert_file_exists(filepath + '.cnfs.empty')

    cmd.run("{root}/extract_feats.py {opts} {fp}.in {fp}.cnfs.empty > {fp}.cnfs" \
        .format(root=config.ROOT_DIR, opts=options, fp=filepath))

def print_confusion_statistics(filepath, options=''):
    stats = cmd.run("{root}/manage_confs.py {opts} {fp}.cnfs.empty" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, 
                opts=options, fp=filepath))
    log.info("training data statistics:\n{}".format(stats))

def vectorize_features(options, filepath):
    log.info("vectorizing features from file {}.cnfs".format(filepath))

    if result_is_ready('{}.data'.format(filepath)):
        return

    assert_file_exists(filepath + '.cnfs')

    cmd.run("{root}/vectorize_feats.py -c {cs} -f {frm} {opts} {fp}.cnfs {fp}.data" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT,
                opts=options, fp=filepath))

def train_classifier(model, options, filepath):
    log.info("training {} model from file {}.data".format(ALGORITHM, filepath))

    if result_is_ready(model):
        return

    assert_file_exists(filepath + '.data')

    cmd.run("{root}/run_classifier.py -t -a {alg} -c {cs} -o ' {opts}' {model} {fp}.data" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, alg=ALGORITHM,
                opts=options, model=model, fp=filepath))

def run_classifier(model, options, filepath):
    log.info("running {} model from file {}.data".format(ALGORITHM, filepath))

    if result_is_ready('{}.pred'.format(filepath)):
        return

    assert_file_exists(model)
    assert_file_exists(filepath + '.data')

    cmd.run("{root}/run_classifier.py -a {alg} -c {cs} -o ' {opts}' {model} {fp}.data -p {fp}.pred" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, alg=ALGORITHM,
                opts=options, model=model, fp=filepath))

def inject_predictions(options, filepath, nrm_articles=False):
    log.info("injecting predictions {0}.pred into {0}.in".format(filepath))

    if result_is_ready('{}.out'.format(filepath)):
        return
    
    assert_file_exists(filepath + '.in')
    assert_file_exists(filepath + '.cnfs')
    assert_file_exists(filepath + '.pred')

    if nrm_articles:
        options += ' --restore-articles'

    cmd.run("{root}/inject_preds.py -c {cs} -f {frm} {opts} {fp}.in {fp}.cnfs {fp}.pred > {fp}.out" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT, 
                opts=options, fp=filepath))
    
    cmd.wdiff(filepath + '.in', filepath + '.out')

def evaluate_predictions(options, filepath):
    log.info("evaluating predictions {0}.pred on {0}.cnfs".format(filepath))

    assert_file_exists(filepath + '.cnfs')
    assert_file_exists(filepath + '.pred')
    
    cmd.run("{root}/eval_preds.py -c {cs} -f {frm} {opts} {fp}.cnfs {fp}.pred >> {fp}.eval" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT, 
                opts=options, fp=filepath))

def run_grid_search(filepath):
    log.info("running grid searching on {0}.pred and {0}.cnfs".format(filepath))

    if result_is_ready('{}.params'.format(filepath)):
        return cmd.run('cat {}.params'.format(filepath))

    assert_file_exists(filepath + '.cnfs')
    assert_file_exists(filepath + '.pred')

    output = cmd.run("{root}/tune_preds.py -c {cs} -f {frm} -g {fp}.eval.grid {fp}.cnfs {fp}.pred" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT, fp=filepath))

    thr, dif = output.split("\t")[:2]
    log.info("grid search found tunning options: t={} d={}".format(thr, dif))

    opts = " -t {} -d {}".format(thr, dif)
    cmd.run("echo '{}' > {}.params".format(opts, filepath))
    return opts

def evaluate_m2(filepath):
    log.info("evaluating on M^2 file: {}.m2".format(filepath))

    assert_file_exists(filepath + '.out')
    assert_file_exists(filepath + '.m2')

    cmd.run("{root}/eval_m2.py {fp}.out {fp}.m2 >> {fp}.eval" \
        .format(root=config.ROOT_DIR, fp=filepath))

def run_m2_grid_search(filepath, nrm_articles=False):
    log.info("running CoNLL grid searching on {0}.pred and {0}.cnfs".format(filepath))

    if result_is_ready('{}.params'.format(filepath)):
        return cmd.run('cat {}.params'.format(filepath))

    assert_file_exists(filepath + '.in')
    assert_file_exists(filepath + '.cnfs')
    assert_file_exists(filepath + '.pred')
    assert_file_exists(filepath + '.m2')

    if nrm_articles:
        options = ' --restore-articles'
    else:
        options = ''

    output = cmd.run("{root}/tune_m2.py {opts} -c {cs} -f {frm} " \
        "-g {fp}.eval.m2.grid -w {fp}.m2gs --m2 {fp}.m2 " \
        "{fp}.in {fp}.cnfs {fp}.pred" \
        .format(root=config.ROOT_DIR, cs=CONFUSION_SET, frm=FORMAT, 
            opts=options, fp=filepath))

    thr, dif = output.split("\t")[:2]
    log.info("M^2 grid search found tunning options: t={} d={}".format(thr, dif))

    opts = " -t {} -d {}".format(thr, dif)
    cmd.run("echo '{}' > {}.params".format(opts, filepath))
    return opts

def null_in_confset():
    return ConfusionSet(CONFUSION_SET).include_null()

def make_m2_parallel(filepath):
    log.debug("making parallel files from M2 file: {}.m2".format(filepath))

    cmd.run("cat {fp}.m2 | perl {root}/make_parallel.perl > {fp}.txt" \
        .format(root=config.SCRIPTS_DIR, fp=filepath))
    cmd.source_side_of_file(filepath + '.txt', filepath + '.in')

def result_is_ready(file):
    if os.path.exists(file):
        if os.stat(file).st_size == 0:
            log.error("result file {} exists but is empty!".format(file))
            exit()
        log.info("step is skipped as result file {} is ready".format(file))
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

    base = parser.add_argument_group("base arguments")
    base.add_argument('-c', '--confusion-set', type=str, 
        help="confusion set as comma-separated list of words")
    base.add_argument("-a", "--algorithm", choices=ALGORITHMS, 
        help="classification algorithm")
    base.add_argument("-m", "--model", type=str, 
        help="classifier model")
    base.add_argument("-d", "--work-dir", default=str(os.getpid()), type=str, 
        help="working directory")

    extra = parser.add_argument_group("extra options")
    extra.add_argument("--ngrams", type=str,
        help="prefix of ngram lists for finding confusion examples")
    extra.add_argument("--feature-set", type=str, choices=FEATURE_SETS.keys(),
        help="feature set")
    extra.add_argument("--nrm-articles", action='store_true',
        help="normalization of indefinite articles")

    parser.add_argument("-t", "--train", type=str, 
        help="train classifier on parallel texts")
    parser.add_argument("-r", "--run", nargs="*", type=str,
        help="run classifier")
    parser.add_argument("-u", "--tune", type=str, 
        help="tune classifier")
    parser.add_argument("-e", "--eval", action='store_true', 
        help="evaluate classifier; file given in --run argument should contain parallel text")
    parser.add_argument("--m2", action='store_true',
        help="assume tuning and running files are in M^2 format")

    opts = parser.add_argument_group("external scripts' arguments")
    opts.add_argument("--cnf-opts", type=str, default='',
        help="options for finding confusions")
    opts.add_argument("--mng-opts", type=str, default='',
        help="options for managing found confusions")
    opts.add_argument("--ext-opts", type=str, default='',
        help="options for feature extraction")
    opts.add_argument("--vec-opts", type=str, default='', 
        help="options for vectorization")
    opts.add_argument("--cls-opts", type=str, default='', 
        help="options for classification algorithm")
    opts.add_argument("--evl-opts", type=str, default='', 
        help="options for evaluation")

    args = parser.parse_args()

    if not args.model:
        args.model = os.path.join(args.work_dir, '{}.model'.format(args.algorithm))

    if args.train:
        assert_file_exists(args.train)
            
    if args.run:
        for run in args.run:
            assert_file_exists(run)
        args = load_setting_file(args)

    if args.tune:
        if args.algorithm in NON_TUNNED_ALGORITHMS:
            raise ArgumentError("algorithm {} can not be tunned!" \
                .format(args.algorithm))

        assert_file_exists(args.tune)
        if not args.eval:
            raise ArgumentError("argument --tune requires --eval")

    if args.eval and not args.run:
        raise ArgumentError("argument --eval requires --run")
    if args.m2 and not args.run:
        raise ArgumentError("argument --m2 requires --run")

    if args.ngrams:
        args.cnf_opts += " -n {}".format(args.ngrams)

    if args.feature_set:
        args.ext_opts += ' --feature-set {}'.format(args.feature_set)
        args.vec_opts += ' --feature-set {}'.format(args.feature_set)

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
                log.debug("loading algorithm: {}".format(val))
                args.algorithm = val
            elif opt == 'set' and not args.confusion_set:
                log.debug("loading confusion set: {}".format(val))
                args.confusion_set = val

            elif opt == 'cnf' and not args.cnf_opts:
                log.debug("loading confusion extraction options: {}".format(val))
                args.cnf_opts = val
            elif opt == 'mng' and not args.mng_opts:
                log.debug("loading confusion managing options: {}".format(val))
                args.mng_opts = val
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
        file.write("mng={}\n".format(args.mng_opts.strip()))
        file.write("ext={}\n".format(args.ext_opts.strip()))
        file.write("vec={}\n".format(args.vec_opts.strip()))
        file.write("cls={}\n".format(args.cls_opts.strip()))
        file.write("evl={}\n".format(args.evl_opts.strip()))


if __name__ == '__main__':
    main()
