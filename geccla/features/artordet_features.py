import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from taggers.lbj_chunker import LBJChunker
from taggers.lbj_chunker import Chunks


MASS_NOUNS_FILE = '/home/romang/scripts/conll/scripts/artordet/nouns/mass-nouns.wiktionary.txt'
COUNT_NOUNS_FILE = '/home/romang/scripts/conll/scripts/artordet/nouns/countable-nouns.wiktionary.txt'


DEBUG = False

FEATURE_SETS = {
    'src': [
        'src'
    ],
    'word': [
        'wB1', 'wB2', 'wB3', 'wA1', 'wA2', 'wA3',
        'wB1A1', 'wB2B1', 'wA1A2',
        'wB3B2B1', 'wB2B1A1', 'wB1A1A2', 'wA1A2A3',
        'wB4B3B2B1', 'wB3B2B1A1', 'wB2B1A1A2', 'wB1A1A2A3', 'wA1A2A3A4'
    ],
    'pos': [
        'pB1', 'pB2', 'pB3', 'pA1', 'pA2', 'pA3',
        'pB1A1', 'pB2B1', 'pA1A2',
        'pB3B2B1', 'pB2B1A1', 'pB1A1A2', 'pA1A2A3',
        'wB1pB1', 'wB2pB2', 
        'wA1pA1', 'wA2pA2', 
    ],
    'cls': [
        'cB1', 'cB2', 'cB3', 'cA1', 'cA2', 'cA3',
        'cB1A1', 'cB2B1', 'cA1A2',
        'cB3B2B1', 'cB2B1A1', 'cB1A1A2', 'cA1A2A3',
        'wB1cB1', 'wB2cB2', 
        'wA1cA1', 'wA2cA2', 
    ],
    'pos2': [
        'pB1', 'pB2', 'pB3', 'pA1', 'pA2', 'pA3',
        'pB1A1', 'pB2B1', 'pA1A2',
        'pB3B2B1', 'pB2B1A1', 'pB1A1A2', 'pA1A2A3',
        'pB4B3B2B1', 'pB3B2B1A1', 'pB2B1A1A2', 'pB1A1A2A3', 'pA1A2A3A4'
    ],
    'cls2': [
        'cB1', 'cB2', 'cB3', 'cA1', 'cA2', 'cA3',
        'cB1A1', 'cB2B1', 'cA1A2',
        'cB3B2B1', 'cB2B1A1', 'cB1A1A2', 'cA1A2A3',
        'cB4B3B2B1', 'cB3B2B1A1', 'cB2B1A1A2', 'cB1A1A2A3', 'cA1A2A3A4'
    ],
    'wordpos': [
        'wpB1', 'wpB2', 'wpB3', 'wpA1', 'wpA2', 'wpA3',
        'wpB2B1', 'wpB1A1', 'wpA1A2',
        'wpB3B2B1', 'wpB2B1A1', 'wpB1A1A2', 'wpA1A2A3',
        'wpB4B3B2B1', 'wpB3B2B1A1', 'wpB2B1A1A2', 'wpB1A1A2A3', 'wpA1A2A3A4'
    ],
    'wordcls': [
        'wcB1', 'wcB2', 'wcB3', 'wcA1', 'wcA2', 'wcA3',
        'wcB2B1', 'wcB1A1', 'wcA1A2',
        'wcB3B2B1', 'wcB2B1A1', 'wcB1A1A2', 'wcA1A2A3',
        'wcB4B3B2B1', 'wcB3B2B1A1', 'wcB2B1A1A2', 'wcB1A1A2A3', 'wcA1A2A3A4'
    ],
    'NP1': [
        'hW', 'npWs', 'NC',
        'adj&hW', 'adjP&hW', 'adj&NC', 'adjP&NC',
        'npPs&hW', 'npPs&NC'
    ],
    'NP2': [
        'hW&hP', 'hNum',
    ],
    'waNP': [
        'hW&1waNP', 'npWs&1waNP',
        'hW&2waNP', 'npWs&2waNP',
        'hW&3waNP', 'npWs&3waNP'
    ],
    'wbNP': [ ],
    'verb': [ ],
    'preps': [ ],

    'chunk': [
        'verb', 'verbSbj', 
        'prep', 'npWs', 'npPs',
        'adj', 'adjP',
    ],
    'dict': [
        'count',
    ],
    'sent': [
        'hWinSent', 
        'hWinPrevSent', 
        'thethe'
    ]
}

