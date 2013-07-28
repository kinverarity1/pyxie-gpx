import datetime
import logging
import os

from matplotlib.dates import date2num, num2date, epoch2num, num2epoch
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from pytz import timezone

from pyxie import io
from pyxie import core
from pyxie.gui.qt import QtGui, QtCore, Qt, MainWindow, MplCanvas



program_name = 'Pyxie Track Editor'
program_version = '0.1'
callbacks = [('link_location', 'Link location on map and graph', True)]


        
class TrackEditorMainWindow(MainWindow):
    def __init__(self, split_direction='horizontal', track_fn=None):
        MainWindow.__init__(self)
        logging.debug('__init__ split_direction=%s track_fn=%s' % (
                split_direction, track_fn))
        self.track_fn = track_fn
        self.dialogs = {}
        self.callbacks = {}
        self.split_direction = split_direction
        self.init_ui(split_direction=split_direction)
        if track_fn:
            self.open_track(track_fn)
                
        
    def init_ui(self, split_direction='horizontal'):
        self.split_direction = split_direction
            
        open_track = self.create_action(text='Open track...', shortcut='Ctrl+O', slot=self.slot_open_track)
        show_callbacks_dialog = self.create_action(text='Enable/disable graph features...', slot=self.slot_show_callbacks_dialog)
        set_gui_style = self.create_action(text='Flip orientation', slot=self.slot_flip_gui_direction)
        exit = self.create_action(text='E&xit', shortcut='Alt+F4', slot=self.slot_exit)
        about = self.create_action(text='&About...', shortcut='F1', slot=self.slot_about)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        view_menu = menubar.addMenu('&View')
        help_menu = menubar.addMenu('&Help')
        self.add_actions(file_menu, [open_track, exit])
        self.add_actions(view_menu, [show_callbacks_dialog, set_gui_style])
        self.add_actions(help_menu, [about])
        
        main_widget = QtGui.QWidget(self)
        main_layout = QtGui.QVBoxLayout(main_widget)
        
        self.map = TrackMap(5, 5)
        self.graph = TrackGraph(5, 5)
        splitter = QtGui.QSplitter(main_widget)
        if split_direction == 'horizontal':
            splitter.setOrientation(Qt.Vertical)
        elif split_direction == 'vertical':
            splitter.setOrientation(Qt.Horizontal)
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
        
    def slot_show_callbacks_dialog(self):
        if not 'callbacks' in self.dialogs:
            self.dialogs['callbacks'] = CallbacksDialog(self)
        self.dialogs['callbacks'].show()
        self.dialogs['callbacks'].activateWindow()
   
    def slot_flip_gui_direction(self):
        logging.debug('flipping gui direction')
        if self.split_direction == 'horizontal':
            self.close()
            self.__init__(split_direction='vertical', track_fn=self.track_fn)
        elif self.split_direction == 'vertical':
            self.close()
            self.__init__(split_direction='horizontal', track_fn=self.track_fn)
   
    def slot_open_track(self):
        logging.debug('Asking for track fn')
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        fn = dialog.getOpenFileName(self,
                'Import track file', os.getcwd(),
                'GPS Exchange Format (*.gpx)'
                )
        return self.open_track(fn)
        
    def open_track(self, fn):
        logging.debug('Opening track_fn' % fn)
        if not os.path.isfile(fn):
            return
        self.track_fn = fn
        self.coords = io.read_gpx(fn)
        logging.info('Read %d points from %s' % (self.coords.shape[0], fn))
        self.refresh()
        
    def refresh(self):
        for callback in self.callbacks.values():
            callback.disconnect()
        self.callbacks.clear()
        if 'callbacks' in self.dialogs:
            self.dialogs['callbacks'].close()
            del self.dialogs['callbacks']
        
        self.map.clear()
        self.map.coords = self.coords
        self.map.plot()
        
        self.graph.clear(axis='on')
        self.graph.coords = self.coords
        self.graph.plot()
        logging.debug('Mapping %s' % self.track_fn)
        
        self.callbacks['link_location'] = LinkLocationCallback(self)
        self.callbacks['link_location'].connect()
        
        self.setWindowTitle('%s : %s' % (program_name, self.track_fn))
   
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
    
    
    
