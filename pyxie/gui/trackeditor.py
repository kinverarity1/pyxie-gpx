'''Python GUI tools for viewing (and editing in the future) GPX tracks.

There are already innumerable tools out there for looking at walk/cycle/drive 
data, but I found myself stuck when I don't have internet access and all I want
to do is look at, perhaps edit, and see general information about a trip I've 
taken. Also just fun to play around with it and learn more about building 
software with a GUI.

Another thing is splitting and cleaning GPX tracks. I want to be able to do it 
visually but I always seem to end up manually editing the XML file (!)'''
import argparse
import datetime
import logging
import os
import re
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import sys

from matplotlib import dates
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from pytz import timezone, common_timezones

from ..config import config
from .. import io
from .. import core
from .. import stats
from .. import utils
from . import qt
from .qt import QtGui, QtCore, Qt, MainWindow, MplCanvas, ExtendedCombo



program_name = 'Pyxie Track Editor'

logger = logging.getLogger(__name__)
        
        
        
class TrackEditorMainWindow(qt.MainWindow):
    '''Main GUI for Pyxie.

    The GUI has three panels: 

        1. On the left-hand side a way to select the data you want (e.g. select
           a GPX file, or a time period);
        2. In the centre show the data: e.g. with a map, a graph vs time or distance,
           and the text of the GPX file itself, or perhaps a table of coordinates.
        3. On the right-hand side show statistics of the data (total travel time, etc.)
           and also any filters that are or need to be applied to the data.

    The only keyword arguments that can be passed to this class constructor are ones that
    define how the GUI starts:

        - *file*: track file to load initially.
        - *cwd*: current working directory
        - and any of the method `ui_init`'s keyword arguments

    '''
    def __init__(self, **kws):
        qt.MainWindow.__init__(self)
        ks = {'file': None,
              'cwd': os.getcwd()}
        ks.update(kws)
        
        self.map = None
        self.graph = None

        self.cwds = [ks['cwd']]

        self.dialogs = {}
        self.callbacks = {}
        
        self.ui_init(**ks)

        if ks['file'] is not None:
            self.open_track(file=ks['file'])
   
        
    def ui_init(self, **kws):
        '''Initialise GUI.

        Keyword arguments:

            - *split_direction*: either 'horizontal' (the default) or 'vertical' - defines
              how the map and time/distance graph are arranged.
            - *graph_kws*: dict.

        '''
            
        self.ui_init_actions(**kws)
        self.ui_init_menu(**kws)
        self.ui_init_widgets(**kws)
        
        self.setGeometry(400, 50, 900, 650) # debug
        self.setWindowTitle(program_name)
        
        self.statusbar = qt.QtGui.QStatusBar(self)
        self.setStatusBar(self.statusbar)
        
        self.show()

    def ui_init_actions(self, **kws):
        self.actions = utils.NamedDict()
        self.actions.open_track = self.create_action('Open track...', shortcut='Ctrl+O')
        self.actions.open_track.triggered.connect(self.slot_open_track)
        self.actions.save_track = self.create_action('Save track', shortcut='Ctrl+S')
        self.actions.save_track.triggered.connect(self.slot_save_track)
        self.actions.flip_split_direction = self.create_action('Flip graph orientation')
        self.actions.flip_split_direction.triggered.connect(self.slot_flip_split_direction)
        self.actions.exit = self.create_action('E&xit', shortcut='Alt+F4')
        self.actions.exit.triggered.connect(self.slot_exit)
        self.actions.about = self.create_action('&About', shortcut='F1')
        self.actions.about.triggered.connect(self.slot_about)

    def ui_init_menu(self, **kws):
        self.menu = utils.NamedDict()
        self.menu.bar = self.menuBar()
        self.menu.file = self.menu.bar.addMenu('&File')
        self.menu.view = self.menu.bar.addMenu('&View')
        self.menu.help = self.menu.bar.addMenu('&Help')
        self.add_actions(self.menu.file, [self.actions.open_track, self.actions.save_track, self.actions.exit])
        self.add_actions(self.menu.view, [self.actions.flip_split_direction])
        self.add_actions(self.menu.help, [self.actions.about])

    def ui_init_widgets(self, **kws):
        ks = {'split_direction': 'horizontal',
              'graph_kws': {}}
        ks.update(kws)

        self.widgets = utils.NamedDict()
        self.widgets.mainwindow_central = qt.QtGui.QWidget(self)
        self.widgets.centre_tab = qt.QtGui.QTabWidget(self.widgets.mainwindow_central)
        self.widgets.map = TrackMap(5, 5)
        self.widgets.graph = TrackGraph(5, 5, **ks['graph_kws'])
        self.widgets.gpx_editor = qt.QtGui.QWidget(self.widgets.centre_tab)
        self.widgets.gpx_edit_box = qt.QtGui.QTextEdit(self.widgets.gpx_editor)
        self.widgets.gpx_edit_box.acceptRichText = False
        self.widgets.gpx_edit_box.setFontFamily('monospace')
        self.widgets.gpx_reformat_button = qt.QtGui.QPushButton('Reformat GPX with helpful linebreaks',
                                                                self.widgets.gpx_editor)
        self.widgets.gpx_reformat_button.clicked.connect(self.slot_reformat_gpx)
        self.widgets.stats_box = QtGui.QTextEdit(self)
        self.widgets.stats_box.setReadOnly(True)

        self.widgets.map_graph_splitter = QtGui.QSplitter(self.widgets.centre_tab)
        self.widgets.map_graph_splitter.setOrientation({'horizontal': Qt.Vertical, 'vertical': Qt.Horizontal}[ks['split_direction']])
        self.widgets.map_graph_splitter.addWidget(self.widgets.map)
        self.widgets.map_graph_splitter.addWidget(self.widgets.graph)

        self.widgets.main_window_splitter = QtGui.QSplitter(self.widgets.mainwindow_central)
        self.widgets.main_window_splitter.setOrientation(Qt.Horizontal)
        self.widgets.main_window_splitter.addWidget(self.widgets.centre_tab)
        self.widgets.main_window_splitter.addWidget(self.widgets.stats_box)

        # Create layouts and order widgets in them.

        layout_gpx_editor = QtGui.QVBoxLayout(self.widgets.gpx_editor)
        layout_gpx_editor.addWidget(self.widgets.gpx_reformat_button)
        layout_gpx_editor.addWidget(self.widgets.gpx_edit_box)

        self.widgets.centre_tab.addTab(self.widgets.map_graph_splitter, 'Map and graph')
        self.widgets.centre_tab.addTab(self.widgets.gpx_editor, 'GPX editor')
        
        layout_main_window = qt.QtGui.QHBoxLayout(self.widgets.mainwindow_central)
        layout_main_window.addWidget(self.widgets.main_window_splitter)
        self.widgets.mainwindow_central.setLayout(layout_main_window)
        self.setCentralWidget(self.widgets.mainwindow_central)
                
        self.map = self.widgets.map
        self.graph = self.widgets.graph

        self.map.clear()
        self.graph.clear(axis='off')

    def slot_show_callbacks_dialog(self):
        if not 'callbacks' in self.dialogs:
            self.dialogs['callbacks'] = CallbacksDialog(self)
        self.dialogs['callbacks'].show()
        self.dialogs['callbacks'].activateWindow()
   
    def slot_flip_split_direction(self):
        if self.ui_setup['split_direction'] == 'horizontal':
            new_split_dir = 'vertical'
        elif self.ui_setup['split_direction'] == 'vertical':
            new_split_dir = 'horizontal'
        self.close()
        kws = {'cwd': self.cwds[-1],
               'file': self.file,
               'split_direction': new_split_dir,
               'graph_kws': {'xlim': self.graph.xlim,
                             'ylim': self.graph.ylim}}
        self.__init__(**kws)
   
    def slot_open_track(self):
        dialog = qt.QtGui.QFileDialog()
        dialog.setFileMode(qt.QtGui.QFileDialog.ExistingFile)
        fn = dialog.getOpenFileName(self,
                'Import track file', self.cwds[-1],
                'GPS Exchange Format (*.gpx)'
                )
        self.open_track(fn)
        
    def slot_save_track(self):
        with open(self.file, mode='w') as f:
            f.write(self.track_txt)
        
    def slot_reformat_gpx(self):
        self.track_txt = re.sub(r'><', r'>\n<', self.track_txt)
        self.track_txt = re.sub(r'\n<ele>', r'\n  <ele>', self.track_txt)
        self.track_txt = re.sub(r'\n<time>', r'\n  <time>', self.track_txt)
        self.slot_show_gpx_in_tab()

    def slot_gpx_text_changed(self):
        self.open_gpx_txt(str(self.widgets.gpx_edit_box.document().toPlainText()))
        
    def slot_show_gpx_in_tab(self):
        try:
            self.widgets.gpx_edit_box.textChanged.disconnect(self.slot_gpx_text_changed)
        except:
            pass
        self.widgets.gpx_edit_box.clear()
        self.widgets.gpx_edit_box.insertPlainText(self.track_txt)
        self.widgets.gpx_edit_box.textChanged.connect(self.slot_gpx_text_changed)

    def slot_exit(self):
        self.close()
    
    def slot_about(self):
        QtGui.QMessageBox.about(
                self, 'About ' + program_name, __doc__)
        
    def open_track(self, file):
        file = str(file)
        if not os.path.isfile(file):
            print('Cannot open %s : is not a file.' % file)
            return
        fndir = os.path.split(file)[0]
        if os.path.isdir(fndir):
            self.cwds.append(fndir)
        with open(file, mode='r') as f:
            s = f.read()
        self.file = file
        self.open_gpx_txt(s)
        
        
    def open_gpx_txt(self, text):
        self.track_txt = text
        self.coords = io.read_gpx(StringIO.StringIO(text))
        if self.graph:
            self.graph.xlim = (None, None)
            self.graph.ylim = (None, None)
        self.slot_show_gpx_in_tab()
        self.refresh_figures()
        

    def refresh_figures(self):
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
        
        callbacks = [('link_location', LinkLocationCallback, [self], True),
                     ('link_axes_limits', ChangeLimitsCallback, [self], True)]
        for label, cls, args, connect in callbacks:
            callback = cls(*args)
            if connect:
                callback.connect()
            self.callbacks[label] = callback
        
        self.write_stats()
        self.setWindowTitle('%s : %s' % (program_name, self.file))
   
    def write_stats(self):
        self.stats = stats.Path(self.map.xs, self.map.ys, self.coords[:, 0])
        self.widgets.stats_box.clear()
        self.widgets.stats_box.insertPlainText(str(self.stats))
    
    
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
            if callback.connected:
                cb.setChecked(True)
            else:
                cb.setChecked(False)
        self.setLayout(main_layout)
        self.setWindowTitle('Enable/disable graph features')
        
        
        
