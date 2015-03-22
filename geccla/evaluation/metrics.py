
METRICS = {
}

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
    aa_edits = tn / float(tn + fp)
    ab_edits = tp / float(fn + tp + xyz)
    skipped_ab_edits = fn / float(fn + tp + xyz)
    return (acc, aa_edits, ab_edits, skipped_ab_edits)

def true_negative_rate(tp, tn, fp, fn):
    return tn / float(tn + fp)
