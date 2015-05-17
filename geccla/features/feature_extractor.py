import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from logger import log

from collections import OrderedDict
from confusions import iterate_text_and_confs
from features import FEATURE_SETS 

from taggers.pos_tagger import StanfordPOSTagger as POSTagger
from taggers.wc_tagger import WordClassTagger as WCTagger

import itertools


class FeatureExtractor():
    
    def __init__(self, window=5, feat_set=None, awc_dict=None):
        self.window = window
        self.feat_set = feat_set or 'base'

        self.pos_tagger = None
        if self.__active_feats('pB1A1', 'mwpB1A1'):
            self.pos_tagger = POSTagger()

        self.wc_tagger = None
        if self.__active_feats('cB1A1', 'mwcB1A1'):
            self.wc_tagger = WCTagger(awc_dict)

    def extract_features(self, input_file, cnfs_file):
        log.info("extracting features from file {} with feature set {}" \
            .format(input_file, self.feat_set))

        pos_io = open(self.pos_tagger.tag_file(input_file)) if self.pos_tagger else None
        awc_io = open(self.wc_tagger.tag_file(input_file)) if self.wc_tagger else None

        for s, cnfs, text in iterate_text_and_confs(input_file, cnfs_file):
            tokens = text.strip().lower().split()

            pos_tags = pos_io.next().strip().split() if pos_io else None
            awc_tags = awc_io.next().strip().split() if awc_io else None
            
            for i, j, err, cor, _ in cnfs:
                features = self.extract_features_for_example(i, j, tokens,
                    pos_tags, awc_tags)
                yield (s, i, j, err, cor, features)

        if pos_io:
            pos_io.close()
        if awc_io:
            awc_io.close()

    def extract_features_for_example(self, i, j, tokens, pos_tags, awc_tags):
        sb_tokens = self.__add_boundaries(tokens)
        sb_pos_tags = self.__add_boundaries(pos_tags) if pos_tags else None
        sb_awc_tags = self.__add_boundaries(awc_tags) if awc_tags else None

        ii, jj = i + self.window, j + self.window

        features = OrderedDict()

        if self.__active_feats('src'):
            features['src'] = ' '.join(tokens[i:j]).lower()

        if self.__active_feats('wB1A1'):
            features.update(self.__extract_ngrams(ii, jj, sb_tokens, 'w'))
        if self.__active_feats('pB1A1'):
            features.update(self.__extract_ngrams(ii, jj, sb_pos_tags, 'p'))
        if self.__active_feats('cB1A1'):
            features.update(self.__extract_ngrams(ii, jj, sb_awc_tags, 'c'))

        if self.__active_feats('mwpB1A1'):
            features.update(self.__extract_mixed_ngrams(ii, jj, sb_tokens, sb_pos_tags, 'mwp'))
        if self.__active_feats('mwcB1A1'):
            features.update(self.__extract_mixed_ngrams(ii, jj, sb_tokens, sb_awc_tags, 'mwc'))

        return features
        
    def __extract_ngrams(self, i, j, tokens, prefix):
        ngrams = {}
        for n in xrange(2, self.window + 2):
            for b, a in zip(range(n), reversed(range(n))):
                name = "{}B{}A{}".format(prefix, b, a)
                ngrams[name] = '_'.join(tokens[i-b:i] + tokens[j:j+a])
        return ngrams

    def __extract_joined_ngrams(self, i, j, tokens, tags, prefix):
        pass

    def __extract_mixed_ngrams(self, i, j, tokens, tags, prefix):
        ngrams = {}
        for n in xrange(3, self.window + 2):
            for b, a in zip(xrange(n), reversed(xrange(n))):
                #log.debug("  b: {} a: {}".format(b, a))
                #log.debug("  i-b:i={}:{} toks: {} tags: {}".format(i-b, i, tokens[i-b:i], tags[i-b:i]))
                #log.debug("  j:j+a={}:{} toks: {} tags: {}".format(j, j+a, tokens[j:j+a], tags[j:j+a]))

                _toks = tokens[i-b:i] + tokens[j:j+a]
                _tags = tags[i-b:i] + tags[j:j+a]
                #log.debug("  toks: {} tags: {}".format(_toks, _tags))

                name_prefix = "{}B{}A{}".format(prefix, b, a)
                
                for m in xrange(1, n-1):
                    for idxes in itertools.combinations(xrange(n-1), m):
                        if any(idx+i-b < self.window for idx in idxes):
                            continue
                        if any(idx+i-b > (len(tokens) - self.window - 1) for idx in idxes):
                            continue

                        name = name_prefix + '_' + ''.join(map(str, idxes))
                        ngram = [_tags[k] if k in idxes else _toks[k] 
                                 for k in xrange(len(_toks))]
                        ngrams[name] = '_'.join(ngram)

                        #log.debug("    {} = {}".format(subname, ' '.join(ngram)))
        return ngrams
    
    def __add_boundaries(self, tokens):
        return ['<s>'] * self.window + tokens + ['</s>'] * self.window

    def __active_feats(self, *feats):
        return any(feat in FEATURE_SETS[self.feat_set] for feat in list(feats))
