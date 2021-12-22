
class HirearchicalDict(dict):
    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super().__setitem__(key, value)
        else:
            pass
