"""Per-world prediction cache shared by physical scheduling strategies."""
class PredictionCache:
    def __init__(self):
        self.slot_anchor = None
        self.slot_times = {}
        self.sunlit = {}
