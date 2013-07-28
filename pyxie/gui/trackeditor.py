import datetime
import logging
import os

from matplotlib.dates import date2num, num2date, epoch2num, num2epoch
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np

from pyxie import io
from pyxie import core
from pyxie.gui.qt import QtGui, QtCore, Qt, MainWindow, MplCanvas



program_name = 'Pyxie Track Editor'
program_version = '0.1'


        
class TrackEditorMainWindow(MainWindow):
    def __init__(self, *args, **kwargs):
        logging.debug('args=%s kwargs=%s' % (args, kwargs))
        MainWindow.__init__(self, *args, **kwargs)
        self.init_ui()
        
    def init_ui(self):
        open_track = self.create_action(text='Open track', shortcut='Ctrl+O', slot=self.slot_open_track)
        exit = self.create_action(text='E&xit', shortcut='Alt+F4', slot=self.slot_exit)
        about = self.create_action(text='&About', shortcut='F1', slot=self.slot_about)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        help_menu = menubar.addMenu('&Help')
        self.add_actions(file_menu, [open_track, exit])
        self.add_actions(help_menu, [about])
        
        main_widget = QtGui.QWidget(self)
        main_layout = QtGui.QVBoxLayout(main_widget)
        
        self.map = TrackMap(5, 5)
        self.graph = TrackGraph(5, 5)
        splitter = QtGui.QSplitter(main_widget)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(self.map)
        splitter.addWidget(self.graph)
        
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        self.map.clear()
        self.graph.clear(axis='off')
        
        self.setGeometry(400, 50, 900, 650) # debug
        # self.showMaximized()
        self.setWindowTitle(program_name)
        self.show()
   
    def slot_open_track(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        fn = dialog.getOpenFileName(self,
                'Import track file', os.getcwd(),
                'GPS Exchange Format (*.gpx)'
                )
        arr = io.read_gpx(fn)
        logging.info('Read %d points from %s' % (arr.shape[0], fn))
        
        self.map.clear()
        self.map.coords = arr
        self.map.plot()
        
        self.graph.clear(axis='on')
        self.graph.coords = arr
        self.graph.plot()
        logging.debug('Mapping %s' % fn)
   
    def slot_exit(self):
        self.close()
    
    def slot_about(self):
        QtGui.QMessageBox.about(
                self, 'About ' + program_name,
                '%(prog)s version %(version)s\n\n'
                '' % {
                        'prog': program_name,
                        'version': program_version,
                        })
    
    
    
class TrackMap(QtGui.QWidget):
    def __init__(self, width, height, dpi=72):
        QtGui.QWidget.__init__(self)
        self.coords = np.empty(shape=(0, 2))
        self.artists = {}
        self.canvas = MplCanvas(self, width=width / float(dpi),
                                height=height / float(dpi), dpi=dpi)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        box = QtGui.QVBoxLayout()
        box.addWidget(self.mpl_toolbar)
        box.addWidget(self.canvas)
        self.setLayout(box)
        
    def plot(self):
        if 'track' in self.artists:
            self.artists['track'].remove()
            del self.artists['track']
        xs, ys = core.convert_coordinate_system(
                self.coords[:, 1], self.coords[:, 2], epsg2='28353')
        self.artists['track'] = self.ax.plot(xs, ys)[0]
        self.draw()
    
    def clear(self):
        for artist in self.artists.values():
            artist.remove()
        self.artists.clear()
        if 'ax' in self.__dict__:
            self.canvas.fig.delaxes(self.ax)
        self.ax = self.canvas.fig.add_axes([0, 0, 1, 1], aspect=True)
        self.ax.axis('off')
        self.ax.set_aspect(aspect='equal', adjustable='datalim')
        
    def draw(self):
        self.canvas.draw()
    
        
        
class TrackGraph(QtGui.QWidget):
    def __init__(self, width, height, dpi=72):
        QtGui.QWidget.__init__(self)
        self.coords = np.empty(shape=(0, 2))
        self.artists = {}
        self.canvas = MplCanvas(self, width=width / float(dpi),
                                height=height / float(dpi), dpi=dpi)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        box = QtGui.QVBoxLayout()
        box.addWidget(self.mpl_toolbar)
        box.addWidget(self.canvas)
        self.setLayout(box)
        
    def plot(self):
        if 'line' in self.artists:
            self.artists['line'].remove()
            del self.artists['line']
        xs, ys = core.convert_coordinate_system(
                self.coords[:, 1], self.coords[:, 2], epsg2='28353')
        speed = core.speed(self.coords[:, 0], xs, ys)
        epoch_times = self.coords[:, 0]
        mpl_dts = epoch2num(epoch_times)
        self.artists['line'] = self.ax.plot_date(
                mpl_dts, speed, ls='-', marker='None')[0]
        min_mpl_dts = min(mpl_dts)
        max_mpl_dts = max(mpl_dts)
        range_mpl_dts = max_mpl_dts - min_mpl_dts
        self.ax.set_xlim(min_mpl_dts - range_mpl_dts * 0.05, 
                         max_mpl_dts + range_mpl_dts * 0.05)
        self.ax.set_ylim(-1, max(speed) + max(speed) * 0.05)
        self.draw()
    
    def clear(self, axis='off'):
        for artist in self.artists.values():
            artist.remove()
        self.artists.clear()
        if 'ax' in self.__dict__:
            self.canvas.fig.delaxes(self.ax)
        self.ax = self.canvas.fig.add_axes([0.05, 0.1, 0.85, 0.94])
        self.ax.axis(axis)
        self.ax.set_aspect(aspect='auto', adjustable='datalim')
        
    def draw(self):
        self.canvas.draw()
    
        