class CallbacksDialog(QtGui.QDialog):
    def __init__(self, parent, *args, **kwargs):
        QtGui.QDialog.__init__(self, *args, **kwargs)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        main_layout = QtGui.QVBoxLayout(self)
        
        for callback in self.parent.callbacks.values():
            cb = QtGui.QCheckBox(callback.name, self)
            main_layout.addWidget(cb)
            cb.stateChanged.connect(callback.slot_state_changed)
        
        self.setLayout(main_layout)
        self.setWindowTitle('Enable graph features')
        

    
class LinkLocationCallback(object):
    def __init__(self, parent):
        self.parent = parent
        self.cid_map = None
        self.cid_graph = None
        self.name = 'Link mouse between map and graph'
        self.status = True
        logging.debug('__init__ LinkLocationCallback')
        
    def connect(self):
        self.cid_map = self.parent.map.canvas.mpl_connect('motion_notify_event', self.on_map_motion)
        self.cid_graph = self.parent.graph.canvas.mpl_connect('motion_notify_event', self.on_graph_motion)
        
    def disconnect(self):
        self.parent.map.canvas.mpl_disconnect(self.cid_map)
        self.parent.graph.canvas.mpl_disconnect(self.cid_graph)
        
    def slot_state_changed(self, state):
        if state == Qt.Checked:
            self.connect()
        elif state == Qt.Unchecked:
            self.disconnect()
            
    def remove_location_markers(self):
        for obj in (self.parent.map, self.parent.graph):
            if 'link_location_marker' in obj.artists:
                obj.artists['link_location_marker'].remove()
                del obj.artists['link_location_marker']
            
    def on_map_motion(self, event):
        map = self.parent.map
        if event.inaxes is self.parent.map.ax:
            index = ((map.xs - event.xdata) ** 2 + (map.ys - event.ydata) ** 2).argmin()
            self.update_markers(index)
            # logging.debug('map motion at %s %s!' % (event.xdata, event.ydata))
    
    def on_graph_motion(self, event):
        graph = self.parent.graph
        if event.inaxes is graph.ax:
            index = (np.abs(np.array(graph.mpl_dts) - event.xdata)).argmin()
            self.update_markers(index)
            # logging.debug('graph motion i=%s at time %s' % (index, num2date(event.xdata)))
            
    def update_markers(self, i):
        map = self.parent.map
        graph = self.parent.graph
        
        if not 'link_location_marker' in graph.artists:
            graph.artists['link_location_marker'] = graph.ax.plot(
                    [graph.mpl_dts[i]], [graph.speed[i]], marker='o', mfc='k', mec='k')[0]
        else:
            graph.artists['link_location_marker'].set_xdata([graph.mpl_dts[i]])
            graph.artists['link_location_marker'].set_ydata([graph.speed[i]])
        
        if not 'link_location_marker' in map.artists:
            map.artists['link_location_marker'] = map.ax.plot(
                    [map.xs[i]], [map.ys[i]], marker='o', mfc='k', mec='k')[0]
        else:
            map.artists['link_location_marker'].set_xdata([map.xs[i]])
            map.artists['link_location_marker'].set_ydata([map.ys[i]])
            
        graph.draw()
        map.draw()
        
    
    
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
        self.xs = xs
        self.ys = ys
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
        self.canvas.draw_idle()
    
        
        
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
        tz = timezone('Australia/Adelaide')
        utc = timezone('UTC')
        dts = [datetime.datetime.fromtimestamp(et) for et in epoch_times]
        utc_dts = [utc.localize(dt) for dt in dts]
        dts_localised = [dt.astimezone(tz) for dt in utc_dts]
        mpl_dts = date2num(dts_localised)
        self.artists['line'] = self.ax.plot_date(
                mpl_dts, speed, ls='-', marker='None')[0]
        min_mpl_dts = min(mpl_dts)
        max_mpl_dts = max(mpl_dts)
        range_mpl_dts = max_mpl_dts - min_mpl_dts
        self.ax.set_xlim(min_mpl_dts - range_mpl_dts * 0.05, 
                         max_mpl_dts + range_mpl_dts * 0.05)
        self.ax.set_ylim(-1, max(speed) + max(speed) * 0.05)
        self.mpl_dts = mpl_dts
        self.speed = speed
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
        self.canvas.draw_idle()
    
