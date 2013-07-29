import datetime
import logging
import os

from matplotlib import dates
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from pytz import timezone, all_timezones, common_timezones

from pyxie import io
from pyxie import core
from pyxie.gui.qt import QtGui, QtCore, Qt, MainWindow, MplCanvas, ExtendedCombo



program_name = 'Pyxie Track Editor'
program_version = '0.1'
callbacks = [('link_location', 'Link location on map and graph', True)]
default_tz = 'Australia/Adelaide'

logger = logging.getLogger(__name__)



        
class TrackEditorMainWindow(MainWindow):
    def __init__(self, split_direction='horizontal', track_fn=None, 
                 graph_kws=None):
        MainWindow.__init__(self)
        logger.debug('__init__ split_direction=%s track_fn=%s' % (
                split_direction, track_fn))
        self.track_fn = track_fn
        self.dialogs = {}
        self.callbacks = {}
        self.split_direction = split_direction
        self.init_ui(split_direction=split_direction,
                     graph_kws=graph_kws)
        if track_fn:
            self.open_track(track_fn)
                
        
    def init_ui(self, split_direction='horizontal', graph_kws=None):
        if graph_kws is None:
            graph_kws = {}
        self.split_direction = split_direction
            
        open_track = self.create_action(text='Open track...', shortcut='Ctrl+O', slot=self.slot_open_track)
        # show_callbacks_dialog = self.create_action(text='Enable/disable graph features...', slot=self.slot_show_callbacks_dialog)
        set_gui_style = self.create_action(text='Flip orientation', slot=self.slot_flip_gui_direction)
        exit = self.create_action(text='E&xit', shortcut='Alt+F4', slot=self.slot_exit)
        about = self.create_action(text='&About...', shortcut='F1', slot=self.slot_about)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        view_menu = menubar.addMenu('&View')
        help_menu = menubar.addMenu('&Help')
        self.add_actions(file_menu, [open_track, exit])
        self.add_actions(view_menu, [set_gui_style])
        self.add_actions(help_menu, [about])
        
        main_widget = QtGui.QWidget(self)
        main_layout = QtGui.QVBoxLayout(main_widget)
        
        self.map = TrackMap(5, 5)
        self.graph = TrackGraph(5, 5, **graph_kws)
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
        
        self.statusbar = QtGui.QStatusBar(self)
        self.setStatusBar(self.statusbar)
        
        self.show()
        
    def slot_show_callbacks_dialog(self):
        if not 'callbacks' in self.dialogs:
            self.dialogs['callbacks'] = CallbacksDialog(self)
        self.dialogs['callbacks'].show()
        self.dialogs['callbacks'].activateWindow()
   
    def slot_flip_gui_direction(self):
        logger.debug('flipping gui direction')
        if self.split_direction == 'horizontal':
            new_split_dir = 'vertical'
        elif self.split_direction == 'vertical':
            new_split_dir = 'horizontal'
        self.close()
        self.__init__(split_direction=new_split_dir, 
                      track_fn=self.track_fn,
                      graph_kws=dict(xlim=self.graph.xlim,
                                     ylim=self.graph.ylim))
   
    def slot_open_track(self):
        logger.debug('Asking for track fn')
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        fn = dialog.getOpenFileName(self,
                'Import track file', os.getcwd(),
                'GPS Exchange Format (*.gpx)'
                )
        return self.open_track(fn)
        
    def open_track(self, fn):
        logger.debug('Opening track_fn' % fn)
        if not os.path.isfile(fn):
            return
        self.track_fn = fn
        self.coords = io.read_gpx(fn)
        logger.info('Read %d points from %s' % (self.coords.shape[0], fn))
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
        logger.debug('Mapping %s' % self.track_fn)
        
        callbacks = [('link_location', LinkLocationCallback, [self], True),
                     ('link_axes_limits', ChangeLimitsCallback, [self], True)]
        for label, cls, args, connect in callbacks:
            callback = cls(*args)
            if connect:
                callback.connect()
            self.callbacks[label] = callback
        
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
        if event.inaxes is graph.ax:
            index = (np.abs(np.array(graph.mpl_dts) - event.xdata)).argmin()
            self.update_markers(index)
            # logger.debug('graph motion i=%s at time %s' % (index, num2date(event.xdata)))
            
    def update_markers(self, i):
        map = self.parent.map
        graph = self.parent.graph
        
        if not 'link_location_marker' in graph.artists:
            graph.artists['link_location_marker'] = graph.ax.plot(
                    [graph.mpl_dts[i]], [graph.speeds[i]], marker='o', mfc='k', mec='k')[0]
        else:
            graph.artists['link_location_marker'].set_xdata([graph.mpl_dts[i]])
            graph.artists['link_location_marker'].set_ydata([graph.speeds[i]])
        
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
        self.tz = timezone(default_tz)
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
        tz_combo.setCurrentIndex(common_timezones.index(default_tz))
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
                mpl_dts, speeds, ls='-', marker='None', tz=self.tz)[0]
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
    
