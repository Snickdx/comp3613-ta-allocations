from app.services.ranking.base import RankingStrategy


class ExperienceFirstStrategy(RankingStrategy):
    name = "experience_first"

    def rank(self, course, candidates):
        # experienced first, then most hours left
        return sorted(candidates, key=lambda c: (not c.prior_experience, -c.hours_left(), c.ta_id))
