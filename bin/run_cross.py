#!/usr/bin/python

import os
import sys
import argparse
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from run_geccla import assert_file_exists
from run_geccla import result_is_ready
from run_geccla import ALGORITHMS

import cmd
import config

from logger import log


def main():
    args = parse_user_arguments()

    # Create working directory
    if not os.path.exists(args.work_dir):
        os.makedirs(args.work_dir)
    log.info("working directory: {}".format(args.work_dir))

    # Change error rate in M2 file
    if args.m2 and args.ann_rate:
        log.info("CHANGING ERROR RATE IN M2 DATA FILE")

        annrate_data = os.path.join(args.work_dir, 'data.annrate-{}.m2' \
            .format(args.ann_rate))
        cmd.run("{root}/change_annorate_m2.py -e {er} {data} > {erdata}" \
            .format(root=config.SCRIPTS_DIR, er=args.ann_rate, data=args.data, 
                    erdata=annrate_data))
        args.data = annrate_data

    # Preprare data parts for cross validation
    log.info("SPLITTING DATA FILES INTO {} PARTS".format(args.parts))
    cross_filebase = os.path.join(args.work_dir, 'cross')

    split_data = split_m2_data if args.m2 else split_txt_data
    split_data(args.data, cross_filebase, args.parts)

    eval_files = ' '.join(args.eval)

    # Train cross validation parts and find threshold parameters
    for part in format_parts(args.parts):
        log.info("CROSS VALIDATION PART {}".format(part))

        create_train_files(cross_filebase, part, args.parts, args.more_data, 
            args.shuffle_data)

        cross_file = cross_filebase + '.' + part
        train_cross(cross_file, args.algorithm, args.confusion_set, args.m2, 
            args.geccla)

        log.info("PART {} - EVALUATING ON FILES: {}".format(part, eval_files))
        eval_cross(cross_file, eval_files, args.m2)

    # Find average (tuned) threshold parameter
    log.info("AVERAGING PARAMS")
    param_sets = collect_evaluation_params(cross_filebase, args.parts)
    evl_opts = average_param_sets(param_sets)

    # Train on all data
    log.info("TRAINING ON ALL DATA")
    train_file = os.path.join(args.work_dir, 'train.txt')

    create_train_file(train_file, args.data, args.more_data, args.m2)

    release_dir = os.path.join(args.work_dir, 'release')
    options = " --evl-opts ' {}' {}".format(evl_opts, args.geccla)
    train_geccla(release_dir, train_file, args.algorithm, args.confusion_set, options)

    # Evaluate with tunned threshold parameter
    log.info("EVALUATING ON FILES: {}".format(eval_files))
    run_geccla(release_dir, eval_files, args.m2)
    

def split_m2_data(m2_file, filepath, num_of_parts):
    if result_is_ready('{}.00.txt'.format(filepath)):
        return

    cmd.run("python {root}/split_m2.py -n {n} -p {fp}. -s .m2 {m2}" \
        .format(root=config.SCRIPTS_DIR, n=num_of_parts, fp=filepath, m2=m2_file))

    log.info("preparing text data from M2 files")
    for part in format_parts(num_of_parts):
        cmd.run("cat {fp}.{p}.m2 | perl {root}/make_parallel.perl > {fp}.{p}.txt" \
            .format(root=config.SCRIPTS_DIR, fp=filepath, p=part))

def split_txt_data(txt_file, filepath, num_of_parts):
    if result_is_ready('{}.00.txt'.format(filepath)):
        return

    num_of_lines = cmd.wc(txt_file)
    log.info("total number of lines: {}".format(num_of_sents))

    part_size = math.ceil(num_of_sents / float(num_of_parts))
    log.info("number of lines per part: {}".format(part_size))

    cmd.run("split --lines {size} -d --additional-suffix .txt {txt} {fp}." \
        .format(txt=txt_file, size=part_size, fp=filepath))

def create_train_files(filepath, 
                       part, num_of_parts, 
                       more_data=None, 
                       shuffle=None):

    if result_is_ready('{}.{}.train.txt'.format(filepath, part)):
        return
    
    cat_or_shuf = 'shuf' if shuffle else 'cat'
    if more_data:
        cmd.run("{} {} >> {}.{}.train.txt".format(cat_or_shuf, more_data, 
            filepath, part))

    train_files = ' '.join(["{}.{}.txt".format(filepath, p) 
                            for p in format_parts(num_of_parts) 
                            if p != part])
    cmd.run("{} {} >> {}.{}.train.txt".format(cat_or_shuf, train_files, 
        filepath, part))


def train_cross(crosspath, algorithm, confset, m2, options):
    if result_is_ready('{}/output.train'.format(crosspath)):
        return

    if not os.path.exists(crosspath):
        os.makedirs(crosspath)

    ext = 'm2' if m2 else 'txt'
    m2_opt = '--m2' if m2 else ''

    command = "python {root}/../bin/run_geccla.py {opts}" \
        " --work-dir {cv}" \
        " --confusion-set {cs} --algorithm {alg} --model {cv}/cross.model" \
        " --train {cv}.train.txt" \
        " --run {cv}.{ext} --tune {cv}.{ext} --eval {m2}" \
        " > {cv}/output.train 2>&1" \
        .format(root=config.ROOT_DIR, alg=algorithm, cs=confset, 
                cv=crosspath, ext=ext, opts=options, m2=m2_opt)
    cmd.run(command)

