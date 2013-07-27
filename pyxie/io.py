import glob
import os
import xmlmisc

import numpy as np

import config

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
    

def import_to_db(fns, dbname=None, dbfn=None):
    if dbfn is None:        
        if dbname is None:
            dbname = config.get('database', 'name')
        dbfn = os.path.join(config.data_dir, dbname + '.npy')
    assert dbfn.endswith('.npy')
    
    if not os.path.exists(dbfn):
        darr = np.zeros((0, 4), dtype=np.float32)
    else:
        darr = np.load(dbfn)
    dsets = {}
    for fn in fns:
        arr = read_gpx(fn)
        if arr.shape[0] > 0:
            dsets[fn] = {'from': arr[0, 0], 'to': arr[-1, 0]}
        darr = np.vstack((darr, arr))
    darr.sort(axis=0)
    np.save(dbfn, darr)
    return dsets
    
    
def get_motions(motionspecs, dbname=None, dbfn=None):
    if dbfn is None:        
        if dbname is None:
            dbname = config.get('database', 'name')
        dbfn = os.path.join(config.data_dir, dbname + '.npy')
    assert dbfn.endswith('.npy')
    
    arrs = []
    darr = np.load(dbfn, mmap_mode='r')
    for mspec in motionspecs:
        if 'from' in mspec and 'to' in mspec:
            inds = []
            for i in range(len(darr)):
                if darr[i, 0] >= mspec['from'] and darr[i, 0] <= mspec['to']:
                    inds.append(i)
                if darr[i, 0] > mspec['to']:
                    break
            if len(inds) > 0:
                arr = darr[inds]
                arrs.append(arr)
                continue
    return arrs
    
    