import traceback
import logging

logger = logging.getLogger(__name__)



class NamedDict(dict):
    def __init__(self, **kwargs):
        for key, value in kwargs:
            setattr(self, key, value)


def skip_exception(message='<-- no message included -->', func=None):
    if func is None:
        func = logger.warning
    func('The below exception has been caught and ignored:\n%s\n%s'
         % (message, traceback.format_exc()))            