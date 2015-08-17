#!/usr/bin/python

import os
import sys
import argparse
import re

from joblib import Parallel, delayed

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                                '../geccla')))

from run_geccla import result_is_ready

import cmd
import config

from logger import log

JOBS = 4
MORE_DATA_LIMIT = 10000


def main():
    args = parse_user_args()

    if not os.path.exists(args.work_dir):
        os.makedirs(args.work_dir)
    log.info("working directory: {}".format(args.work_dir))
    
    log.info("loading confusion sets from file: {}".format(args.csets))
    with open(args.csets, 'r') as csets_io:
        csets = [line.strip().split()[-1] for line in csets_io][:args.expts]

    log.info("number of experiments: {}".format(len(csets)))

    eval_inits = initialize_eval(args.work_dir, args.eval)

    for cset in csets:
        log.info("running experiment for confusion set: {}".format(cset))
        work_dir = os.path.join(args.work_dir, re.sub(r"[^a-z,]", "", cset))
        
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)
        else:
            #if result_is_ready():
                #continue
            #else:
                ## TODO: rm dir and create new dir
            continue
        
        prepare_data(cset, work_dir, args)
        prepare_more_data(cset, work_dir, args)

        eval_files = prepare_eval(cset, work_dir, eval_inits)

        log.info("running GECcla")
        cmd.run("python {root}/../bin/run_cross.py --work-dir {dir}" \
            " --confusion-set {cset} --algorithm liblinear" \
            " --data {dir}/data.m2 --eval {eval} --m2" \
            " --more-data {dir}/more_data.txt --shuffle-data" \
            " --geccla ' --feature-set genawc+src'" \
            .format(root=config.ROOT_DIR, dir=work_dir, cset=cset,
                    eval=' '.join(eval_files)))
        
    log.info("evaluate on all confusion sets")

    out_files = {eval: [] for eval in args.eval}
    in_files = {}

    for cset in csets:
        work_dir = os.path.join(args.work_dir, re.sub(r"[^a-z,]", "", cset))

        for eval in args.eval:
            eval_path = cmd.base_filepath(work_dir + '/release', eval)
            out_files[eval].append(eval_path + '.out')
            if eval not in in_files:
                in_files[eval] = eval_path + '.in'

    for eval in args.eval:
        out = args.work_dir + '/' + cmd.base_filename(eval) + '.out'
        evl = args.work_dir + '/' + cmd.base_filename(eval) + '.eval'

        files = ' '.join(out_files[eval])

        cmd.run("python {root}/../scripts/join_cors.py {files} > {out}" \
            .format(root=config.ROOT_DIR, files=files, out=out))
        cmd.run("{root}/eval_m2.py {out} {m2} > {evl}" \
            .format(root=config.ROOT_DIR, out=out, m2=eval, evl=evl))

        cmd.wdiff(in_files[eval], out)


def initialize_eval(work_dir, m2_files):
    eval_inits = {}

    for m2_file in m2_files:
        log.info("creating .err/.cor files for M2 file: {}".format(m2_file))

        m2_base = cmd.base_filepath(work_dir, m2_file)
        m2_name = cmd.base_filename(m2_file)
        eval_inits[m2_name] = []

        num_of_anns = __count_annotators(m2_file)

        for num in range(num_of_anns):
            cmd.run("cat {m2} | {root}/../scripts/make_parallel.perl" \
                " --annotator {ann} > {base}.{ann}.txt" \
                .format(root=config.ROOT_DIR, m2=m2_file, ann=num, base=m2_base))

            if not os.path.exists("{}.err".format(m2_base)):
                cmd.run("cut -f1 {base}.{ann}.txt > {base}.err" \
                    .format(base=m2_base, ann=num))
                eval_inits[m2_name].append("{}.err".format(m2_base))

            cmd.run("cut -f2 {base}.{ann}.txt > {base}.{ann}.cor" \
                .format(base=m2_base, ann=num))
            eval_inits[m2_name].append("{}.{}.cor".format(m2_base, num))
    
    return eval_inits

def __count_annotators(m2_file):
    num = cmd.run("cat {} | grep '^A ' | sed -r " \
        "'s/.*\\|\\|\\|([0-9]+)$/\\1/' | sort -u | wc -l".format(m2_file))
    return int(num.strip())

def prepare_data(cset, work_dir, args):
    log.info("changing error rate in cross validation data")

    cmd.run("cat {input} | {root}/../scripts/make_parallel.perl" \
        " > {dir}/data.raw.txt" \
        .format(root=config.ROOT_DIR, input=args.data, dir=work_dir))
    
    cmd.cut(work_dir + '/data.raw.txt', work_dir + '/data.raw.err', col=1)
    cmd.cut(work_dir + '/data.raw.txt', work_dir + '/data.raw.cor', col=2)

    cmd.run("python {root}/../scripts/format_m2.py -c {cset}" \
        " --greedy --no-spaces" \
        " {dir}/data.raw.err {dir}/data.raw.cor" \
        " > {dir}/data.raw.m2" \
        .format(root=config.ROOT_DIR, cset=cset, dir=work_dir))

    # FIXME: error rates should be calculated from development data!
    cmd.run("python {root}/../scripts/change_annorate_m2.py" \
        " -e {rate} --shuffle {dir}/data.raw.m2" \
        " > {dir}/data.m2 2> {dir}/data.stderr" \
            .format(root=config.ROOT_DIR, rate=args.error_rate, dir=work_dir))

    if not args.debug:
        os.remove(work_dir + '/data.raw.txt')
        os.remove(work_dir + '/data.raw.err')
        os.remove(work_dir + '/data.raw.cor')
        os.remove(work_dir + '/data.raw.m2')
        os.remove(work_dir + '/data.stderr')

def prepare_more_data(cset, work_dir, args):
    log.info("changing error rate in training data")

    cmd.run("python {root}/../scripts/change_txt.py --shuffle" \
        " -c {cset} -e {rate} {input} | head -n {limit}" \
        " > {dir}/more_data.txt 2> {dir}/more_data.stderr" \
        .format(root=config.ROOT_DIR, 
                input=args.more_data, dir=work_dir, 
                cset=cset, rate=args.error_rate,
                limit=MORE_DATA_LIMIT))

    if not args.debug:
        os.remove(work_dir + '/more_data.stderr')
        
def prepare_eval(cset, work_dir, eval_inits):
    log.info("selecting errors by confusion set: {}".format(cset))
    eval_files = []

    for base, files in eval_inits.iteritems():
        eval_file = work_dir + '/' + base + '.m2'

        cmd.run("python {root}/../scripts/format_m2.py" \
            " -c {cset} -t cset --greedy --no-spaces {files}" \
            " > {eval}" \
            .format(root=config.ROOT_DIR, cset=cset, files=' '.join(files),
                    eval=eval_file))

        eval_files.append(eval_file)

    return eval_files


def parse_user_args():
    parser = argparse.ArgumentParser()

    base = parser.add_argument_group("base arguments")
    base.add_argument("-c", "--csets", required=True)
    base.add_argument("--error-rate", type=float, default=0.15)

    data = parser.add_argument_group("data arguments")
    data.add_argument("--data", required=True)
    data.add_argument("--more-data", required=True)
    data.add_argument("--eval", nargs='+')

    parser.add_argument("--work-dir", type=str, default='.')
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--expts", type=int, default=2)
    parser.add_argument("--debug", action='store_true')

    return parser.parse_args()

if __name__ == '__main__':
    main()
