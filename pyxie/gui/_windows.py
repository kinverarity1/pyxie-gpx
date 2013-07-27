import datetime
import logging
logging.basicConfig(level=logging.DEBUG)
import os

from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

from pyxie import io
import pyxie.config as config_mod
from pyxie.config import config
from pyxie.gui._qt import (
        QtGui, QtCore, Qt,
        MainWindow, GraphSetWidget, DataTable
        )

        
class PyxieMainWindow(MainWindow):
    def __init__(self, *args, **kwargs):
        MainWindow.__init__(self, *args, **kwargs)
        self.state = {'data_dir': config_mod.data_dir}
        if 'state' in kwargs:
            self.state.update(kwargs['state'])
        self.init_ui()
        
    def init_ui(self):
        open_track = self.create_action(text='Open track', shortcut='Ctrl+O', slot=self.slot_open_track)
        open_tracks = self.create_action(text='Open track(s)', shortcut='Ctrl+T', slot=self.slot_open_tracks)
        exit = self.create_action(text='E&xit', shortcut='Alt+F4', slot=self.slot_exit)
        about = self.create_action(text='&About', shortcut='F1', slot=self.slot_about)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        help_menu = menubar.addMenu('&Help')
        self.add_actions(file_menu, [open_track, open_tracks, exit])
        self.add_actions(help_menu, [about])
        
        main_widget = QtGui.QWidget(self)
        main_layout = QtGui.QHBoxLayout(main_widget)
        
        self.graph = GraphSetWidget(5, 5)
        self.table = DataTable([['Time', 'X', 'Y']])
        splitter = QtGui.QSplitter(main_widget)
        splitter.addWidget(self.graph)
        splitter.addWidget(self.table)
        
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        self.graph.clear()
        self.table.link_graphset(self.graph)
        self.graph.link_datatable(self.table)
        self.setGeometry(500, 50, 800, 600) # debug
        # self.showMaximized()
        self.setWindowTitle(config.get('program', 'name'))
        self.show()
    
    def slot_open_tracks(self):
        '''Open multiple tracks, just for viewing's sake.'''
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        fns = dialog.getOpenFileNames(self,
                'Import track file(s)', os.getcwd(),
                'GPS Exchange Format (*.gpx)'
                )
        ax = self.graph.ax
        if fns:
            logging.debug('Found %d track files' % len(fns))
            logging.debug('Removing previous tracks...')
            for line in ax.lines:
                line.remove()
            del ax.lines[:]
        arrs = []
        for fn in fns:
            arr = io.read_gpx(fn)
            arrs.append(arr)
            logging.info('Read %d points from %s' % (arr.shape[0], fn))
        for i, arr in enumerate(arrs):
            line = ax.plot(arr[:, 1], arr[:, 2])
            logging.debug('Graphing %s' % fns[i])
        self.graph.canvas.draw()
   
    def slot_open_track(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        fn = dialog.getOpenFileName(self,
                'Import track file', os.getcwd(),
                'GPS Exchange Format (*.gpx)'
                )
        self.graph.clear()
        ax = self.graph.ax
        arr = io.read_gpx(fn)
        logging.info('Read %d points from %s' % (arr.shape[0], fn))
        self.graph.set_array(arr)
        self.graph.plot()
        logging.debug('Graphing %s' % fn)
        
        table_data = [['Time', 'X', 'Y']]
        indices = [0, 1, 2]
        for i in range(arr.shape[0]):
            table_data.append([str(datetime.datetime.fromtimestamp(arr[i, 0])),
                               str(arr[i, 1]), 
                               str(arr[i, 2])])
        self.table.refresh(table=table_data)
   
    def slot_exit(self):
        self.close()
    
    def slot_about(self):
        QtGui.QMessageBox.about(
                self, 'About ' + config.get('program', 'name'),
                '%(prog)s version %(version)s\n\n'
                '' % {
                        'prog': config.get('program', 'name'),
                        'version': config.get('program', 'version'),
                        })
    