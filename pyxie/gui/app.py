'''Entry point for the GUI applications. You can run this script:

    $ python app.py AppName [args]
    
where AppName can be:

    trackeditor
    
args can include:

    level=DEBUG/INFO/WARNING/ERROR/CRITICAL
    
          or a number between 0 and 50
    
'''
import logging
import sys

from PyQt4.QtGui import QApplication

from pyxie.gui.trackeditor import TrackEditorMainWindow


def main():
    if len(sys.argv) == 1:
        logging.warning('You need to provide an AppName. Using trackeditor by default.')
        app_name = 'trackeditor'
        args = []
    else:
        app_name = sys.argv[1]
        if len(sys.argv) > 2:
            args = sys.argv[2:]
        else:
            args = []
    return main_func(args, app_name=app_name)
    

def main_func(args, app_name='trackeditor'):
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    argdict = {'level': 50}
    for arg in args:
        key, value = arg.split('=')
        if key == 'level':
            try:
                level = (levels.index(value) + 1) * 10
            except:
                level = '%.0f' % float(value)
            value = level
        argdict[key] = value
        
    logging.basicConfig(level=argdict['level'])
    app = QApplication([])
    window = False
    if app_name == 'trackeditor':
        logging.debug('Importing TrackEditorMainWindow')
        main_window_class = TrackEditorMainWindow
    if not main_window_class is False:
        main_window = main_window_class()
        main_window.show()
        sys.exit(app.exec_())
    else:
        logging.error('AppName %s not known; try trackeditor' % app_name)

    
if __name__ == '__main__':
    main()