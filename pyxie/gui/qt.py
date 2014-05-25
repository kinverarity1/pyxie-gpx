import logging
import os

from PyQt4 import QtCore, QtGui

Qt = QtCore.Qt

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .. import utils


logger = logging.getLogger(__name__)

QtCore.QCoreApplication.setOrganizationName('pyxie')
QtCore.QCoreApplication.setOrganizationDomain('pyxie.com')


class ActionHandler(object):
    '''A base class for Qt widgets, to make it easy to handle adding actions.

    Intended to be inherited, not instantiated directly.

    '''
    def create_action(self, text, slot=None, shortcut=None, icon=None,
                      tip=None, checkable=False, signal='triggered'):
        '''Add an action.
        
        Args:
            - *icon*: filename
            - *shortcut*: str e.g. <Ctrl-W>
            - *slot*: function or method
            - *tip*: string
            - *checkable*: bool
            - *signal*: attribute of the action
            
        '''
        action = QtGui.QAction(text, self)
        if icon:
            action.setIcon(QtGui.QIcon(":/%s.png" % icon))
        if shortcut:
            action.setShortcut(shortcut)
        if tip:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if checkable:
            action.setCheckable(True)
        if slot and signal:
            getattr(action, signal).connect(slot)
        return action
    
    def add_actions(self, target, actions):
        '''Add actions to a target, like a ToolBar or Menu.

        Args:
            - *target*: should have an addSeparator() and addAction(action)
              methods.
            - *actions*: iterable sequence containing QActions

        '''
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

                

class Widget(ActionHandler, QtGui.QWidget):
    '''QWidget wrapper -- see :class:`ActionHandler`.'''
    def __init__(self, *args, **kwargs):
        ActionHandler.__init__(self)
        QtGui.QWidget.__init__(self, *args, **kwargs)

                
                
class MainWindow(ActionHandler, QtGui.QMainWindow):
    '''QMainWindow wrapper -- see :class:`ActionHandler`.

    '''
    def __init__(self, app_name='Application', **kwargs):
        self.app_name = app_name
        ActionHandler.__init__(self)
        QtGui.QMainWindow.__init__(self, **kwargs)
        

    def init_settings(self):
        try:
            self.restore_settings()
        except:
            utils.skip_exception('Failed to restore QSettings')


    def restore_settings(self):
        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value('geometry'))
        self.restoreState(settings.value('windowState'))
        # self.area.restoreState(settings.value('dockState'))
        

    def remember_settings(self):
        settings = QtCore.QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        # settings.setValue('dockState', self.area.saveState())
        

    def closeEvent(self, event):
        self.remember_settings()
        QtGui.QMainWindow.closeEvent(self, event)
        

    def set_title_message(self, message):
        self.setWindowTitle('%s - %s' % (self.app_name, message))

        

class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=2, height=2, dpi=100, frameon=True):
        self.fig = Figure(figsize=(width, height), dpi=dpi, frameon=frameon)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
                
                

class ExtendedCombo(QtGui.QComboBox):
    '''Taken from http://stackoverflow.com/a/4829759/596328'''
    def __init__(self, parent=None):
        super(ExtendedCombo, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.completer = QtGui.QCompleter(self)
        self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
        self.pFilterModel = QtGui.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setPopup(self.view())
        self.setCompleter(self.completer)
        self.lineEdit().textEdited[unicode].connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.setTextIfCompleterIsClicked)

    def setModel(self, model):
        super(ExtendedCombo, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedCombo, self).setModelColumn(column)

    def view(self):
        return self.completer.popup()

    def index(self):
        return self.currentIndex()

    def setTextIfCompleterIsClicked(self, text):
      if text:
        index = self.findText(text)
        self.setCurrentIndex(index)
