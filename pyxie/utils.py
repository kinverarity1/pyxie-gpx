class NamedDict(dict):
    def __init__(self, **kwargs):
        for key, value in kwargs:
            setattr(self, key, value)