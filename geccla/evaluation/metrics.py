
def accuracy(tp, tn, fp, fn):
    return (tp + tn) / float(tp + tn + fp + fn)

def precision(tp, tn, fp, fn):
    if tp == 0 and fp == 0:
        return 0.0
    return tp / float(tp + fp)

def recall(tp, tn, fp, fn):
    if tp == 0 and fn == 0:
        return 0.0
    return tp / float(tp + fn)

def fscore(tp, tn, fp, fn, base=0.5):
    p = precision(tp, tn, fp, fn)
    if p == 0.0:
        return 0.0
    r = recall(tp, tn, fp, fn)
    return (1 + base**2) * (p * r) / (base**2*p + r)

def edits_count(tp, tn, fp, fn, xyz):
    acc = (tp + tn) / float(tp + tn + fp + fn + xyz)
    aa_edits = tn / float(tn + fp) if tn + fp != 0 else 0
    ab_edits = tp / float(fn + tp + xyz) if fn + tp + xyz != 0 else 0
    skipped_ab_edits = fn / float(fn + tp + xyz) if fn + tp + xyz != 0 else 0
    return (acc, aa_edits, ab_edits, skipped_ab_edits)

def specificity(tp, tn, fp, fn):
    return tn / float(tn + fp)

def fall_out(tp, tn, fp, fn):
    return fp / float(tn + fp)

def bias(tp, tn, fp, fn):
    return (tp + fp) / float(tp + tn + fp + fn)

def prevalence(tp, tn, fp, fn):
    return (tp + fn) / float(tp + tn + fp + fn)