def compose_feature_set(base_feature, set_name):
    result = []
    for feature in FEATURE_SETS[set_name]:
        result.append(base_feature + '&' + feature)
    return set(result)

FEATURE_SETS['wbNP'] = compose_feature_set('wB1', 'NP1')
FEATURE_SETS['verb'] = compose_feature_set('verb', 'NP1')
FEATURE_SETS['preps'] = compose_feature_set('prep', 'NP1')

def sum_feature_sets(names):
    if type(names) == type(''):
        names = names.split(' ')
    result = []
    for name in names:
        result += FEATURE_SETS[name]
    return set(result)

FEATURE_SETS['posngrams'] = sum_feature_sets('word pos2 wordpos')
FEATURE_SETS['clsngrams'] = sum_feature_sets('word cls2 wordcls')
FEATURE_SETS['poscls'] = sum_feature_sets('word pos2 wordpos cls2 wordcls')
FEATURE_SETS['roz'] = sum_feature_sets('word pos NP1 NP2 waNP wbNP verb preps')
FEATURE_SETS['rozplus'] = sum_feature_sets('roz wordpos dict sent')
FEATURE_SETS['rozsrc'] = sum_feature_sets('src roz')
FEATURE_SETS['allnosrc'] = sum_feature_sets([f for f in FEATURE_SETS.keys()]) - set(['src'])


