from app.services.constants import WEEKLY_HOUR_CAP


class CapacityGuard:
    def __init__(self, cap=WEEKLY_HOUR_CAP):
        self.cap = cap

    def problem(self, candidate, hours, budget):
        if hours <= 0:
            return "hours must be positive"
        if candidate.hours_used + hours > self.cap:
            return "TA would exceed the " + str(self.cap) + " hour weekly cap"
        if hours > budget:
            return "exceeds department budget"
        return None

    def feasible(self, candidate, hours, budget):
        return self.problem(candidate, hours, budget) is None

    def filter(self, candidates, hours, budget):
        result = []
        for c in candidates:
            if self.feasible(c, hours, budget):
                result.append(c)
        return result