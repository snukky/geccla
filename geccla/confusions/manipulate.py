import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from logger import log


def impose_error_rate(cnfs_file, error_rate, matrix):
    num_rm = __calculate_num_of_AA_cnfs_to_remove(error_rate, matrix)

    with open(cnfs_file) as cnfs:
        for line in cnfs:
            if num_rm > 0 and __is_AA_conf_line(line):
                num_rm -= 1
            else:
                print line.strip()

def __calculate_num_of_AA_cnfs_to_remove(error_rate, matrix):
    new_AA_confs = int(math.floor(matrix.num_of_AB_confs() * (1-error_rate) / error_rate))

    num_rm = max(0, matrix.num_of_AA_confs() - new_AA_confs)
    log.debug("number of AA confusions to remove: {}".format(num_rm))

    return num_rm

def __is_AA_conf_line(line):
    fields = line.strip().split('|||')
    return fields[2].lower() == fields[3].lower()