class ArtOrDetFeatures():

    ART_OR_DETS = 'a an the'.split() + ['']
    SENTENTIAL_ADVERBS  = 'already recently now later then however even possibly indeed often just really also'.split()

    NOUN_TAGS       = set('NN NNP NNS NNPS'.split())
    ADJECTIVE_TAGS  = set('JJ JJR JJS VBN'.split())
    VERB_TAGS       = set('VB VBG VBD VBP VBZ VBN MD'.split())
    ADVERBS_TAGS    = set('RB RBR RBS'.split())
    PRONOUNS        = set('PRP PRP$ WP WP$'.split())

    NA = '<NA>'

    def __init__(self, wc_dic=None):
        self.edits_finder = ConfusionEditsFinder(ArtOrDetFeatures.ART_OR_DETS)
        with open(MASS_NOUNS_FILE) as f:
            self.mass_nouns = set([line.strip().lower() for line in f.readlines()])
        with open(COUNT_NOUNS_FILE) as f:
            self.count_nouns = set([line.strip().lower() for line in f.readlines()])
        self.wc_tagger = WordClassTagger(wc_dic)
        self.prev_sentence = set()

    def extract_features(self, chunks, cor_text=None):
        artordets = OrderedDict()
        
        words = [w.lower() for w in chunks.words]
        poses = chunks.pos
        clses = self.wc_tagger.tag_words(words)

        if DEBUG:
            print >> sys.stderr, ' '.join(words)
            if cor_text:
                print >> sys.stderr, cor_text

        for idx, (word, cor_word) in self.__artordet_indexes(chunks, cor_text).iteritems():
            features = {}
            
            # index of word preceding the article
            i = idx - 1
            # index of word following the article
            j = idx if word == '<null>' else idx + 1

            if DEBUG:
                print >> sys.stderr, ' {0} ({1},{2}) {3} -> {4}'.format(idx, i, j, word, cor_word)

            word_b1 = words[i] if i >= 0 else '<s>'
            word_b2 = words[i-1] if i >= 1 else '<s>'
            word_b3 = words[i-2] if i >= 2 else '<s>'
            word_b4 = words[i-3] if i >= 3 else '<s>'
            word_a1 = words[j] if j <= len(words) - 1 else '</s>'
            word_a2 = words[j+1] if j <= len(words) - 2 else '</s>'
            word_a3 = words[j+2] if j <= len(words) - 3 else '</s>'
            word_a4 = words[j+3] if j <= len(words) - 4 else '</s>'

            pos_b1 = poses[i] if i >= 0 else '<S>'
            pos_b2 = poses[i-1] if i >= 1 else '<S>'
            pos_b3 = poses[i-2] if i >= 2 else '<S>'
            pos_b4 = poses[i-3] if i >= 3 else '<S>'
            pos_a1 = poses[j] if j <= len(poses) - 1 else '</S>'
            pos_a2 = poses[j+1] if j <= len(poses) - 2 else '</S>'
            pos_a3 = poses[j+2] if j <= len(poses) - 3 else '</S>'
            pos_a4 = poses[j+3] if j <= len(poses) - 4 else '</S>'

            cls_b1 = clses[i] if i >= 0 else '<S>'
            cls_b2 = clses[i-1] if i >= 1 else '<S>'
            cls_b3 = clses[i-2] if i >= 2 else '<S>'
            cls_b4 = clses[i-3] if i >= 3 else '<S>'
            cls_a1 = clses[j] if j <= len(clses) - 1 else '</S>'
            cls_a2 = clses[j+1] if j <= len(clses) - 2 else '</S>'
            cls_a3 = clses[j+2] if j <= len(clses) - 3 else '</S>'
            cls_a4 = clses[j+3] if j <= len(clses) - 4 else '</S>'

            chunk = chunks.get_chunk_by_word_idx(idx)

            if DEBUG:
                print >> sys.stderr, ' ', chunk

            # source and label articles
            features['src'] = word
            features['lbl'] = cor_word or word

            # word n-grams features
            features['wB1'] = word_b1
            features['wB2'] = word_b2
            features['wB3'] = word_b3
            features['wA1'] = word_a1
            features['wA2'] = word_a2
            features['wA3'] = word_a3
            features['wB3B2'] = word_b3 + ' ' + word_b2
            features['wB2B1'] = word_b2 + ' ' + word_b1
            features['wB1A1'] = word_b1 + ' ' + word_a1
            features['wA1A2'] = word_a1 + ' ' + word_a2
            features['wA2A3'] = word_a2 + ' ' + word_a3
            features['wB3B2B1'] = word_b3 + ' ' + word_b2 + ' ' + word_b1
            features['wB2B1A1'] = word_b2 + ' ' + word_b1 + ' ' + word_a1
            features['wB1A1A2'] = word_b1 + ' ' + word_a1 + ' ' + word_a2
            features['wA1A2A3'] = word_a1 + ' ' + word_a2 + ' ' + word_a3

            features['wB4B3B2B1'] = word_b4 + ' ' + word_b3 + ' ' + word_b2 + ' ' + word_b1
            features['wB3B2B1A1'] = word_b3 + ' ' + word_b2 + ' ' + word_b1 + ' ' + word_a1
            features['wB2B1A1A2'] = word_b2 + ' ' + word_b1 + ' ' + word_a1 + ' ' + word_a2
            features['wB1A1A2A3'] = word_b1 + ' ' + word_a1 + ' ' + word_a2 + ' ' + word_a3
            features['wA1A2A3A4'] = word_a1 + ' ' + word_a2 + ' ' + word_a3 + ' ' + word_a4

            # POS features
            features['p'] = poses[idx] if word != '<null>' else '<NULL>'
            features['pB1'] = pos_b1
            features['pB2'] = pos_b2
            features['pB3'] = pos_b3
            features['pA1'] = pos_a1
            features['pA2'] = pos_a2
            features['pA3'] = pos_a3
            features['pB1A1'] = pos_b1 + ' ' + pos_a1
            features['pB2B1'] = pos_b2 + ' ' + pos_b1
            features['pA1A2'] = pos_a1 + ' ' + pos_a2
            features['pB3B2B1'] = pos_b3 + ' ' + pos_b2 + ' ' + pos_b1
            features['pB2B1A1'] = pos_b2 + ' ' + pos_b1 + ' ' + pos_a1
            features['pB1A1A2'] = pos_b1 + ' ' + pos_a1 + ' ' + pos_a2
            features['pA1A2A3'] = pos_a1 + ' ' + pos_a2 + ' ' + pos_a3
            features['pB4B3B2B1'] = pos_b4 + ' ' + pos_b3 + ' ' + pos_b2 + ' ' + pos_b1
            features['pB3B2B1A1'] = pos_b3 + ' ' + pos_b2 + ' ' + pos_b1 + ' ' + pos_a1
            features['pB2B1A1A2'] = pos_b2 + ' ' + pos_b1 + ' ' + pos_a1 + ' ' + pos_a2
            features['pB1A1A2A3'] = pos_b1 + ' ' + pos_a1 + ' ' + pos_a2 + ' ' + pos_a3
            features['pA1A2A3A4'] = pos_a1 + ' ' + pos_a2 + ' ' + pos_a3 + ' ' + pos_a4

            # word & POS features (depreciated)
            features['wB1pB1'] = word_b1 + ' ' + pos_b1
            features['wB2pB2'] = word_b2 + ' ' + pos_b2
            features['wB3pB3'] = word_b3 + ' ' + pos_b3
            features['wA1pA1'] = word_a1 + ' ' + pos_a1
            features['wA2pA2'] = word_a2 + ' ' + pos_a2
            features['wA3pA3'] = word_a3 + ' ' + pos_a3

            # word & POS n-gram features
            features['wpB1'] = word_b1 + pos_b1
            features['wpB2'] = word_b2 + pos_b2
            features['wpB3'] = word_b3 + pos_b3
            features['wpA1'] = word_a1 + pos_a1
            features['wpA2'] = word_a2 + pos_a2
            features['wpA3'] = word_a3 + pos_a3
            features['wpB3B2'] = word_b3 + pos_b3 + ' ' + word_b2 + pos_b2
            features['wpB2B1'] = word_b2 + pos_b2 + ' ' + word_b1 + pos_b1
            features['wpB1A1'] = word_b1 + pos_b1 + ' ' + word_a1 + pos_a1
            features['wpA1A2'] = word_a1 + pos_a1 + ' ' + word_a2 + pos_a2
            features['wpA2A3'] = word_a2 + pos_a2 + ' ' + word_a3 + pos_a3
            features['wpB3B2B1'] = word_b3 + pos_b3 + ' ' + word_b2 + pos_b2 + ' ' + word_b1 + pos_b1
            features['wpB2B1A1'] = word_b2 + pos_b2 + ' ' + word_b1 + pos_b1 + ' ' + word_a1 + pos_a1
            features['wpB1A1A2'] = word_b1 + pos_b1 + ' ' + word_a1 + pos_a1 + ' ' + word_a2 + pos_a2
            features['wpA1A2A3'] = word_a1 + pos_a1 + ' ' + word_a2 + pos_a2 + ' ' + word_a3 + pos_a3

            features['wpB4B3B2B1'] = word_b4 + pos_b4 + ' ' + word_b3 + pos_b3 + ' ' + word_b2 + pos_b2 + ' ' + word_b1 + pos_b1
            features['wpB3B2B1A1'] = word_b3 + pos_b3 + ' ' + word_b2 + pos_b2 + ' ' + word_b1 + pos_b1 + ' ' + word_a1 + pos_a1
            features['wpB2B1A1A2'] = word_b2 + pos_b2 + ' ' + word_b1 + pos_b1 + ' ' + word_a1 + pos_a1 + ' ' + word_a2 + pos_a2
            features['wpB1A1A2A3'] = word_b1 + pos_b1 + ' ' + word_a1 + pos_a1 + ' ' + word_a2 + pos_a2 + ' ' + word_a3 + pos_a3
            features['wpA1A2A3A4'] = word_a1 + pos_a1 + ' ' + word_a2 + pos_a2 + ' ' + word_a3 + pos_a3 + ' ' + word_a4 + pos_a4

            head_word = chunk['words'][-1].lower()
            if word_a1 == 'of':
                head_word += ' of'

            head_pos = chunk['pos'][-1]

            # word class features
            features['c'] = clses[idx] if word != '<null>' else '<NULL>'
            features['cB1'] = cls_b1
            features['cB2'] = cls_b2
            features['cB3'] = cls_b3
            features['cA1'] = cls_a1
            features['cA2'] = cls_a2
            features['cA3'] = cls_a3
            features['cB1A1'] = cls_b1 + ' ' + cls_a1
            features['cB2B1'] = cls_b2 + ' ' + cls_b1
            features['cA1A2'] = cls_a1 + ' ' + cls_a2
            features['cB3B2B1'] = cls_b3 + ' ' + cls_b2 + ' ' + cls_b1
            features['cB2B1A1'] = cls_b2 + ' ' + cls_b1 + ' ' + cls_a1
            features['cB1A1A2'] = cls_b1 + ' ' + cls_a1 + ' ' + cls_a2
            features['cA1A2A3'] = cls_a1 + ' ' + cls_a2 + ' ' + cls_a3
            features['cB4B3B2B1'] = cls_b4 + ' ' + cls_b3 + ' ' + cls_b2 + ' ' + cls_b1
            features['cB3B2B1A1'] = cls_b3 + ' ' + cls_b2 + ' ' + cls_b1 + ' ' + cls_a1
            features['cB2B1A1A2'] = cls_b2 + ' ' + cls_b1 + ' ' + cls_a1 + ' ' + cls_a2
            features['cB1A1A2A3'] = cls_b1 + ' ' + cls_a1 + ' ' + cls_a2 + ' ' + cls_a3
            features['cA1A2A3A4'] = cls_a1 + ' ' + cls_a2 + ' ' + cls_a3 + ' ' + cls_a4

            # word & word class features (depreciated)
            features['wB1cB1'] = word_b1 + ' ' + cls_b1
            features['wB2cB2'] = word_b2 + ' ' + cls_b2
            features['wB3cB3'] = word_b3 + ' ' + cls_b3
            features['wA1cA1'] = word_a1 + ' ' + cls_a1
            features['wA2cA2'] = word_a2 + ' ' + cls_a2
            features['wA3cA3'] = word_a3 + ' ' + cls_a3

            # word & word class n-gram features
            features['wcB1'] = word_b1 + cls_b1
            features['wcB2'] = word_b2 + cls_b2
            features['wcB3'] = word_b3 + cls_b3
            features['wcA1'] = word_a1 + cls_a1
            features['wcA2'] = word_a2 + cls_a2
            features['wcA3'] = word_a3 + cls_a3
            features['wcB3B2'] = word_b3 + cls_b3 + ' ' + word_b2 + cls_b2
            features['wcB2B1'] = word_b2 + cls_b2 + ' ' + word_b1 + cls_b1
            features['wcB1A1'] = word_b1 + cls_b1 + ' ' + word_a1 + cls_a1
            features['wcA1A2'] = word_a1 + cls_a1 + ' ' + word_a2 + cls_a2
            features['wcA2A3'] = word_a2 + cls_a2 + ' ' + word_a3 + cls_a3
            features['wcB3B2B1'] = word_b3 + cls_b3 + ' ' + word_b2 + cls_b2 + ' ' + word_b1 + cls_b1
            features['wcB2B1A1'] = word_b2 + cls_b2 + ' ' + word_b1 + cls_b1 + ' ' + word_a1 + cls_a1
            features['wcB1A1A2'] = word_b1 + cls_b1 + ' ' + word_a1 + cls_a1 + ' ' + word_a2 + cls_a2
            features['wcA1A2A3'] = word_a1 + cls_a1 + ' ' + word_a2 + cls_a2 + ' ' + word_a3 + cls_a3

            features['wcB4B3B2B1'] = word_b4 + cls_b4 + ' ' + word_b3 + cls_b3 + ' ' + word_b2 + cls_b2 + ' ' + word_b1 + cls_b1
            features['wcB3B2B1A1'] = word_b3 + cls_b3 + ' ' + word_b2 + cls_b2 + ' ' + word_b1 + cls_b1 + ' ' + word_a1 + cls_a1
            features['wcB2B1A1A2'] = word_b2 + cls_b2 + ' ' + word_b1 + cls_b1 + ' ' + word_a1 + cls_a1 + ' ' + word_a2 + cls_a2
            features['wcB1A1A2A3'] = word_b1 + cls_b1 + ' ' + word_a1 + cls_a1 + ' ' + word_a2 + cls_a2 + ' ' + word_a3 + cls_a3
            features['wcA1A2A3A4'] = word_a1 + cls_a1 + ' ' + word_a2 + cls_a2 + ' ' + word_a3 + cls_a3 + ' ' + word_a4 + cls_a4

            head_cls = self.wc_tagger.tag_words([head_word])[0]

            # NP1 features
            features['hW'] = head_word 
            features['hP'] = head_pos 
            features['hC'] = head_cls 

            if 'chunk' in chunk and chunk['chunk'] == 'NP':
                features['npWs'] = ' '.join(chunk['words']).lower()
                features['npPs'] = ' '.join(chunk['pos'])

            if len(chunk['pos']) > 1 and self.is_noun( chunk['pos'][-2] ):
                features['NC'] = ' '.join(chunk['words'][-2:]).lower()

            if self.is_adv(pos_a1):
                if self.is_adj(pos_a2) and not chunks.is_NP_ending_at(j+1):
                    features['adj'] = word_a2
                    features['adjP'] = pos_a2
            else:
                if self.is_adj(pos_a1) and not chunks.is_NP_ending_at(j):
                    features['adj'] = word_a1
                    features['adjP'] = pos_a1

            if 'adj' in features:
                features['adj&hW'] = features['adj'] + ' ' + head_word 
                features['adjP&hW'] = features['adjP'] + ' ' + head_word 

                if 'NC' in features:
                    features['adj&NC'] = features['adj'] + ' ' + features['NC']
                    features['adjP&NC'] = features['adjP'] + ' ' + features['NC']
           
            if 'npWs' in features and 'NC' in features: 
                features['npPs&hW'] = features['npPs'] + ' ' + head_word 
                features['npPs&NC'] = features['npPs'] + ' ' + features['NC']

            # NP2 fatures
            features['hW&hP'] = head_word + ' ' + head_pos
            features['hNum'] = self.noun_number(head_pos)

            # features with words after NP
            if 'npWs' in features:
                words_after_NP = ['</s>' if w is None else w.lower() for w in chunks.get_n_words_after_chunk(idx, 3)]

                features['hW&1waNP'] = head_word + ' ' + words_after_NP[0]
                features['hW&2waNP'] = features['hW&1waNP'] + ' ' + words_after_NP[1]
                features['hW&3waNP'] = features['hW&2waNP'] + ' ' + words_after_NP[2]
                features['npWs&1waNP'] = features['npWs'] + ' ' + words_after_NP[0]
                features['npWs&2waNP'] = features['npWs&1waNP'] + ' ' + words_after_NP[1]
                features['npWs&3waNP'] = features['npWs&2waNP'] + ' ' + words_after_NP[2]

            # verb features
            if self.is_adv(pos_b1) and self.is_verb(pos_b2):
                features['verb'] = word_b2
            elif self.is_verb(pos_b1):
                features['verb'] = word_b1

            if 'verb' in features:
                for f in FEATURE_SETS['NP1']:
                    if f in features:
                        features['verb&' + f] = features['verb'] + ' ' + features[f]

            # Subject position is defined as follows: The word immediately
            # after the NP is a verb and the word immediately preceding the NP
            # is not a verb or a preposition.
            if chunk['j'] < len(poses) - 1 and i >= 0:
                n = chunk['j'] + 1
                if self.is_verb(poses[n]) and not (self.is_verb(pos_b1) or self.is_prep(pos_b1)):
                    features['verbSbj'] = words[n]

            # preposition features
            if 'verb' not in features:
                if self.is_prep(pos_b1):
                    features['prep'] = word_b1
                elif self.is_prep(pos_b2):
                    features['prep'] = word_b2

            if 'prep' in features:
                for feature in FEATURE_SETS['NP1']:
                    if feature in features:
                        features['prep&' + feature] = features['prep'] + ' ' + features[feature]

            # features with word before NP
            if 'verbObj' not in features and 'prepBefore' not in features:
                for feature in FEATURE_SETS['NP1']:
                    if feature in features:
                        features['wB1&' + feature] = word_b1 + ' ' + features[feature]
            
            # custom features
            is_mass = head_word in self.mass_nouns
            is_count = head_word in self.count_nouns
            if is_mass and is_count:
                features['count'] = 'mass&count'
            elif is_mass:
                features['count'] = 'mass'
            elif is_count:
                features['count'] = 'count'

            if self.occurs_in_prev_sentence(head_word):
                features['hWinPrevSent'] = 'true'
            if i >= 0 and (head_word in set(words[:i+1])):
                features['hWinSent'] = 'true'

            if word.lower() == 'the' and self.is_thethe_structure(j, poses):
                features['thethe'] = 'true'

            artordets[ (idx, j) ] = features
        
        self.prev_sentence = set(words)
        return artordets

    def is_thethe_structure(self, j, poses):
        if j < len(poses) and j > 0:
            return poses[j-1] == 'DT' and poses[j] == 'JJR' and re.match(r".*DT JJR .*, DT JJR", ' '.join(poses))
        return False

    def occurs_in_prev_sentence(self, word):
        return word.lower() in self.prev_sentence

    def is_noun(self, tag):
        return tag in ArtOrDetFeatures.NOUN_TAGS

    def is_adj(self, tag):
        return tag in ArtOrDetFeatures.ADJECTIVE_TAGS

    def is_verb(self, tag):
        return tag in ArtOrDetFeatures.VERB_TAGS

    def is_prep(self, tag):
        return tag == 'IN'

    def is_adv(self, tag):
        return tag in ArtOrDetFeatures.ADVERBS_TAGS

    def is_pronoun(self, tag):
        return tag in ArtOrDetFeatures.PRONOUNS

    def is_artordet(self, word):
        return word.lower() in ArtOrDetFeatures.ART_OR_DETS

    def noun_number(self, tag):
        if tag == 'NN' or tag == 'NNP':
            return 'singular'
        elif tag == 'NNS' or tag == 'NNPS':
            return 'plural'
        else:
            return 'none'

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: python %s text.err [--debug]" % sys.argv[0]
        exit()

    if len(sys.argv) >= 3 and '--debug' in sys.argv:
        DEBUG = True

    chunker = LBJChunker()
    extractor = ArtOrDetFeatures()
    file = sys.argv[1]

    s = 0
    for chunks in chunker.chunks_and_pos_tags(file):
        print s, ':', ' '.join(chunks.words)
        for (i, j), features in extractor.extract_features(chunks).iteritems():
            print "(%i, %i)" % (i, j) 
            pprint.pprint(features)
        s += 1
