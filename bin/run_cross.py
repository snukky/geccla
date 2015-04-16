#!/usr/bin/python

import os
import sys
import argparse
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../geccla')))

from run_geccla import assert_file_exists
from run_geccla import ALGORITHMS

import cmd
import config

from logger import log


def main():
    args = parse_user_arguments()

    if not os.path.exists(args.work_dir):
        os.makedirs(args.work_dir)
    log.info("working directory: {}".format(args.work_dir))

    log.info("SPLITTING DATA FILES INTO {} PARTS".format(args.parts))
    cross_filebase = os.path.join(args.work_dir, 'cross')

    split_data = split_m2_data if args.m2 else split_txt_data
    split_data(args.data, cross_filebase, args.parts)

    for part in format_parts(args.parts):
        log.info("CROSS VALIDATION PART {}".format(part))

        create_train_files(cross_filebase, part, args.parts, args.more_data)

        cross_file = cross_filebase + '.' + part
        train_cross(cross_file, args.algorithm, args.confusion_set, args.m2)

        for eval in args.eval:
            log.info("PART {} - EVALUATING ON FILE: {}".format(part, eval))
            eval_cross(cross_file, eval, args.m2)

    log.info("AVERAGING PARAMS")
    param_sets = collect_evaluation_params(cross_filebase, args.parts)
    evl_opts = average_param_sets(param_sets)

    log.info("TRAINING ON ALL DATA")
    train_file = os.path.join(args.work_dir, 'train.txt')

    if args.m2:
        cmd.run("cat {data} | perl {root}/make_parallel.perl > {out}" \
            .format(root=config.SCRIPTS_DIR, data=args.data, out=train_file))
    else:
        cmd.run("cat {data} > {out}".format(data=args.data, out=train_file))
    if args.more_data:
        cmd.run("cat {data} >> {out}".format(data=args.more_data, out=train_file))

    release_dir = os.path.join(args.work_dir, 'release')
    train_geccla(release_dir, train_file, args.algorithm, args.confusion_set, evl_opts)

    for eval in args.eval:
        log.info("EVALUATING FILE: {}".format(eval))
        run_geccla(release_dir, eval, args.m2)
    

def split_m2_data(m2_file, filepath, num_of_parts):
    parts = format_parts(num_of_parts)
    log.info("part numbers: {}".format(' '.join(parts)))

    num_of_sents = int(cmd.run("grep -c '^S ' {}".format(m2_file)))
    log.info("total number of sentences in data: {}".format(num_of_sents))

    part_size = math.ceil(num_of_sents / float(num_of_parts))
    log.info("number of sentences in one part: {}".format(part_size))

    log.info("splitting M2 file {}".format(m2_file))
    part_io = open('{}.{}.m2'.format(filepath, parts.pop(0)), 'w+')
    s = 0
    with open(m2_file) as m2_io:
        for line in m2_io:
            if line.startswith("S "):
                s += 1
            part_io.write(line)
            if s >= part_size and line.strip() == '':
                part_io.close()
                part_io = open('{}.{}.m2'.format(filepath, parts.pop(0)), 'w+')
                s = 0
    part_io.close()

    log.info("preparing text data from M2 files")
    for part in format_parts(num_of_parts):
        cmd.run("cat {fp}.{p}.m2 | perl {root}/make_parallel.perl > {fp}.{p}.txt" \
            .format(root=config.SCRIPTS_DIR, fp=filepath, p=part))

def split_txt_data(txt_file, filepath, num_of_parts):
    parts = format_parts(num_of_parts)
    log.info("part numbers: {}".format(' '.join(parts)))

    num_of_sents = cmd.wc(txt_file)
    log.info("total number of sentences in data: {}".format(num_of_sents))

    part_size = math.ceil(num_of_sents / float(num_of_parts))
    log.info("number of sentences in one part: {}".format(part_size))

    log.info("splitting text file {}".format(txt_file))
    part_io = open('{}.{}.txt'.format(filepath, parts.pop(0)), 'w+')
    s = 0
    with open(txt_file) as txt_io:
        for line in txt_io:
            s += 1
            part_io.write(line)
            if s >= part_size:
                part_io.close()
                part_io = open('{}.{}.txt'.format(filepath, parts.pop(0)), 'w+')
                s = 0
    part_io.close()

def create_train_files(filepath, part, num_of_parts, more_data=None):
    train_files = ' '.join(["{}.{}.txt".format(filepath, p) 
                            for p in format_parts(num_of_parts) 
                            if p != part])

    cmd.run("cat {} > {}.{}.train.txt".format(train_files, filepath, part))
    if more_data:
        cmd.run("cat {} >> {}.{}.train.txt".format(more_data, filepath, part))


def train_cross(crosspath, algorithm, confset, m2=False):
    if not os.path.exists(crosspath):
        os.makedirs(crosspath)

    ext = 'm2' if m2 else 'txt'
    command = "python {root}/../bin/run_geccla.py" \
        " --work-dir {cv}" \
        " --confusion-set {cs} --algorithm {alg} --model {cv}/cross.model" \
        " --train {cv}.train.txt" \
        " --run {cv}.{ext} --tune {cv}.{ext} --eval" \
        " > {cv}/output.train 2>&1" \
        .format(root=config.ROOT_DIR, alg=algorithm, cs=confset, 
                cv=crosspath, ext=ext)
    if m2:
        command += " --m2"
    cmd.run(command)

def eval_cross(crosspath, eval_file, m2=False):
    ext = 'm2' if m2 else 'txt'
    command = "python {root}/../bin/run_geccla.py" \
        " --work-dir {cv} --model {cv}/cross.model" \
        " --run {eval} --eval" \
        " > {cv}/output.eval.{num} 2>&1" \
        .format(root=config.ROOT_DIR, cv=crosspath, ext=ext, 
                eval=eval_file, num=cmd.base_filename(eval_file))
    if m2:
        command += " --m2"
    cmd.run(command)

def train_geccla(release_dir, train_file, algorithm, confset, evl_opts):
    os.makedirs(release_dir)
    command = "python {root}/../bin/run_geccla.py" \
        " --work-dir {rel}" \
        " --confusion-set {cs} --algorithm {alg} --model {rel}/release.model" \
        " --train {train} --evl-opts ' {opts}'" \
        " > {rel}/output.train 2>&1" \
        .format(root=config.ROOT_DIR, alg=algorithm, cs=confset, 
                train=train_file, rel=release_dir, opts=evl_opts)
    cmd.run(command)

def run_geccla(release_dir, eval_file, m2=False):
    command = "python {root}/../bin/run_geccla.py" \
        " --work-dir {rel} --model {rel}/release.model" \
        " --run {eval} --eval" \
        " > {rel}/output.eval.{num} 2>&1" \
        .format(root=config.ROOT_DIR, rel=release_dir, eval=eval_file,
                num=cmd.base_filename(eval_file))
    if m2:
        command += " --m2"
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
    log.debug("averaged params: t={:.4f} d={:.4f}".format(avg.thr, avg.dif))
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

    parser.add_argument("-d", "--data", type=str, required=True,
        help="data for training and tuning classifier")
    parser.add_argument("-m", "--more-data", type=str,
        help="more data for training classifier")
    parser.add_argument("-e", "--eval", nargs="*", type=str,
        help="evaluate classifier")
    parser.add_argument("--m2", action='store_true',
        help="assume --data and --eval are files in M2 format")

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
