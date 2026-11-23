from abc import ABC, abstractmethod


class RankingStrategy(ABC):
    name = ""

    @abstractmethod
    def rank(self, course, candidates):
        pass
