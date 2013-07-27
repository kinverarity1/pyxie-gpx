import numpy as np

class Track(object):
    def __init__(self, points=None, **kwargs):
        assert points.shape[1] == 4
        self.points = points
        
class Import(object):