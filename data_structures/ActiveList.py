class EntryRecord:
    def __init__(self, logical_dest, old_dest, pc, done=False, exception=False):
        self.done = done
        self.exception = exception
        self.logical_dest = logical_dest
        self.old_dest = old_dest
        self.pc = pc

    def to_dict(self):
        return {
            "Done": self.done,
            "Exception": self.exception,
            "LogicalDestination": self.logical_dest,
            "OldDestination": self.old_dest,
            "PC": self.pc
        }
