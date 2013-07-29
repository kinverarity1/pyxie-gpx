'''Miscellaneous routines for getting coordinate data out of GPX and KML files.'''
import datetime
import time
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import xml.etree.ElementTree

import numpy as np


class Element(object):
    '''XML Element wrapper.
    
    Args:
        - *elem*: xml.etree.ElementTree.Element object.
    
    Attributes:
        - *tag*: name of element
    
    '''
    def __init__(self, elem):
        self.elem = elem

    @property
    def tag(self):
        return self.elem.tag.split('}')[1]

        

class GPXTrackpoint(Element):
    '''Wrapper for GPX trkpt elements.
    
    Attributes:
        - *lat, lon, elev*: floats
        - *datetime*: datetime object
        
    '''
    name = 'trkpt'
    
    @property
    def lat(self):
        return float(self.elem.get('lat'))

    @property
    def lon(self):
        return float(self.elem.get('lon'))

    @property
    def elev(self):
        for echild in self.elem:
            if echild.tag.endswith('ele'):
                return float(echild.text)

    @property
    def datetime(self):
        for echild in self.elem:
            if echild.tag.endswith('time'):
                return datetime.datetime.strptime(
                        echild.text[:19], '%Y-%m-%dT%H:%M:%S')
                        
    @property
    def time(self):
        if self.datetime:
            return time.mktime(self.datetime.timetuple())
        else:
            return np.nan



class GPXWaypoint(Element):
    '''Wrapper for GPX wpt elements.
    
    Attributes:
        - *lat, lon, elev*: floats
        - *datetime*: datetime object
        
    '''
    name = 'wpt'
    
    @property
    def lat(self):
        return float(self.elem.get('lat'))

    @property
    def lon(self):
        return float(self.elem.get('lon'))

    @property
    def elev(self):
        for echild in self.elem:
            if echild.tag.endswith('ele'):
                return float(echild.text)

    @property
    def datetime(self):
        for echild in self.elem:
            if echild.tag.endswith('time'):
                return datetime.datetime.strptime(
                        echild.text[:19], '%Y-%m-%dT%H:%M:%S')

    @property
    def name(self):
        for echild in self.elem:
            if echild.tag.endswith('name'):
                return echild.text
                        
                        
                        
class KMLcoordinates(Element):
    '''Wrapper for KML coordinates elements.
    
    Attributes:
        - *lat, lon, elev*: floats
        - *datetime*: datetime object

    '''
    name = 'coordinates'
    
    @property
    def array(self):
        txt = self.elem.text.replace(' ', '\n')
        rows = txt.splitlines()
        arr = []
        for row in rows:
            row = row.strip()
            if not row:
                continue
            items = map(float, row.split(','))
            arr.append(items)
        return arr
    
    @property
    def lon(self):
        return [row[0] for row in self.array]
    
    @property
    def lat(self):
        return [row[1] for row in self.array]
        
    def elev(self):
        return [row[2] for row in self.array]
                        
                        
                        
def iterparse(source, cls=GPXTrackpoint, **kwargs):
    '''Iterate over *cls* elements in *source* file object.
    
    Args:
        - *source*: file-like object.
        - *cls*: class or subclass of Element class from this module.

    Kwargs: passed to xml.etree.ElementTree.iterparse.
       
    '''
    return ((cls(elem).tag == cls.name, cls(elem)) for event, elem
            in xml.etree.ElementTree.iterparse(source, **kwargs))

