import math

def dist(p1, p2):
    return math.sqrt(sum((p1i-p2i)**2 for p1i, p2i in zip(p1, p2)))
