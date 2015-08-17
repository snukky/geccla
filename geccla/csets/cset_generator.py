import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import csets

from logger import log


class CSetGenerator():

    def __init__(self, editstats):
        self.editstats = editstats
        
    def generate_by_coverage(self, req_cover=0.85,
                                   max_iters=1000,
                                   seeds=[],
                                   disjoint=True,
                                   reject_sparse=0.5):
        log.info("generating confusion sets")

        if not seeds:
            seeds = [wrd for wrd, _ in csets.sort_dict(self.editstats.freqs)]
        
        used_words = set()
        conf_sets = []

        for iter, err in enumerate(seeds):
            if iter == max_iters:
                break
            if disjoint and err in used_words:
                continue
            if err not in self.editstats.edits:
                continue

            conf_set = set([err])
            used_words.add(err)
            counter = 0

            cors = self.editstats.edits[err]

            log.debug("word: {}".format(err))
            log.debug("cors: {}".format(csets.readable_dict(cors)))

            for cor, frac in csets.incfrac_dict(cors):
                counter += 1

                if disjoint and cor in used_words:
                    continue

                conf_set.add(cor)
                used_words.add(cor)

                if frac > req_cover:
                    break

            log.debug("cset: {}".format(', '.join(conf_set)))

            if len(conf_set) < 2:
                log.debug("too less words in confusion set!")
                used_words -= set(conf_set)
                continue

            if disjoint and reject_sparse:
                sparsity = len(conf_set) / float(counter)
                if sparsity < reject_sparse:
                    log.debug("too many words are rejected! ({:.2f})" \
                        .format(sparsity))
                    used_words -= set(conf_set)
                    continue

            log.debug("used: {}".format('|'.join(used_words)))
            conf_sets.append(conf_set)

        return conf_sets

