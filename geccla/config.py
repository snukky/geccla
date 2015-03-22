import os


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

THREADS = 8

class CLASSIFIERS:
    SNOW_BIN        = "/home/romang/tools/Snow_v3.2/snow"
    VW_BIN          = "/home/romang/tools/vowpal_wabbit/vowpalwabbit/vw"
    LIBLINEAR_DIR   = "/home/romang/tools/liblinear-ovo-1.94"
    MAXENT_BIN      = "java -Xmx8192m -jar /home/romang/tools/stanford-classifier-2014-08-27/stanford-classifier.jar"
    BSVM_BIN        = "/home/romang/tools/bsvm-2.08"


class TOOLS:
    PARALLEL    = 'parallel --no-notice --pipe --keep-order --block 2M -j {}'.format(THREADS)
    LOWERCASER  = 'perl /home/romang/mosesdecoder/scripts/tokenizer/lowercase.perl'

    STANFORD_TOKENIZER_DIR  = '/home/romang/tools/stanford-postagger-2014-01-04'
    LBJ_CHUNKER             = 'java -Xmx512m -cp $CLASSPATH:{}/taggers/lbj FixedLBJChunker'.format(ROOT_DIR)


class FILES:
    WORD_CLASSES = '/home/romang/data/word2vec/classes.moses.lc.wc'
