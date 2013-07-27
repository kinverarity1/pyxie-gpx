'''Keep configuration settings for pyxie in CFG files.

This module will try to load the ``pyxie.cfg`` settings file from three locations:
the current working directory, the user's home directory, and the original
in the package source directory (SYSTEM_CFG), in that priority. Each file
need not contain all settings, and settings from higher priority files take
precendence.

Usage
-----

For the configuration file containing this text::

    [GUI]
    save_as = blah.txt

you can access settings like so::
    
    >>> from pyxie.config import config
    >>> for section_name in config.sections():
    ...     print 'Section:', section_name
    ...     for name, value in config.items(section_name):
    ...         print '    ', name, ':', value
    Section: GUI
        save_as = blah.txt

Format
------
        
The settings file should be in CFG file format. See for more info:

http://www.doughellmann.com/PyMOTW/ConfigParser/#accessing-configuration-settings

Github
------

If for some reason the SYSTEM_CFG file is missing, load will try to download the
original from Github, and write it as a backup 'github-mtpy.cfg' configuration
file.
        
'''
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import ConfigParser
import os
import shutil
import urllib2

from appdirs import user_data_dir

CFG_FN = 'pyxie.cfg'

# Possible locations for CFG files

SYSTEM_CFG = os.path.join(os.path.dirname(__file__), CFG_FN)
USER_CFG = os.path.join(os.path.expanduser('~'), CFG_FN)
WORKINGDIR_CFG = os.path.join(os.getcwd(), CFG_FN)
    
    
def load():
    '''Return config parser.
    
    Checks for SYSTEM_CFG, USER_CFG, and WORKINGDIR_CFG and updates
    the parser object with the values found each time.
    
    '''
    def combine(parsers):
        '''Return a new SafeConfigParser containing the options already set in
        *parsers*.
        
        Works forwards through the list, so the higher priority parsers should go
        at the end of *parsers*.
        
        '''
        new_parser = ConfigParser.SafeConfigParser()
        for parser in parsers:
            if not parser:
                continue
            for section in parser.sections():
                if not new_parser.has_section(section):
                    new_parser.add_section(section)
                for name, value in parser.items(section):
                    new_parser.set(section, name, str(value))
        return new_parser
    
    def make_parser(fn):
        parser = ConfigParser.SafeConfigParser()
        parser.read(fn)
        return parser
    
    parser = make_parser(SYSTEM_CFG)
    for fn in [USER_CFG, WORKINGDIR_CFG]:
        try:
            next_parser = make_parser(fn)
            if next_parser.read(fn):
                parser = combine([parser, next_parser])
        except:
            raise
    return parser
    
    
config = load()

data_dir = user_data_dir(config.get('program', 'name'), config.get('program', 'name'))
if not os.path.isdir(data_dir):
    os.makedirs(data_dir)

log = StringIO.StringIO()