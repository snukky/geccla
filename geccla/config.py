import os


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

SCRIPTS_DIR = os.path.abspath(os.path.join(ROOT_DIR, '..', 'scripts'))

THREADS = 8


class CLASSIFIERS:
    SNOW_BIN        = "/home/romang/tools/Snow_v3.2/snow"
    VW_BIN          = "/home/romang/tools/vowpal_wabbit/vowpalwabbit/vw"
    LIBLINEAR_DIR   = "/home/romang/tools/liblinear-ovo-1.94"
    MAXENT_BIN      = "java -Xmx8192m -jar /home/romang/tools/stanford-classifier-2014-08-27/stanford-classifier.jar"
    BSVM_BIN        = "/home/romang/tools/bsvm-2.08"


class TOOLS:
    PARALLEL            = 'parallel --no-notice --pipe --keep-order --block 2M -j {}'.format(THREADS)

    STANFORD_TAGGER_DIR = '/home/snukky/Programy/stanford-postagger-2014-01-04'
    LBJ_CHUNKER         = 'java -Xmx512m -cp $CLASSPATH:{}/taggers/lbj FixedLBJChunker'.format(ROOT_DIR)

    MOSES_DIR           = '/home/romang/mosesdecoder'
    LOWERCASER          = 'perl /home/romang/mosesdecoder/scripts/tokenizer/lowercase.perl'

    NLTK_TOKENIZER      = '{}/nltk-tok'.format(SCRIPTS_DIR)
    NLTK_DETOKENIZER    = '{}/nltk-detok'.format(SCRIPTS_DIR)


class FILES:
    WORD_CLASSES        = '/home/snukky/Korpusy/word2vec/classes.moses.lc.wc'


class CONLL:
    ORIGINAL_TOKS = {
        'nucle' : '/home/romang/data/nucle/nucle.err',
        '2013'  : '/home/romang/data/nucle/nucle.test2013.err',
        '2014'  : '/home/romang/data/nucle/nucle.test2014.err',
    }
    TEST_SETS = {
        'nucle': {
            'allerrors' : '/home/romang/data/nucle/nucle.m2',
            '5errors'   : '/home/romang/data/nucle/nucle.5errors.m2',
            'artordets' : '/home/romang/data/nucle/nucle.artordet.m2'
        },
        '2013' : {
            'allerrors' : '/home/romang/data/nucle/nucle.test2013.m2',
            '5errors'   : '/home/romang/data/nucle/nucle.test2013.5errors.m2',
            'artordets' : '/home/romang/data/nucle/nucle.test2013.artordet.m2'
        },
        '2014' : {
            'allerrors' : '/home/romang/data/nucle/nucle.test2014.m2',
            '5errors'   : '/home/romang/data/nucle/nucle.test2014.5errors.m2',
            'artordets' : '/home/romang/data/nucle/nucle.test2014.artordet.m2'
        },
    }
