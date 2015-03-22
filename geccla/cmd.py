import os

from logger import log


def run(cmd):
    log.debug(cmd)
    return os.popen(cmd).read()

def wc(file):
    if not os.path.exists(file) or os.path.isdir(file):
        return None
    return int(os.popen('wc -l ' + file).read().strip().split()[0])

def ln(file, link):
    run("ln -s {} {}".format(os.path.abspath(file), os.path.abspath(link)))


def get_source_side_of_file(file):
    if is_parallel_file(file):
        run("cut -f1 {0} > {0}.err".format(file))
        return file + '.err'
    return file

def is_parallel_file(file):
    with open(file) as file_io:
        if "\t" in file_io.next().strip():
            return True
    return False

def filebase_path(dir, filepath):
    return os.path.join(dir, os.path.splitext(filepath)[0])