class CallbackHandler(object):
    def __init__(self):
        self.name = 'abstract callback handler'
        
    def slot_state_changed(self, state):
        logger.debug('(%s) checkbox state changed' % self.name)
        if state == Qt.Checked:
            logger.debug('(%s) state=checked!' % self.name)
            self.connect()
        elif state == Qt.Unchecked:
            logger.debug('(%s) state=UNchecked!' % self.name)
            self.disconnect()

    
    
class LinkLocationCallback(CallbackHandler):
    def __init__(self, parent):
        CallbackHandler.__init__(self)
        self.parent = parent
        self.connected = False
        self.cid_map = None
        self.cid_graph = None
        self.name = 'Link mouse between map and graph'
        self.status = True
        logger.debug('__init__ LinkLocationCallback')
        
    def connect(self):
        self.cid_map = self.parent.map.canvas.mpl_connect('motion_notify_event', self.on_map_motion)
        self.cid_graph = self.parent.graph.canvas.mpl_connect('motion_notify_event', self.on_graph_motion)
        self.connected = True
        logger.debug('(%s) connected (connected=%s)' % (self.name, self.connected))
        
    def disconnect(self):
        self.parent.map.canvas.mpl_disconnect(self.cid_map)
        self.parent.graph.canvas.mpl_disconnect(self.cid_graph)
        self.connected = False
        logger.debug('(%s) disconnected (connected=%s)' % (self.name, self.connected))
            
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
            # logger.debug('map motion at %s %s!' % (event.xdata, event.ydata))
    
    def on_graph_motion(self, event):
        graph = self.parent.graph
        if event.inaxes is graph.ax or event.inaxes is graph.ax2:
            index = (np.abs(np.array(graph.mpl_dts) - event.xdata)).argmin()
            self.update_markers(index)
            # logger.debug('graph motion i=%s at time %s' % (index, num2date(event.xdata)))
            
    def update_markers(self, i):
        map = self.parent.map
        graph = self.parent.graph
        
        if not 'link_location_marker' in graph.artists:
            graph.artists['link_location_marker'] = graph.ax.plot(
                    [graph.mpl_dts[i]], [graph.speeds[i]], marker='o', mfc='gray', mec='k')[0]
        else:
            graph.artists['link_location_marker'].set_xdata([graph.mpl_dts[i]])
            graph.artists['link_location_marker'].set_ydata([graph.speeds[i]])
            
        if not 'link_location_marker_elev' in graph.artists:
            graph.artists['link_location_marker_elev'] = graph.ax2.plot(
                    [graph.mpl_dts[i]], [graph.elevs[i]], marker='o', mfc='red', mec='k')[0]
        else:
            graph.artists['link_location_marker_elev'].set_xdata([graph.mpl_dts[i]])
            graph.artists['link_location_marker_elev'].set_ydata([graph.elevs[i]])
        
        if not 'link_location_marker' in map.artists:
            map.artists['link_location_marker'] = map.ax.plot(
                    [map.xs[i]], [map.ys[i]], marker='o', mfc='k', mec='k')[0]
        else:
            map.artists['link_location_marker'].set_xdata([map.xs[i]])
            map.artists['link_location_marker'].set_ydata([map.ys[i]])
            
        graph.draw()
        map.draw()
        
        def formatter(index):
            x = map.xs[index]
            y = map.ys[index]
            speed = graph.speeds[index]
            dt = dates.num2date(graph.mpl_dts[index], tz=graph.tz)
            dt_fmt = '%a %Y-%m-%d %H:%M:%S'
            return 'Nearest point: time=%s x=%.2f y=%.2f speed=%.2f' % (
                    dt.strftime(dt_fmt), x, y, speed)
                    
        self.parent.statusbar.showMessage(formatter(i))
        
        

