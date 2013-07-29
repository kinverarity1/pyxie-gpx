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
                
                

class ExtendedCombo(QtGui.QComboBox):
    def __init__(self, parent=None):
        super(ExtendedCombo, self).__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable( True )

        self.setEditable( True )
        self.completer = QtGui.QCompleter( self )

        # always show all completions
        self.completer.setCompletionMode( QtGui.QCompleter.UnfilteredPopupCompletion )
        self.pFilterModel = QtGui.QSortFilterProxyModel( self )
        self.pFilterModel.setFilterCaseSensitivity( Qt.CaseInsensitive )



        self.completer.setPopup( self.view() )


        self.setCompleter( self.completer )


        self.lineEdit().textEdited[unicode].connect( self.pFilterModel.setFilterFixedString )
        self.completer.activated.connect(self.setTextIfCompleterIsClicked)

    def setModel( self, model ):
        super(ExtendedCombo, self).setModel( model )
        self.pFilterModel.setSourceModel( model )
        self.completer.setModel(self.pFilterModel)

    def setModelColumn( self, column ):
        self.completer.setCompletionColumn( column )
        self.pFilterModel.setFilterKeyColumn( column )
        super(ExtendedCombo, self).setModelColumn( column )


    def view( self ):
        return self.completer.popup()

    def index( self ):
        return self.currentIndex()

    def setTextIfCompleterIsClicked(self, text):
      if text:
        index = self.findText(text)
        self.setCurrentIndex(index)
