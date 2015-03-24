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

def wdiff(file1, file2, output_file=None):
    if os.path.exists(file1):
        log.error("file {} does not exists".format(file1))
        return None
    if os.path.exists(file2):
        log.error("file {} does not exists".format(file2))
        return None

    if not output_file:
        output_file = file2 + '.wdiff'
    run("wdiff {0} {1} | sed -e :a -e '/-]$/N; s/\\n/ /; ta'"
        " | grep -P '\\[-|{{\+' > {2}".format(file1, file2, output_file))

    return output_file


def source_side_of_file(file):
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