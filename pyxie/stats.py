import datetime
import numpy as np


def total_dist(xs, ys):
    return np.sum(distances(xs, ys))

def distances(xs, ys):
    dx = np.gradient(xs)
    dy = np.gradient(ys)
    return np.sqrt(dx ** 2 + dy ** 2)

def total_time(times):
    return np.sum(np.gradient(times))

class Path(object):
    def __init__(s, xs, ys, times=None):
        if times is None:
            times = np.ones_like(xs) * np.nan
        s.xs = xs
        s.ys = ys
        s.abs_times = times
        s.times = np.gradient(s.abs_times)
        s.dxs = np.gradient(s.xs)
        s.dys = np.gradient(s.ys)
        s.dist = np.sqrt(s.dxs ** 2 + s.dys ** 2)
        s.tot_dist = np.nansum(s.dist)
        s.tot_time = np.nansum(s.times)
        s.spd = s.dist / s.times
        s.max_spd = np.nanmax(s.spd)
        s.avg_spd = np.nanmean(s.spd)
        
    def __str__(s):
        sl = []
        if s.tot_dist > 10e3:
            sl += ['Distance - total: %.2f km' % (s.tot_dist / 1000.)]
        else:
            sl += ['Distance - total: %.2f m' % (s.tot_dist)]
        sl += ['Time - total: %s hr:mins:secs' % str(datetime.timedelta(seconds=int(s.tot_time)))]
        sl += ['Speed - overall: %.2f km/h' % 
               (s.avg_spd / 1000. * 60. * 60.)]
        sl += ['Speed - maximum: %.2f km/h' % 
               (s.max_spd / 1000. * 60. * 60.)]
        return '\n'.join(sl)
        