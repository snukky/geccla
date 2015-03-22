
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
