import sys

from PyQt4.QtGui import QApplication

from _windows import PyxieMainWindow


def main():
    return main_func(sys.argv[1:])
    

def main_func(args):
    app = QApplication([])
    main_window = PyxieMainWindow()
    main_window.show()
    sys.exit(app.exec_())

    
if __name__ == '__main__':
    main()