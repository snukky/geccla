import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from logger import log


def compose_feature_set(name, base_feature, set_name, extra=[]):
    global FEATURE_SETS

    if set_name not in FEATURE_SETS:
        log.error("feature set '{}' does not exist!".format(set_name))
        return None
    if name in FEATURE_SETS and FEATURE_SETS[name] is not None:
        log.warn("feature set '{}' exist and is not empty!".format(name))
        return None

    FEATURE_SETS[name] = list(set([base_feature + '&' + feat 
                                   for feat in FEATURE_SETS[set_name]] + extra))
    return len(FEATURE_SETS[name])
    
def sum_feature_sets(name, set_names):
    global FEATURE_SETS

    if name in FEATURE_SETS and FEATURE_SETS[name] is not None:
        log.warn("feature set '{}' exist and is not empty!".format(name))
        return None
    if type(set_names) == type(''):
        set_names = set_names.split()

    result = []
    for set_name in set_names:
        if set_name not in FEATURE_SETS:
            log.error("feature set '{}' does not exist!".format(set_name))
        else:
            result += FEATURE_SETS[set_name]
    FEATURE_SETS[name] = list(set(result))

    return len(FEATURE_SETS[name])


FEATURE_SETS = {
    # general feature sets
    'tok': 
        'wB5A0 wB4A1 wB3A2 wB2A3 wB1A4 wB0A5 '
        'wB4A0 wB3A1 wB2A2 wB1A3 wB0A4 '
        'wB3A0 wB2A1 wB1A2 wB0A3 '
        'wB2A0 wB1A1 wB0A1 wB1A0 wB0A1'.split(),

    'pos':
        'pB5A0 pB4A1 pB3A2 pB2A3 pB1A4 pB0A5 '
        'pB4A0 pB3A1 pB2A2 pB1A3 pB0A4 '
        'pB3A0 pB2A1 pB1A2 pB0A3 '
        'pB2A0 pB1A1 pB0A1 pB1A0 pB0A1'.split(),

    'awc':
        'cB5A0 cB4A1 cB3A2 cB2A3 cB1A4 cB0A5 '
        'cB4A0 cB3A1 cB2A2 cB1A3 cB0A4 '
        'cB3A0 cB2A1 cB1A2 cB0A3 '
        'cB2A0 cB1A1 cB0A1 cB1A0 cB0A1'.split(),

    'src': ['src'],

    # A.Roz. features - word n-grams
    'wordngrams': 
        'wB, w2B, w3B, wA, w2A, w3A, wBwA, w2BwB, wAw2A, w3Bw2BwB, w2BwBwA, '
        'wBwAw2A, wAw2Aw3A, w4Bw3Bw2BwB, w3Bw2BwBwA, w2BwBwAw2A, wBwAw2Aw3A, '
        'wAw2Aw3w4A'.split(', '),

    # A.Roz. features - POS
    'POS':
        'pB, p2B, p3B, pA, p2A, p3A, pBpA, p2BpB, pAp2A, pBwB, pAwA, p2Bw2B, '
        'p2Aw2A, p2BpBpA, pBpAp2A, pAp2Ap3A'.split(', '),

    # A.Roz. features - NP1
    'NP1': 
        'headWord, npWords, NC, adj&headWord, adjTag&headWord, adj&NC, '
        'adjTag&NC, npTags&headWord, npTags&NC'.split(', '),

    # A.Roz. features - NP2
    'NP2':
        'headWord&headPOS, headNumber'.split(', '),

    'wordsAfterNP':
        'headWord&wordAfterNP, npWords&wordAfterNP, headWord&2wordsAfterNP, '
        'npWords&2wordsAfterNP, headWord&3wordsAfterNP, npWords&3wordsAfterNP' \
        .split(', '),
    
    'wordsBeforeNP': None,
    'Verb': None,
    'Preposition': None,

    # my custom features
    'extra': 
        'count headWordinSent headWordinPrevSent'.split(),
}

sum_feature_sets('genall', 'tok pos awc')
sum_feature_sets('genpos', 'tok pos')
sum_feature_sets('gentok', 'tok awc')

sum_feature_sets('all', 'tok pos awc')

compose_feature_set('wordsBeforeNP', 'wB', 'NP1')
compose_feature_set('Preposition', 'prep', 'NP1')
compose_feature_set('Verb', 'verb', 'NP1', extra=['verb'])

sum_feature_sets('rozword', 'wordngrams')
sum_feature_sets('rozpos', 'wordngrams POS')
sum_feature_sets('roz', 'wordngrams POS NP1 NP2 wordsAfterNP wordsBeforeNP Verb Preposition')
sum_feature_sets('rozextra', 'roz extra')
sum_feature_sets('rozsrc', 'roz src')
