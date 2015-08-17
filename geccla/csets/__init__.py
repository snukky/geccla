
def frac_dict(dict):
    div = sum(dict.values())
    for key in sorted(dict, key=dict.__getitem__, reverse=True):
        yield key, dict[key] / float(div)
        
def incfrac_dict(dict):
    div = sum(dict.values())
    incfrac = 0.0
    for key in sorted(dict, key=dict.__getitem__, reverse=True):
        incfrac += dict[key] / float(div)
        yield key, incfrac

def sort_dict(dict):
    for key in sorted(dict, key=dict.__getitem__, reverse=True):
        yield key, dict[key]

def readable_dict(dict):
    text = ''
    for key in sorted(dict, key=dict.__getitem__, reverse=True):
        text += "{} ({}) ".format(key, dict[key]) 
    return text

