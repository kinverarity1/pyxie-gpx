from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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
    '''QMainWindow wrapper -- see :class:`ActionHandler`.'''
    def __init__(self, *args, **kwargs):
        ActionHandler.__init__(self)
        QtGui.QMainWindow.__init__(self, *args, **kwargs)

        

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
                
                

                
def debug(item):
    print item.column(), item.row(), item.text()