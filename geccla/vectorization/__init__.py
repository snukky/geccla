import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import cmd

from features import FEATURE_SETS
from logger import log


def create_freq_file(cnfs_file, freq_file):
    log.info("counting frequencies...")
    cmd.run("cat {} | sed 's/|||/\\t/g' | cut -f5 | tr ' ' '\\n' "
        "| sort | uniq -c | sort -nr > {}".format(cnfs_file, freq_file))

def create_feat_file(freq_file, feat_set, feat_file, 
                     min_feat_count=5, max_vec_size=500000):
    log.info("truncating features...")
    log.info("minimum count for single feature: {}" \
        .format(min_feat_count))

    line_num = cmd.run("cat {} | grep -Pn ' +{} .*' | tr ':' '\\t' | cut -f1 | tail -1" \
        .format(freq_file, min_feat_count)).strip()

    log.info("building feature vector...")

    log.info("selected feature set: {}".format(feat_set))
    log.info("feature predicates: {}".format(', '.join(FEATURE_SETS[feat_set])))
    log.info("total number of predicates: {}".format(len(FEATURE_SETS[feat_set])))

    regex = '^(' + '|'.join(FEATURE_SETS[feat_set]) + ')(_[0-9]+)?='
    cmd.run("head -n {} {} | sed -r 's/ *[0-9]+ (.*)/\\1/' | grep -P '{}' > {}" \
        .format(line_num, freq_file, regex, feat_file))

    log.info("limit for features: {}".format(max_vec_size))
    log.info("active features: {}".format(cmd.wc(feat_file)))

    feat_preds = cmd.run("cat {} | sed -r 's/(.*)=.*/\\1/' | sort -u" \
        .format(feat_file)).strip().split("\n")

    log.info("active feature predicates: {}".format(', '.join(feat_preds)))
    log.info("total number of active predicates: {}".format(len(feat_preds)))

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