class ChangeLimitsCallback(CallbackHandler):
    def __init__(self, parent):
        logger.debug('__init__ ChangeLimitsCallback')
        self.parent = parent
        self.connected = False
        self.map_cids = []
        self.graph_cids = []
        self.name = 'Auto-adjust map and graph after zooming or panning'
        self.status = True
        
        self.refresh_status = 'inactive'
        self.map_changed = False
        self.map_clicked = False
        self.graph_changed = False
        self.graph_clicked = False
        
    def connect(self):
        self.map_canvas_cids = [
            self.parent.map.canvas.mpl_connect('button_press_event', self.map_mouse_down),
            self.parent.map.canvas.mpl_connect('button_release_event', self.map_mouse_up)]
        self.graph_canvas_cids = [
            self.parent.graph.canvas.mpl_connect('button_press_event', self.graph_mouse_down),
            self.parent.graph.canvas.mpl_connect('button_release_event', self.graph_mouse_up)]
        self.map_ax_cids = [
            self.parent.map.ax.callbacks.connect('xlim_changed', self.map_limits_changed),
            self.parent.map.ax.callbacks.connect('ylim_changed', self.map_limits_changed)]
        self.graph_ax_cids = [
            self.parent.graph.ax.callbacks.connect('xlim_changed', self.graph_limits_changed),
            self.parent.graph.ax.callbacks.connect('ylim_changed', self.graph_limits_changed)]
        self.connected = True
        logger.debug('(%s) connected (connected=%s)' % (self.name, self.connected))
        
    def disconnect(self):
        for cid in self.map_canvas_cids:
            self.parent.map.canvas.mpl_disconnect(cid)
        for cid in self.graph_canvas_cids:
            self.parent.graph.canvas.mpl_disconnect(cid)
        for cid in self.map_ax_cids:
            self.parent.map.ax.callbacks.disconnect(cid)
        for cid in self.graph_ax_cids:
            self.parent.graph.ax.callbacks.disconnect(cid)
        self.connected = False
        del self.map_canvas_cids[0:len(self.map_canvas_cids)]
        del self.map_ax_cids[0:len(self.map_ax_cids)]
        del self.graph_canvas_cids[0:len(self.graph_canvas_cids)]
        del self.graph_ax_cids[0:len(self.graph_ax_cids)]
        logger.debug('(%s) disconnected (connected=%s)' % (self.name, self.connected))
        
    def map_mouse_down(self, event):
        # logger.debug('map_mouse_down')
        if event.inaxes == self.parent.map.ax:
            self.map_clicked = True
        else:
            self.map_clicked = False
    
    def map_mouse_up(self, event):
        # logger.debug('map_mouse_up')
        self.map_clicked = False
        if self.map_changed:
            self.refresh_from_map(check=False)
        
    def graph_mouse_down(self, event):
        # logger.debug('graph_mouse_down')
        if event.inaxes == self.parent.graph.ax:
            self.graph_clicked = True
        else:
            self.graph_clicked = False
                    
    def graph_mouse_up(self, event):
        # logger.debug('graph_mouse_up')
        self.graph_clicked = False
        if self.graph_changed:
            self.refresh_from_graph(check=False)
        
    def map_limits_changed(self, ax):
        # logger.debug('map axes limits changed')
        self.map_changed = True
        self.parent.map.xlim = self.parent.map.ax.get_xlim()
        self.parent.map.ylim = self.parent.map.ax.get_ylim()        
        # The below causes some kind of weird recursive problem. The only need
        # for me to track this is AFAICT with the NavigationToolbar prev/next view
        # buttons.
        
        # self.refresh_from_map(check=True)
        
    def graph_limits_changed(self, ax):
        # logger.debug('graph axes limits changed.')
        self.graph_changed = True
        self.parent.graph.xlim = self.parent.graph.ax.get_xlim()
        self.parent.graph.ylim = self.parent.graph.ax.get_ylim()
        # The below causes some kind of weird recursive problem. The only need
        # for me to track this is AFAICT with the NavigationToolbar prev/next view
        # buttons.
        
        # self.refresh_from_graph(check=True)
    
    def refresh_from_map(self, check=True):
        logger.debug('refresh from map')
        return # TEMPORARILY REMOVE BECAUSE THIS BEHAVIOUR SEEMS ANNOYING TO ME
        map = self.parent.map
        graph = self.parent.graph
        if check and self.map_clicked:
            return
        if self.refresh_status == 'active':
            return
        self.refresh_status = 'active'
        logger.debug('Using changed map lims to refresh graph...')
        xlim = map.ax.get_xlim()
        ylim = map.ax.get_ylim()
        valid_points = (((map.xs >= xlim[0]) & (map.xs <= xlim[1]))
                        & ((map.ys >= ylim[0]) & (map.ys <= ylim[1])))
        mpl_dts = graph.mpl_dts[valid_points]
        speeds = graph.speeds[valid_points]
        if np.any(mpl_dts):
            graph.ax.set_xlim(np.nanmin(mpl_dts), np.nanmax(mpl_dts))
        if np.any(speeds):
            graph.ax.set_ylim(np.nanmin(speeds), np.nanmax(speeds))
        graph.draw()
        self.refresh_status = 'inactive'
        
    def refresh_from_graph(self, check=True):
        logger.debug('refresh from graph')
        map = self.parent.map
        graph = self.parent.graph
        if check and self.graph_clicked:
            return
        if self.refresh_status == 'active':
            return
        self.refresh_status = 'active'
        logger.debug('Using changed graph lims to refresh map...')
        dt_lim = graph.ax.get_xlim()
        speed_lim = graph.ax.get_ylim()
        valid_points = (((graph.mpl_dts >= dt_lim[0]) & (graph.mpl_dts <= dt_lim[1]))
                        & ((graph.speeds >= speed_lim[0]) & (graph.speeds <= speed_lim[1])))
        xs = map.xs[valid_points]
        ys = map.ys [valid_points]
        if np.any(xs):
            map.ax.set_xlim(np.nanmin(xs), np.nanmax(xs))
            map.ax.set_ylim(np.nanmin(ys), np.nanmax(ys))
        map.draw()
        self.refresh_status = 'inactive'
    
    
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
    def __init__(self, width, height, dpi=72, xlim=(None, None), ylim=(None, None)):
        logger.debug('TrackGraph __init__ xlim=%s ylim=%s' % (xlim, ylim))
        QtGui.QWidget.__init__(self)
        self.coords = np.empty(shape=(0, 2))
        self.tz = timezone(config.get('datetime', 'default_timezone'))
        self.xlim = xlim
        self.ylim = ylim
        self.artists = {}
        self.canvas = MplCanvas(self, width=width / float(dpi),
                                height=height / float(dpi), dpi=dpi)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        box = QtGui.QVBoxLayout()
        box.addWidget(self.mpl_toolbar)
        box.addWidget(self.canvas)
        self.setLayout(box)
        
        tz_combo = ExtendedCombo(self.canvas.toolbar)
        tz_model = QtGui.QStandardItemModel()
        for i, tz in enumerate(common_timezones):
            item = QtGui.QStandardItem(tz)
            tz_model.setItem(i, 0, item)
        tz_combo.setModel(tz_model)
        tz_combo.setModelColumn(0)
        tz_combo.activated.connect(self.set_tz)
        tz_combo.setCurrentIndex(common_timezones.index(
                config.get('datetime', 'default_timezone')))
        self.canvas.toolbar.addWidget(tz_combo)
        
    def set_tz(self, index):
        self.tz = timezone(common_timezones[index])
        logger.debug('set_tz index=%d tz=%s' % (index, self.tz))
        self.clear(axis='on')
        self.plot()
        
    def plot(self):
        if 'line' in self.artists:
            self.artists['line'].remove()
            del self.artists['line']
        xs, ys = core.convert_coordinate_system(
                self.coords[:, 1], self.coords[:, 2], epsg2='28353')
        speeds = core.speed(self.coords[:, 0], xs, ys)
        epoch_times = self.coords[:, 0]
        utc = timezone('UTC')
        dts = [datetime.datetime.fromtimestamp(et) for et in epoch_times]
        utc_dts = [utc.localize(dt) for dt in dts]
        dts_localised = [dt.astimezone(self.tz) for dt in utc_dts]
        logger.debug('localised dt[0] = %s (self.tz=%s)' % (dts_localised[0], self.tz))
        
        mpl_dts = np.array(dates.date2num(dts_localised))
        self.artists['line'] = self.ax.plot_date(
                mpl_dts, speeds, ls='-', color='k', marker='None', tz=self.tz)[0]
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        self.ax.fmt_xdata = dates.DateFormatter(dt_fmt, tz=self.tz)
        
        min_mpl_dts = np.nanmin(mpl_dts)
        max_mpl_dts = np.nanmax(mpl_dts)
        range_mpl_dts = max_mpl_dts - min_mpl_dts
        
        min_speed = np.nanmin(speeds)
        max_speed = np.nanmax(speeds)
        range_speed = max_speed - min_speed
        
        x0, x1 = self.xlim
        y0, y1 = self.ylim
        if x0 is None:
            x0 = min_mpl_dts - range_mpl_dts * 0.05
        if x1 is None:
            x1 = max_mpl_dts + range_mpl_dts * 0.05
        if y0 is None:
            y0 = min_speed - range_speed * 0.05
        if y1 is None:
            y1 = max_speed + range_speed * 0.05
            
        self.ax.set_xlim(x0, x1)
        self.ax.set_ylim(y0, y1)
        
        self.xlim = (x0, x1)
        self.ylim = (y0, y1)
        
        self.mpl_dts = mpl_dts
        self.speeds = speeds
        self.elevs = self.coords[:, 3]
        self.artists['line_elev'] = self.ax2.plot_date(
                mpl_dts, self.elevs, ls='-', color='r', 
                marker='None', tz=self.tz)[0]
        self.draw()
    
    def clear(self, axis='off'):
        for artist in self.artists.values():
            artist.remove()
        self.artists.clear()
        if 'ax' in self.__dict__:
            self.canvas.fig.delaxes(self.ax)
        if 'ax2' in self.__dict__:
            self.canvas.fig.delaxes(self.ax2)
        self.ax = self.canvas.fig.add_axes([0.05, 0.1, 0.85, 0.94])
        self.ax2 = self.ax.twinx()
        self.ax.axis(axis)
        self.ax2.axis(axis)
        for ax in (self.ax, self.ax2):
            ax.set_aspect(aspect='auto', adjustable='datalim')
        
    def draw(self):
        self.canvas.draw_idle()
       
       
       
def get_parser():
    parser = argparse.ArgumentParser(
            description='Pyxie Track Editor',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', nargs='?', default=None)
    return parser
    
    
def main():
    args = get_parser().parse_args(sys.argv[1:])
    
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    kwargs = {'file': args.file}
    
    app = QtGui.QApplication([])
    app.setApplicationName(program_name)
    app.setStyle(QtGui.QStyleFactory.create('GTK'))
    app.setPalette(QtGui.QApplication.style().standardPalette())
    window = TrackEditorMainWindow(**kwargs)
    window.show()
    sys.exit(app.exec_())

    
if __name__ == '__main__':
    main()
