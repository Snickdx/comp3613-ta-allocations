class StrategyRegistry:
    def __init__(self):
        self.strategies = {}

    def register(self, strategy):
        self.strategies[strategy.name] = strategy

    def get(self, mode):
        if mode not in self.strategies:
            raise ValueError("unknown mode: " + mode)
        return self.strategies[mode]

    def names(self):
        return list(self.strategies.keys())
