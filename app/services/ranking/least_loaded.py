from app.services.ranking.base import RankingStrategy


class LeastLoadedStrategy(RankingStrategy):
    name = "least_loaded"

    def rank(self, course, candidates):
        # most hours left first, ties go to experienced TAs
        return sorted(candidates, key=lambda c: (-c.hours_left(), not c.prior_experience, c.ta_id))