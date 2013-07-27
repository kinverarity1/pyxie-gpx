import os.path as op

import h5py
import numpy as np


def open_hdf(fn, create_if_required=False):
    if op.exists(fn):
        h = h5py.File(fn, mode='o')
        return h
    elif create_if_required:
        h = h5py.File(fn, mode='w')
        init_hdf(h)
        h.close()
        return open_hdf(fn)
    else:
        raise OSError('%s does not exist and create_if_required=False' % fn)
        

def init_hdf(h):

    # Create root dataset inside h5 file, which is a single array with columns for:
    # - timestamp (float)
    # - longitude (float)
    # - latitude (float)
    # - elevation (float)
    # - metadata key (int)
    # but no rows... I think rows will be appended per import
    
    
# Create a module-level reference to the data array (via a module level function)
# but this has to go into the package's yaml configuration, and so then I'll need to sort out a 
# configuration/data storage folder via yaml, and that'll need to be set up on package installation.
def get_DataArray(h):
    return h['/data']
    

locData = get_Loc