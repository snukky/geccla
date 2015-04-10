import os
import shutil

from logger import log


def run(cmd):
    log.debug(cmd)
    return os.popen(cmd).read()

def wc(file):
    if not os.path.exists(file) or os.path.isdir(file):
        return None
    count = int(os.popen('wc -l ' + file).read().strip().split()[0])
    log.info("file {} has {} lines".format(file, count))
    return count

def ln(file, link):
    run("ln -s {} {}".format(os.path.abspath(file), os.path.abspath(link)))

def wdiff(file1, file2, output_file=None):
    if not os.path.exists(file1):
        log.error("file {} does not exists".format(file1))
        return None
    if not os.path.exists(file2):
        log.error("file {} does not exists".format(file2))
        return None

    if not output_file:
        output_file = file2 + '.wdiff'
    run("wdiff {0} {1} | sed -e :a -e '/-]$/N; s/\\n/ /; ta'"
        " | grep -P '\\[-|{{\+' > {2}".format(file1, file2, output_file))

    return output_file

def cut(file, col_file=None, col=1):
    if not col_file:
        col_file ='{}.col{}'.format(file, col)
    run("cut -f{} {} > {}".format(col, file, col_file))
    return col_file


def source_side_of_file(file, src_file=None):
    if is_parallel_file(file):
        if not src_file:
            src_file = file + '.src'
        return cut(file, src_file)
    return file

def is_parallel_file(file):
    with open(file) as file_io:
        if "\t" in file_io.next().strip():
            return True
    return False

def base_filename(file):
    return os.path.splitext(os.path.basename(file))[0]

def base_filepath(dir, file):
    filename = os.path.split(file)[1]
    filepath = os.path.join(dir, os.path.splitext(filename)[0])
    log.debug("dir {} and file {} gives filepath: {}".format(dir, file, filepath))
    return filepath
