import logging

import numpy as np

import pyproj


logger = logging.getLogger(__name__)


def convert_coordinate_system(xs, ys, epsg1='4326', epsg2='28353'):
    p1 = pyproj.Proj(init='epsg:%s' % epsg1)
    p2 = pyproj.Proj(init='epsg:%s' % epsg2)
    nxs, nys = pyproj.transform(p1, p2, xs, ys)
    return nxs, nys
    
    
def speed(times, xs, ys, 
          time_factor_into_hrs=(1. / 60. / 60),
          distance_factor_into_km=(1./  1000)):
    times = np.asarray(times)
    xs = np.asarray(xs)
    ys = np.asarray(ys)
    assert times.shape[0] == xs.shape[0] == ys.shape[0]
    distances = np.ones_like(times) * np.nan
    dxs = np.gradient(xs)
    dys = np.gradient(ys)
    dtimes = np.gradient(times) * time_factor_into_hrs
    distances = np.sqrt(dxs ** 2 + dys**2) * distance_factor_into_km
    speeds = distances / dtimes
    logger.debug('xs=%s' % xs)
    logger.debug('ys=%s' % ys)
    logger.debug('dxs=%s' % dxs)
    logger.debug('dys=%s' % dys)
    logger.debug('dtimes=%s' % dtimes)
    logger.debug('distances=%s' % distances)
    logger.debug('speeds=%s' % speeds)
    return speeds
    