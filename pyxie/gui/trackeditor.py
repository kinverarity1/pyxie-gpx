import datetime
import logging
import os

from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np

from pyxie import io
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
        main_layout = QtGui.QHBoxLayout(main_widget)
        
        self.graph = TrackGraph(5, 5)
        self.table = CoordsTable(headers=['Time', 'X', 'Y', 'Z'])
        splitter = QtGui.QSplitter(main_widget)
        splitter.addWidget(self.graph)
        splitter.addWidget(self.table)
        
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        self.graph.clear()
        self.graph.link_to_coordstable(self.table)
        self.table.link_to_trackgraph(self.graph)
        
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
        self.graph.clear()
        arr = io.read_gpx(fn)
        logging.info('Read %d points from %s' % (arr.shape[0], fn))
        self.graph.coords = arr
        self.graph.plot()
        logging.debug('Graphing %s' % fn)
        self.table.refresh_from_linked_trackgraph()
   
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
    
    
    
class TrackGraph(QtGui.QWidget):
    def __init__(self, width, height, dpi=72):
        QtGui.QWidget.__init__(self)
        self.table = None
        self.coords = np.empty(shape=(0, 2))
        self.artists = {}
        self.canvas = MplCanvas(self, width=width / float(dpi),
                                height=height / float(dpi), dpi=dpi)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        box = QtGui.QVBoxLayout()
        box.addWidget(self.mpl_toolbar)
        box.addWidget(self.canvas)
        self.setLayout(box)
        
    def link_to_coordstable(self, table):
        self.table = table
        
    def get_track(self):
        if 'track' in self.artists:
            return self.artists['track']
        else:
            return None
    
    def set_track(self, obj):
        self.artists['track'] = obj
    
    track = property(get_track, set_track)
        
    def plot(self):
        if self.track:
            self.track.remove()
            del self.track
        self.track = self.ax.plot(self.coords[:, 1], self.coords[:, 2])[0]
        self.draw()
        
    def point_selection_updated(self):
        if not self.table:
            return
        else:
            items = self.table.table_widget.selectedItems()
            if 'table_selection' in self.artists:
                logging.debug('%s' % self.artists['table_selection'])
                while len(self.artists['table_selection']) > 0:
                    self.artists['table_selection'].pop(0).remove()
            self.artists['table_selection'] = []
            rows_plotted = set()
            for item in items:
                drawn = self.ax.plot([self.coords[item.row(), 1]],
                                     [self.coords[item.row(), 2]],
                                     marker='o', mfc='k', mec='k', ms=10)
                self.artists['table_selection'] += drawn
            self.draw()
    
    def clear(self):
        if 'table_selection' in self.artists:
            while len(self.artists['table_selection']) > 0:
                self.artists['table_selection'].pop(0).remove()
        if self.track:
            self.track.remove()
        self.artists.clear()
        if 'ax' in self.__dict__:
            self.canvas.fig.delaxes(self.ax)
        self.ax = self.canvas.fig.add_axes([0, 0, 1, 1], aspect=True)
        self.ax.axis('off')
        
    def draw(self):
        self.canvas.draw()
    
        
class CoordsTable(QtGui.QWidget):
    '''QWidget showing a table. Not editable.
    
    Args:
        - *coords*: n x 2 array
        - *headers*: n x list of strings
        
    '''
    def __init__(self, coords=None, headers=None):
        QtGui.QWidget.__init__(self)
        self.graph = None
        if coords is None:
            coords = np.empty(shape=(0, 2))
        self.coords = coords
        if headers is None:
            headers = ['Col%d' % i for i in range(self.coords.shape[0])]
        self.headers = headers
        self.init_ui()
        self.refresh(self.coords)
        
    def link_to_trackgraph(self, graph):
        self.graph = graph
        self.table_widget.itemSelectionChanged.connect(
                                            self.graph.point_selection_updated)
        
    def refresh_from_linked_trackgraph(self):
        if self.graph:
            self.coords = self.graph.coords
            self.refresh()
        
    @property
    def table(self):
        table = []
        for i in range(self.coords.shape[0]):
            table.append([str(datetime.datetime.fromtimestamp(self.coords[i, 0])),
                          str(self.coords[i, 1]),
                          str(self.coords[i, 2]),
                          str(self.coords[i, 3])])
        return table
        
    def init_ui(self):
        self.table_widget = QtGui.QTableWidget()
        self.table_widget.setShowGrid(True)
        box = QtGui.QVBoxLayout()
        box.addWidget(self.table_widget)
        self.setLayout(box)

    def refresh(self, table=None):
        if table is None:
            table = self.table
        self.table_widget.setRowCount(len(self.table))
        self.table_widget.setColumnCount(len(self.headers))
        self.table_widget.setHorizontalHeaderLabels(self.headers)
        for i in range(len(self.table)):
            for j in range(len(self.headers)):
                self.table_widget.setItem(i, j, QtGui.QTableWidgetItem(self.table[i][j]))
                
                