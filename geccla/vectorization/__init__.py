import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import cmd

from features import FEATURE_SETS
from logger import log


def create_freq_file(cnfs_file, freq_file):
    log.info("counting frequencies...")
    cmd.run("cat {0} | sed 's/|||/\\t/g' | cut -f5 | tr ' ' '\\n' > {1}.unit".format(cnfs_file, freq_file))
    cmd.run("sort -S 10G --parallel 8 {0}.unit > {0}.unit.sort".format(freq_file))
    cmd.run("cat {0}.unit.sort | uniq -cd | sort -nr -S 10G --parallel 8 > {0}".format(freq_file))

def create_feat_file(freq_file, feat_set, feat_file, 
                     min_feat_count=5, max_vec_size=2000000):
    log.info("truncating features...")
    log.info("minimum count for single feature: {}" \
        .format(min_feat_count))

    line_num = cmd.run("cat {} | grep -Pn ' +{} .*' | tr ':' '\\t' | cut -f1 | tail -1" \
        .format(freq_file, min_feat_count)).strip()

    log.info("building feature vector...")
    log.info("selected feature set: {}".format(feat_set))

    all_feat_preds = FEATURE_SETS[feat_set]

    log.info("feature predicates in selected feature set: {}".format(', '.join(all_feat_preds)))
    log.info("total number of predicates in feature set: {}".format(len(all_feat_preds)))

    regex = '^(' + '|'.join(FEATURE_SETS[feat_set]) + ')(_[0-9]+)?='
    cmd.run("head -n {} {} | sed -r 's/ *[0-9]+ (.*)/\\1/' | grep -P '{}' > {}" \
        .format(line_num, freq_file, regex, feat_file))

    log.info("limit for features: {}".format(max_vec_size))
    log.info("active features: {}".format(cmd.wc(feat_file)))

    feat_preds = cmd.run("cat {} | tr '=' '\\t' | cut -f1 | sort -u -S 10G --parallel 8" \
        .format(feat_file)).strip().split("\n")

    log.info("active feature predicates: {}".format(', '.join(feat_preds)))
    log.info("total number of active predicates: {}".format(len(feat_preds)))

    miss_feat_preds = [fp for fp in all_feat_preds if fp not in feat_preds]

    log.info("nonactive feature predicates: {}".format(', '.join(miss_feat_preds)))
    log.info("total number of nonactive predicates: {}".format(len(miss_feat_preds)))

    cmd.run("head -n {} {} | sed -r 's/ *[0-9]+ (.*)/\\1/' | grep -vP '{}' " \
        " | tr '=' '\\t' | cut -f1 | sort -u -S 1G --parallel 8 > {}" \
        .format(line_num, freq_file, regex, feat_file + '.skip'))

    skip_feat_preds = []
    with open(feat_file + '.skip') as skip_io:
        skip_feat_preds = [line.strip() for line in skip_io.readlines()]

    log.info("skipped feature predicates: {}".format(', '.join(skip_feat_preds)))
    log.info("total number of skipped predicates: {}".format(len(skip_feat_preds)))


def strong_evidence(conf_set, cnfs_file, freq_file, evid_file):
    freq_io = open(freq_file)
    evid_io = open(evid_file, 'w+')

    i = 0
    for line in freq_io:
        feat = line.strip().split()[-1]
        counts = {}

        for word in conf_set:
            count = cmd.run(r'egrep -ci "\|{word}\|\|\|[^|]*{feat}\b" {file}' \
                .format(word=word, feat=feat, file=cnfs_file))
            counts[word] = int(count)
        
        evidence = max(counts, key=lambda w: counts[w]) / float(sum(counts.values()))
        evid_io.write("{}\t{}\t{}\n".format(feat, counts, evidence))

        i += 1
        if i > 10:
            break
    
    freq_io.close()
    evid_io.close()
