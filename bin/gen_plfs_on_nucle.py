#!/usr/bin/python

import os
import sys
import argparse
import shutil
import re


GECCLA_DIR = "/home/romang/scripts/geccla"

CROSS_PARTS = ['00', '01', '02', '03']
RELEASE_PART = 'release'
CROSS_PARTS_WITH_RELEASE = CROSS_PARTS + [RELEASE_PART]

GECCLA_CROSSES = None


def main():
    args = parse_user_args()

    if not os.path.exists(args.work_dir):
        debug('Create working directory: {}'.format(args.work_dir))
        os.makedirs(args.work_dir)

    filebase = os.path.join(args.work_dir, 'file')

    global GECCLA_CROSSES
    GECCLA_CROSSES = read_geccla_cross_files(filebase, args.model)

    create_geccla_cross_files(filebase, args.nucle)
    run_geccla_crosses(filebase, args.model, args.plf, args.threshold)
    recreate_nucle_cross_files(filebase, args.nucle, args.suffix)

    if args.clean:
        debug("Remove working dir")
        shutil.rmtree(args.work_dir)
    

def read_geccla_cross_files(filebase, model):
    debug("Read cross files from GECcla directory")

    crosses = []
    for part in CROSS_PARTS:
        with open(os.path.join(model, 'cross.{}.txt'.format(part))) as cross_io:
            err_sents = [line.split("\t")[0] for line in cross_io.readlines()]
            sent_signs = [__sentence_fingerprint(sent) for sent in err_sents]
            crosses.append( set(sent_signs) )

    return crosses


def create_geccla_cross_files(filebase, nucle_files):
    debug("Create cross files for GECcla classifiers")

    output_io = open(filebase + '.info', 'w')
    cross_files = { part: open('{}.geccla.{}.err'.format(filebase, part), 'w') 
                    for part in CROSS_PARTS_WITH_RELEASE }

    for idx, nucle_file in enumerate(nucle_files):
        with open(nucle_file, 'r') as nucle_io:
            for sent in nucle_io:
                cross = __find_geccla_model(sent)
                output_io.write("{}\t{}\n".format(idx, cross))
                cross_files[cross].write(sent)

    output_io.close()
    for _, file in cross_files.iteritems():
        file.close()

def run_geccla_crosses(filebase, model_dir, output_format='plf-best', 
                                            threshold=None):
    for part in CROSS_PARTS_WITH_RELEASE:
        if part == RELEASE_PART:
            model = os.path.join(model_dir, 'release/release.model')
        else:
            model = os.path.join(model_dir, 'cross.{}/cross.model'.format(part))
        
        geccla = "python {g}/bin/run_geccla.py --work-dir {f}.{p}" \
            " --model {m} --run {f}.geccla.{p}.err" \
            " --output-file {f}.geccla.{p}.out --output-format {o}" \
            " > {f}.geccla.{p}.stderr 2>&1" \
            .format(g=GECCLA_DIR, m=model, f=filebase, p=part, o=output_format)

        if threshold:
            geccla += " --evl-opts ' -t {}'".format(threshold)

        debug("Run GECcla model: {}".format(part))
        run_cmd(geccla)

def recreate_nucle_cross_files(filebase, nucle_files, suffix):
    debug("Create output files for input NUCLE parts")

    output_files = [ open(file + suffix, 'w') for file in nucle_files ]
    cross_files = { part: open('{}.geccla.{}.out'.format(filebase, part)) 
                    for part in CROSS_PARTS_WITH_RELEASE }

    with open(filebase + '.info') as input_io:
        for line in input_io:
            idx, cross = line.split("\t")
            cor_sent = cross_files[cross.strip()].next()

            output_files[int(idx)].write(cor_sent)
    
    for file in output_files:
        file.close()
    for _, file in cross_files.iteritems():
        file.close()


def __find_geccla_model(text):
    sign = __sentence_fingerprint(text)
    for idx, cross_signs in enumerate(GECCLA_CROSSES):
        if sign in cross_signs:
            return '{:0>2d}'.format(idx)
    return RELEASE_PART

def __sentence_fingerprint(text):
    return re.sub(r'[^a-z0-9,.()]+', '', text.lower())


def run_cmd(cmd):
    debug(cmd)
    os.popen(cmd)

def debug(msg):
    print >> sys.stderr, msg

def parse_user_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("nucle", nargs="+",
        help="NUCLE cross file(s) to correct")
    parser.add_argument("-m", "--model", required=True, 
        help="directory of GECcla model")
    #parser.add_argument("-n", "--geccla-nucle", type=str,
        #help="NUCLE subcorpus used to train GECcla model")

    parser.add_argument("-t", "--threshold", type=float)
    parser.add_argument("-d", "--work-dir", default=str(os.getpid()))
    parser.add_argument("-f", "--plf", type=str, default="plf-best")
    parser.add_argument("-s", "--suffix", type=str, default=".plf")
    parser.add_argument("-c", "--clean", action='store_true')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    main()
