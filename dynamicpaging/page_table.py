class PageTableEntry:
    """页表项：valid、frame、modified"""
    def __init__(self, valid=False, frame=None, modified=False):
        self.valid = valid
        self.frame = frame
        self.modified = modified