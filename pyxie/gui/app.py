'''Entry point for the GUI applications.

'''
import argparse
import logging
import sys

from PyQt4.QtGui import QApplication

from pyxie.gui.trackeditor import TrackEditorMainWindow




def main():
    app_name = 'trackeditor'
    args = get_parser().parse_args(sys.argv[1:])
    return main_func(args, app_name=app_name)
    
    
def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', default=50, help='1 to 50; lower is more detailed messages')
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
        logger.error('AppName %s not known; try trackeditor' % app_name)

    
if __name__ == '__main__':
    main()