from app.services.ranking.base import RankingStrategy


class RoundRobinStrategy(RankingStrategy):
    name = "round_robin"

    def __init__(self):
        self.cursor = 0

    def rank(self, course, candidates):
        if len(candidates) == 0:
            return []
        ordered = sorted(candidates, key=lambda c: c.ta_id)
        start = self.cursor % len(ordered)
        self.cursor += 1
        return ordered[start:] + ordered[:start]