import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from features import FEATURE_SETS
from features import sum_feature_sets, compose_feature_set
from confusions import iterate_text_and_confs

from taggers.pos_helper import *
from taggers.lbj_chunker import LBJChunker

from logger import log
import config


class ArtOrDetFeatures():

    SENTENTIAL_ADVERBS  = 'already recently now later then however even possibly indeed often just really also'.split()

    def __init__(self, wc_dic=None):
        self.mass_nouns = self.__load_list(config.FILES.MASS_NOUNS)
        self.count_nouns = self.__load_list(config.FILES.COUNTABLE_NOUNS)

        self.prev_sentence = set()
        self.chunker = LBJChunker()
        
    def __load_list(self, file):
        items = []
        with open(file) as io:
            items = [line.strip().lower() for line in io.readlines()]
        return set(items)
    
    def extract_features(self, input_file, cnfs_file, feat_set=None):
        log.info("extracting features from file {} with feature set {}" \
            .format(input_file, feat_set))

        all_chunks = self.chunker.chunks_and_pos_tags(input_file)
        warns = 0

        for s, cnfs, text in iterate_text_and_confs(input_file, cnfs_file):
            tokens = text.strip().lower().split()
            chunks = all_chunks.next()

            words = [w.lower() for w in chunks.words]
            if len(words) != len(tokens):
                log.warn("chunker could change tokenization:\nwords : {}\nchunks: {}" \
                    .format(' '.join(tokens), ' '.join(words)))
                warns += 1

            for i, j, err, cor, _ in cnfs:
                features = self.extract_features_for_example(i, j, err, tokens, chunks, words)
                yield (s, i, j, err, cor, features)

        if warns > 0:
             log.warn("number of sentences with changed tokenization: {}" \
                .format(warns))

    def extract_features_for_example(self, i, j, word, tokens, chunks, words=None):
        if words is None:
            words = [w.lower() for w in chunks.words]
        poses = chunks.pos

        features = {}

        idx = i
        # index of word preceding the article
        i = i - 1
        # index of word following the article
        j = i if word == '<null>' else i + 1

        wB = words[i] if i >= 0 else '<s>'
        w2B = words[i-1] if i >= 1 else '<s>'
        w3B = words[i-2] if i >= 2 else '<s>'
        w4B = words[i-3] if i >= 3 else '<s>'
        wA = words[j] if j <= len(words) - 1 else '</s>'
        w2A = words[j+1] if j <= len(words) - 2 else '</s>'
        w3A = words[j+2] if j <= len(words) - 3 else '</s>'
        w4A = words[j+3] if j <= len(words) - 4 else '</s>'
        
        pB = poses[i] if i >= 0 else '<S>'
        p2B = poses[i-1] if i >= 1 else '<S>'
        p3B = poses[i-2] if i >= 2 else '<S>'
        pA = poses[j] if j <= len(poses) - 1 else '</S>'
        p2A = poses[j+1] if j <= len(poses) - 2 else '</S>'
        p3A = poses[j+2] if j <= len(poses) - 3 else '</S>'

        chunk = chunks.get_chunk_by_word_idx(idx)

        # source and label articles
        features['src'] = word

        # word n-grams features
        features['wB']  = wB
        features['w2B'] = w2B
        features['w3B'] = w3B 
        features['wA']  = wA
        features['w2A'] = w2A
        features['w3A'] = w3A

        features['wBwA'] = wB+' '+wA
        features['w2BwB'] = w2B+' '+wB
        features['wAw2A'] = wA+' '+w2A
        features['w3Bw2BwB'] = w3B+' '+w2B+' '+wB
        features['w2BwBwA'] = w2B+' '+wB+' '+wA
        features['wBwAw2A'] = wB+' '+wA+' '+w2A
        features['wAw2Aw3A'] = wA+' '+w2A+' '+w3A
        features['w4Bw3Bw2BwB'] = w4B+' '+w3B+' '+w2B+' '+wB
        features['w3Bw2BwBwA'] = w3B+' '+w2B+' '+wB+' '+wA
        features['w2BwBwAw2A'] = w2B+' '+wB+' '+wA+' '+w2A
        features['wBwAw2Aw3A'] = wB+' '+wA+' '+w2A+' '+w3A
        features['wAw2Aw3w4A'] = wA+' '+w2A+' '+w3A+' '+w4A

        # POS features
        features['pB'] = pB
        features['p2B'] = p2B
        features['p3B'] = p3B
        features['pA'] = pA
        features['p2A'] = p2A
        features['p3A'] = p3A

        features['pBpA'] = pB+' '+pA
        features['p2BpB'] = p2B+' '+pB
        features['pAp2A'] = pA+' '+p2A
        features['pBwB'] = pB+' '+wB
        features['pAwA'] = pA+' '+wA
        features['p2Bw2B'] = p2B+' '+w2B
        features['p2Aw2A'] = p2A+' '+w2A
        features['p2BpBpA'] = p2B+' '+pB+' '+pA
        features['pBpAp2A'] = pB+' '+pA+' '+p2A
        features['pAp2Ap3A'] = pA+' '+p2A+' '+p3A

        headWord = chunk['words'][-1].lower()
        if wA == 'of':
            headWord += ' of'
        headPOS = chunk['pos'][-1]

        # NP1 features
        features['headWord'] = headWord 

        if 'chunk' in chunk and chunk['chunk'] == 'NP':
            features['npWords'] = ' '.join(chunk['words']).lower()
            features['npTags'] = ' '.join(chunk['pos'])

        if len(chunk['pos']) > 1 and is_noun( chunk['pos'][-2] ):
            features['NC'] = ' '.join(chunk['words'][-2:]).lower()

        if is_adv(pA):
            if is_adj(p2A) and not chunks.is_NP_ending_at(j+1):
                features['adj'] = w2A
                features['adjTag'] = p2A
        else:
            if is_adj(pA) and not chunks.is_NP_ending_at(j):
                features['adj'] = wA
                features['adjTag'] = pA

        if 'adj' in features:
            features['adj&headWord'] = features['adj']+' '+headWord
            features['adjTag&headWord'] = features['adjTag']+' '+headWord

            if 'NC' in features:
                features['adj&NC'] = features['adj']+' '+features['NC']
                features['adjTag&NC'] = features['adj']+' '+features['NC']
        
        if 'npWords' in features:
            features['npTags&headWord'] = features['npTags']+' '+headWord 
            if 'NC' in features: 
                features['npTags&NC'] = features['npTags']+' '+features['NC']

        # NP2 fatures
        features['headWord&headPOS'] = headWord + ' ' + headPOS
        features['headNumber'] = noun_number(headPOS)

        # features with words after NP
        if 'npWords' in features:
            words_after_NP = ['</s>' if w is None else w.lower() for w in chunks.get_n_words_after_chunk(idx, 3)]

            features['headWord&wordAfterNP'] = headWord + ' ' + words_after_NP[0]
            features['headWord&2wordsAfterNP'] = features['headWord&wordAfterNP'] + ' ' + words_after_NP[1]
            features['headWord&3wordsAfterNP'] = features['headWord&2wordsAfterNP'] + ' ' + words_after_NP[2]
            features['npWords&wordAfterNP'] = features['npWords'] + ' ' + words_after_NP[0]
            features['npWords&2wordsAfterNP'] = features['npWords&wordAfterNP'] + ' ' + words_after_NP[1]
            features['npWords&3wordsAfterNP'] = features['npWords&2wordsAfterNP'] + ' ' + words_after_NP[2]

        # verb features
        if is_adv(pB) and is_verb(p2B):
            features['verb'] = w2B
        elif is_verb(pB):
            features['verb'] = wB

        if 'verb' in features:
            for feat in FEATURE_SETS['NP1']:
                if feat in features:
                    features['verb&' + feat] = features['verb'] + ' ' + features[feat]

        # Subject position is defined as follows: The word immediately
        # after the NP is a verb and the word immediately preceding the NP
        # is not a verb or a preposition.
        if chunk['j'] < len(poses) - 1 and i >= 0:
            n = chunk['j'] + 1
            if is_verb(poses[n]) and not (is_verb(pB) or is_prep(pB)):
                features['verbSbj'] = words[n]

        # preposition features
        if 'verb' not in features:
            if is_prep(pB):
                features['prep'] = wB
            elif is_prep(p2B):
                features['prep'] = w2B

        if 'prep' in features:
            for feat in FEATURE_SETS['NP1']:
                if feat in features:
                    features['prep&' + feat] = features['prep'] + ' ' + features[feat]

        # features with word before NP
        if 'verbObj' not in features and 'prepBefore' not in features:
            for feat in FEATURE_SETS['NP1']:
                if feat in features:
                    features['wB&' + feat] = wB + ' ' + features[feat]
        
        # custom features
        is_mass = headWord in self.mass_nouns
        is_count = headWord in self.count_nouns
        if is_mass and is_count:
            features['count'] = 'mass&count'
        elif is_mass:
            features['count'] = 'mass'
        elif is_count:
            features['count'] = 'count'

        if self.occurs_in_prev_sentence(headWord):
            features['headWordinPrevSent'] = 'true'
        if i >= 0 and (headWord in set(words[:i+1])):
            features['headWordinSent'] = 'true'

        self.prev_sentence = set(words)
        return features

    def occurs_in_prev_sentence(self, word):
        return word.lower() in self.prev_sentence
