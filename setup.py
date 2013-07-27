try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

    
setup(name='pyxie',
      entry_points={'console_scripts': [
                        'pyxie = pyxie.gui.app:main'
                        ],
                    },
      )