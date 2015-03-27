import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from logger import log

from collections import OrderedDict
from features import sum_feature_sets
from confusions import iterate_text_and_confs

from taggers.pos_tagger import StanfordPOSTagger as POSTagger
from taggers.wc_tagger import WordClassTagger as WCTagger


class FeatureExtractor():
    
    def __init__(self):
        self.window = 4
        self.pos_tagger = POSTagger()
        self.wc_tagger = WCTagger()

    def extract_features(self, input_file, cnfs_file, feat_set=None):
        log.info("extracting features from file {} with feature set {}" \
            .format(input_file, feat_set))

        pos_io = open(self.pos_tagger.tag_file(input_file))
        awc_io = open(self.wc_tagger.tag_file(input_file))

        for s, cnfs, text in iterate_text_and_confs(input_file, cnfs_file):
            tokens = text.strip().lower().split()
            pos_tags = pos_io.next().strip().split()
            awc_tags = awc_io.next().strip().split()
            
            for i, j, err, cor, _ in cnfs:
                features = self.extract_features_for_example(i, j, tokens,
                    pos_tags, awc_tags)
                yield (s, i, j, err, cor, features)
        
        pos_io.close()
        awc_io.close()

    def extract_features_for_example(self, i, j, tokens, pos_tags, awc_tags):
        sb_tokens = self.__add_boundaries(tokens)
        sb_pos_tags = self.__add_boundaries(pos_tags)
        sb_awc_tags = self.__add_boundaries(awc_tags)

        ii, jj = i + self.window, j + self.window

        features = OrderedDict()
        features.update(self.__extract_ngrams(ii, jj, sb_tokens, 'w'))
        features.update(self.__extract_ngrams(ii, jj, sb_pos_tags, 'p'))
        features.update(self.__extract_ngrams(ii, jj, sb_awc_tags, 'c'))
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
        pass
    
    def __add_boundaries(self, tokens):
        return ['<s>'] * self.window + tokens + ['</s>'] * self.window
