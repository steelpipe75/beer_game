from abc import ABC, abstractmethod
from typing import Optional


class DataAdapter(ABC):
    @abstractmethod
    def saveStat(self, identifier, week, inventory, cost, out_of_stock):
        pass

    @abstractmethod
    def saveOrder(self, order, week, game, player, role):
        pass

    @abstractmethod
    def saveDelivery(self, delivery, week, game, player, role):
        pass

    @abstractmethod
    def getStat(self, identifier: tuple, week: int) -> dict:
        pass

    @abstractmethod
    def getOrder(self, identifier: tuple, week: int) -> int:
        pass

    @abstractmethod
    def getDashboard(self, game: str) -> dict:
        pass

    @abstractmethod
    def getDelivery(self, identifier: tuple, week: int) -> int:
        pass

    @abstractmethod
    def createGame(self, game: str):
        pass

    @abstractmethod
    def removeGame(self, game: str):
        pass

    @abstractmethod
    def addPlayer(self, game: str, player: str, role: str):
        pass

    @abstractmethod
    def getPlayers(self, game: str) -> dict:
        pass

    @abstractmethod
    def incrWeek(self, game: str):
        pass

    @abstractmethod
    def getOrderByWeek(
        self, game: str, start_week: int, end_week: Optional[int] = None
    ) -> dict[int, dict[str, dict[str, dict[str, int]]]]:
        pass
