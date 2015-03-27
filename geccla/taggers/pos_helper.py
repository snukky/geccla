
class TAGS:
    NA          = '<NA>'

    NOUNS       = set('NN NNP NNS NNPS'.split())
    ADJECTIVES  = set('JJ JJR JJS VBN'.split())
    VERBS       = set('VB VBG VBD VBP VBZ VBN MD'.split())
    ADVERBS     = set('RB RBR RBS'.split())
    PRONOUNS    = set('PRP PRP$ WP WP$'.split())
    PREPS       = set(['IN'])

def is_verb(tag):
    return tag in TAGS.VERBS

def is_prep(tag):
    return tag in TAGS.PREPS

def is_pronoun(tag):
    return tag in TAGS.PRONOUNS

def is_noun(tag):
        return tag in TAGS.NOUNS

def is_adj(tag):
    return tag in TAGS.ADJECTIVES

def is_adv(tag):
    return tag in TAGS.ADVERBS

def noun_number(tag):
    if tag == 'NN' or tag == 'NNP':
        return 'singular'
    elif tag == 'NNS' or tag == 'NNPS':
        return 'plural'
    else:
        return None
