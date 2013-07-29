'''Launch a Pyxie GUI app.'''
import argparse
import logging
import sys

from PyQt4.QtGui import QApplication

import pyxie
from pyxie import config
from pyxie.gui.trackeditor import TrackEditorMainWindow



def main():
    app_name = 'trackeditor'
    args = get_parser().parse_args(sys.argv[1:])
    if args.config_file:
        print(config.USER_CFG)
        sys.exit(0)
    return main_func(args, app_name=app_name)
    
    
def get_parser():
    fix = lambda d: d.replace('Pyxie', 'Pyxie v%s' % pyxie.__version__)
    parser = argparse.ArgumentParser(description=fix(__doc__), 
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-a', '--app', default='trackeditor', help='Which app to launch')
    parser.add_argument('-v', '--verbose', default=50, help='1 to 50; lower is more detailed messages')
    parser.add_argument('--config-file', action='store_true', help='Show the location of your configuration file')
    return parser
    

def main_func(args, app_name='trackeditor'):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    app = QApplication([])
    window = False
    if app_name == 'trackeditor':
        logger.debug('Importing TrackEditorMainWindow')
        main_window_class = TrackEditorMainWindow
    if not main_window_class is False:
        main_window = main_window_class()
        main_window.show()
        sys.exit(app.exec_())
    else:
        logger.error('--app=%s not known; try trackeditor' % app_name)

    
if __name__ == '__main__':
    main()