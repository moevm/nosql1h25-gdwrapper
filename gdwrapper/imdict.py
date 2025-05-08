class imdict(dict):

    def __hash__(self):
        return int(self.get('_id'), 16)
    
    def __eq__(self, other):
        return self.get('id') == other.get('id')

    def _immutable(self, *args, **kws):
        raise TypeError('object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear       = _immutable
    update      = _immutable
    setdefault  = _immutable
    pop         = _immutable
    popitem     = _immutable