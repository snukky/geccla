
def compose_feature_set(feature_sets, base_feature, set_name):
    result = []
    for feature in feature_sets[set_name]:
        result.append(base_feature + '&' + feature)
    return set(result)

def sum_feature_sets(feature_sets, names):
    if type(names) == type(''):
        names = names.split(' ')
    result = []
    for name in names:
        result += feature_sets[name]
    return set(result)


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

FEATURE_SETS['genall'] = sum_feature_sets(FEATURE_SETS, 'tok pos awc')
FEATURE_SETS['genpos'] = sum_feature_sets(FEATURE_SETS, 'tok pos')
FEATURE_SETS['gentok'] = sum_feature_sets(FEATURE_SETS, 'tok awc')

FEATURE_SETS['wordsBeforeNP'] = compose_feature_set(FEATURE_SETS, 'wB', 'NP1')
FEATURE_SETS['Preposition']   = compose_feature_set(FEATURE_SETS, 'prep', 'NP1')
FEATURE_SETS['Verb']          = compose_feature_set(FEATURE_SETS, 'verb', 'NP1')
FEATURE_SETS['Verb'].add('verb')

FEATURE_SETS['word']     = sum_feature_sets(FEATURE_SETS, 'wordngrams')
FEATURE_SETS['pos']      = sum_feature_sets(FEATURE_SETS, 'wordngrams POS')
FEATURE_SETS['roz']      = sum_feature_sets(FEATURE_SETS, 'wordngrams POS NP1 NP2 wordsAfterNP wordsBeforeNP Verb Preposition')
FEATURE_SETS['rozextra'] = sum_feature_sets(FEATURE_SETS, 'roz extra')
FEATURE_SETS['rozsrc']   = sum_feature_sets(FEATURE_SETS, 'roz src')
