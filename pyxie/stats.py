import numpy as np


def total_distance(xs, ys):
    return np.sum(distances(xs, ys))

def distances(xs, ys):
    dx = np.gradient(xs)
    dy = np.gradient(ys)
    return np.sqrt(dx ** 2 + dy ** 2)


class Path(object):
    '''Args:
    
        - *array*: n x m where m >= 3. The first column should be timestamps,
          the second x coordinate and the third y coordinates.
          
    '''
    def __init__(self, xs, ys, times=None):
        if times is None:
            times = np.ones_like(xs) * np.nan
        self.xs = xs
        self.ys = ys
        self.times = times
        
    @property
    def total_distance(self):
        return total_distance(self.xs, self.ys)
        
    def __str__(self):
        return '\n'.join([
                'Path statistics:',
                'Distance: %s' % self.total_distance,
                ])
