from typing import Optional

from .adapter import DataAdapter
from .models import GAME_TEMPLATE, ORDER_TEMPLATE, STAT_TEMPLATE


class DictDBAdapter(DataAdapter):
    def __init__(self):
        self.data = {"stat": {}, "order": {}}

    def saveStat(self, identifier, week, inventory, cost, out_of_stock):
        pk = (identifier, week)
        self.data["stat"].setdefault(pk, STAT_TEMPLATE())
        self.data["stat"][pk]["inventory"] = inventory
        self.data["stat"][pk]["cost"] = cost
        self.data["stat"][pk]["out_of_stock"] = out_of_stock

    def saveOrder(self, order, week, game, player, role):
        pk = ((game, player, role), week)
        self.data["order"].setdefault(pk, ORDER_TEMPLATE())
        self.data["order"][pk]["buy"] = order

    def saveDelivery(self, delivery, week, game, player, role):
        pk = ((game, player, role), week)
        self.data["order"].setdefault(pk, ORDER_TEMPLATE())
        self.data["order"][pk]["delivery"] = delivery

    def getStat(self, identifier: tuple, week: int) -> dict:
        pk = (identifier, week)
        return self.data["stat"].get(pk, STAT_TEMPLATE())

    def getOrder(self, identifier: tuple, week: int) -> int:
        pk = (identifier, week)
        return self.data["order"].get(pk, ORDER_TEMPLATE())["buy"]

    def getDashboard(self, game: str) -> dict:
        gameInfo = self.data.setdefault(game, GAME_TEMPLATE())
        return gameInfo

    def getDelivery(self, identifier: tuple, week: int) -> int:
        pk = (identifier, week)
        return self.data["order"].get(pk, ORDER_TEMPLATE())["delivery"]

    def createGame(self, game: str):
        self.data[game] = GAME_TEMPLATE()

    def removeGame(self, game: str):
        self.data.pop(game, None)
        for table in ["stat", "order"]:
            for k in list(self.data[table].keys()):
                ((g, _, _), _) = k
                if g == game:
                    del self.data[table][k]

    def addPlayer(self, game: str, player: str, role: str):
        gameInfo = self.data.setdefault(game, GAME_TEMPLATE())
        gameInfo["players"].setdefault(
            player, {"shop": False, "retailer": False, "factory": False}
        )
        gameInfo["players"][player][role] = True

    def getPlayers(self, game: str) -> dict:
        gameInfo = self.data.setdefault(game, GAME_TEMPLATE())
        return gameInfo["players"]

    def incrWeek(self, game: str):
        gameInfo = self.data.setdefault(game, GAME_TEMPLATE())
        gameInfo["week"] += 1

    def find_all_stats(self, game: str, player: str, role: str) -> list[dict]:
        result = []
        for (identifier, week), stat in self.data["stat"].items():
            if identifier == (game, player, role):
                result.append({**stat, "week": week})
        return result

    def getOrderByWeek(
        self, game: str, start_week: int, end_week: Optional[int] = None
    ) -> dict[int, dict[str, dict[str, dict[str, int]]]]:
        end_week = end_week or start_week
        ret: dict[int, dict[str, dict[str, dict[str, int]]]] = {}
        players = self.getPlayers(game)

        for week in range(start_week, end_week + 1):
            ret[week] = {}
            for p, roles in players.items():
                ret[week][p] = {}
                for role, v in roles.items():
                    if not v:
                        continue
                    pk = ((game, p, role), week)
                    ret[week][p][role] = self.data["order"].get(pk, {})

        return ret
