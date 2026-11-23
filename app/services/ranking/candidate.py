from app.services.constants import WEEKLY_HOUR_CAP


class Candidate:
    def __init__(self, ta, prior_experience, hours_used):
        self.ta = ta
        self.ta_id = ta.id
        self.prior_experience = prior_experience
        self.hours_used = hours_used

    def hours_left(self):
        return WEEKLY_HOUR_CAP - self.hours_used

    def to_dict(self):
        return {
            "ta_id": self.ta_id,
            "name": self.ta.name,
            "prior_experience": self.prior_experience,
            "weekly_hours_used": self.hours_used,
            "weekly_hours_remaining": self.hours_left(),
        }
