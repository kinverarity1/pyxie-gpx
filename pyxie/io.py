import glob
import os
import xmlmisc

import numpy as np

from pyxie import core


def read_gpx(fileobj):
    '''Get array of times, lons, lats, and elevations.
    
    Args:
        - *fileobj*: file-like object containing GPX XML data.
        
    
    '''
    times = []
    lons = []
    lats = []
    elevs = []
    line = None
    for trkpt, elem in xmlmisc.iterparse(fileobj, cls=xmlmisc.GPXTrackpoint):
        if trkpt:
            times.append(elem.time)
            lons.append(elem.lon)
            lats.append(elem.lat)
            elevs.append(elem.elev)
    return np.vstack((times, lons, lats, elevs)).T

    
def search_directory_tree(root_path, pattern='*.gpx', debug=None):
    '''Find list of filenames from directory tree.'''
    fns = []
    if debug is None:
        debug = config.log
    for root, dirs, files in os.walk(root_path):
        incr_fns = glob.glob(os.path.join(root, pattern))
        if incr_fns:
            debug.write('% 9.0f %s\n' % (len(incr_fns), root))
        fns += incr_fns
    debug.write('---------\n')
    debug.write('% 9.0f Total\n' % len(fns))
    return fns

    
# def gpx_trackpoint(x, y, epsg='4326', dt=None, z=None):
    # '''Return XML string.
    
    # <trkpt lat="-35.0001252349" lon="138.5810883343"><ele>47.72</ele><time>2013-08-08T06:06:04Z</time></trkpt>'''
    # lons, lats = core.convert_coordinate_system(xs, ys, epsg1='4326', epsg2='28353'):
    # p1 = pyproj.Proj(init='epsg:%s' % epsg1)
    # p2 = pyproj.Proj(init='epsg:%s' % epsg2)
    # nxs, nys = pyproj.transform(p1, p2, xs, ys)
    # return nxs, nys