def eval_cross(crosspath, eval_files, m2):
    if result_is_ready('{}/output.eval'.format(crosspath)):
        return

    ext = 'm2' if m2 else 'txt'
    m2_opt = '--m2' if m2 else ''

    command = "python {root}/../bin/run_geccla.py" \
        " --work-dir {cv} --model {cv}/cross.model" \
        " --run {eval} --eval {m2}" \
        " > {cv}/output.eval 2>&1" \
        .format(root=config.ROOT_DIR, cv=crosspath, ext=ext, 
                eval=eval_files, m2=m2_opt)
    cmd.run(command)

def create_train_file(train_file, data, more_data, m2):
    if result_is_ready(train_file):
        return 

    if more_data:
        cmd.run("cat {data} >> {out}".format(data=more_data, out=train_file))

    if m2:
        cmd.run("cat {data} | perl {root}/make_parallel.perl >> {out}" \
            .format(root=config.SCRIPTS_DIR, data=data, out=train_file))
    else:
        cmd.run("cat {data} >> {out}".format(data=data, out=train_file))

def train_geccla(release_dir, train_file, algorithm, confset, options):
    if result_is_ready('{}/output.train'.format(release_dir)):
        return

    os.makedirs(release_dir)
    command = "python {root}/../bin/run_geccla.py {opts}" \
        " --work-dir {rel}" \
        " --confusion-set {cs} --algorithm {alg} --model {rel}/release.model" \
        " --train {train} " \
        " > {rel}/output.train 2>&1" \
        .format(root=config.ROOT_DIR, alg=algorithm, cs=confset, 
                train=train_file, rel=release_dir, opts=options)
    cmd.run(command)

def run_geccla(release_dir, eval_files, m2=False):
    if result_is_ready('{}/output.eval'.format(release_dir)):
        return

    m2_opt = '--m2' if m2 else ''

    command = "python {root}/../bin/run_geccla.py" \
        " --work-dir {rel} --model {rel}/release.model" \
        " --run {eval} --eval {m2}" \
        " > {rel}/output.eval 2>&1" \
        .format(root=config.ROOT_DIR, rel=release_dir, eval=eval_files, m2=m2_opt)
    cmd.run(command)


def collect_evaluation_params(filepath, num_of_parts):
    param_sets = []

    for part in format_parts(num_of_parts):
        param_file = "{fp}.{p}/cross.{p}.params".format(fp=filepath, p=part)
        if not os.path.exists(param_file):
            log.warning("file with tuned params does not exist: {}".format(param_file))
            continue

        with open(param_file) as file:
            fields = file.read().strip().split()
        param_set = (float(fields[1]), float(fields[3]))
        param_sets.append(param_set)

    return param_sets

def average_param_sets(param_sets):
    if not param_sets:
        log.error("no param set found!")
        return ""
    avg_thr = sum(pair[0] for pair in param_sets) / float(len(param_sets))
    avg_dif = sum(pair[1] for pair in param_sets) / float(len(param_sets))
    log.debug("averaged params: t={:.4f} d={:.4f}".format(avg_thr, avg_dif))
    return "-t {} -d {}".format(avg_thr, avg_dif)


def format_parts(size):
    return ["{:0>2d}".format(n) for n in xrange(size)]

def parse_user_arguments():
    parser = argparse.ArgumentParser()

    base = parser.add_argument_group("base arguments")
    base.add_argument('-c', '--confusion-set', type=str, required=True, 
        help="confusion set as comma-separated list of words")
    base.add_argument("-a", "--algorithm", choices=ALGORITHMS, 
        help="classification algorithm")
    base.add_argument("-p", "--parts", type=int, default=4,
        help="number of cross validation parts")
    base.add_argument("--work-dir", type=str, required=True,
        help="working directory")
    base.add_argument("-s", "--shuffle-data", action='store_true',
        help="shuffle data in cross validations")

    geccla = parser.add_argument_group("geccla arguments")
    geccla.add_argument('--geccla', type=str,
        help="extra arguments for run_geccla.py script")

    parser.add_argument("-d", "--data", type=str, required=True,
        help="data for training and tuning classifier")
    parser.add_argument("-m", "--more-data", type=str,
        help="more data for training classifier")
    parser.add_argument("-e", "--eval", nargs="*", type=str,
        help="evaluate classifier")
    parser.add_argument("--m2", action='store_true',
        help="assume --data and --eval are files in M2 format")
    parser.add_argument("--ann-rate", type=float,
        help="change error rate in M2 file")

    args = parser.parse_args()

    assert_file_exists(args.data)
    if args.more_data:
        assert_file_exists(args.more_data)
    for eval in args.eval:
        assert_file_exists(eval)

    log.debug(args)
    return args

if __name__ == '__main__':
    main()
