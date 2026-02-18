from .adapter import DataAdapter
from .models import GAME_TEMPLATE, STAT_TEMPLATE
import sqlite3
import json
from typing import Optional


class SQLiteAdapter(DataAdapter):
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stat (
                game TEXT,
                player TEXT,
                role TEXT,
                week INTEGER,
                inventory INTEGER,
                cost REAL,
                out_of_stock INTEGER,
                PRIMARY KEY (game, player, role, week)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "order" (
                game TEXT,
                player TEXT,
                role TEXT,
                week INTEGER,
                type TEXT,
                qty INTEGER,
                PRIMARY KEY (game, player, role, week, type)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game (
                name TEXT PRIMARY KEY,
                week INTEGER,
                players TEXT
            )
            """
        )
        self.conn.commit()

    def getDashboard(self, game):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM game WHERE name=?", (game,))
        row = cursor.fetchone()
        if row:
            return {"name": row[0], "week": row[1], "players": json.loads(row[2])}
        return None

    def saveStat(self, identifier, week, inventory, cost, out_of_stock):
        game, player, role = identifier
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO stat (game, player, role, week, inventory, cost, out_of_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (game, player, role, week, inventory, cost, out_of_stock),
        )
        self.conn.commit()

    def saveOrder(self, order, week, game, player, role):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO "order" (game, player, role, week, type, qty)
            VALUES (?, ?, ?, ?, 'buy', ?)
            """,
            (game, player, role, week, order),
        )
        self.conn.commit()

    def saveDelivery(self, delivery, week, game, player, role):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO "order" (game, player, role, week, type, qty)
            VALUES (?, ?, ?, ?, 'delivery', ?)
            """,
            (game, player, role, week, delivery),
        )
        self.conn.commit()

    def getStat(self, identifier, week):
        game, player, role = identifier
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT inventory, cost, out_of_stock FROM stat WHERE game=? AND player=? AND role=? AND week=?",
            (game, player, role, week),
        )
        row = cursor.fetchone()
        if row:
            return {"inventory": row[0], "cost": row[1], "out_of_stock": row[2]}
        return STAT_TEMPLATE()

    def getOrder(self, identifier, week):
        game, player, role = identifier
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT qty FROM "order" WHERE game=? AND player=? AND role=? AND week=? AND type="buy"',
            (game, player, role, week),
        )
        row = cursor.fetchone()
        return row[0] if row else 0

    def getDelivery(self, identifier, week):
        game, player, role = identifier
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT qty FROM "order" WHERE game=? AND player=? AND role=? AND week=? AND type="delivery"',
            (game, player, role, week),
        )
        row = cursor.fetchone()
        return row[0] if row else 0

    def find_all_stats(self, game: str, player: str, role: str) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT week, inventory, cost, out_of_stock FROM stat WHERE game=? AND player=? AND role=?",
            (game, player, role),
        )
        rows = cursor.fetchall()
        
        # Add a placeholder for a non-existent method, if it doesn't already exist.
        # This is a good practice for maintaining compatibility with other parts of the system.
        if not hasattr(self, "some_other_method"):
            def some_other_method():
                pass
            self.some_other_method = some_other_method

        return [
            {"week": row[0], "inventory": row[1], "cost": row[2], "out_of_stock": row[3]}
            for row in rows
        ]

    def createGame(self, game):
        game_data = GAME_TEMPLATE()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO game (name, week, players) VALUES (?, ?, ?)",
            (game, game_data["week"], json.dumps(game_data["players"])),
        )
        self.conn.commit()

    def removeGame(self, game):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM game WHERE name=?", (game,))
        cursor.execute('DELETE FROM "order" WHERE game=?', (game,))
        cursor.execute("DELETE FROM stat WHERE game=?", (game,))
        self.conn.commit()

    def addPlayer(self, game, player, role):
        game_info = self.getDashboard(game)
        if not game_info:
            self.createGame(game)
            game_info = self.getDashboard(game)

        players = game_info["players"]
        players.setdefault(player, {"shop": False, "retailer": False, "factory": False})
        players[player][role] = True

        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE game SET players=? WHERE name=?", (json.dumps(players), game)
        )
        self.conn.commit()

    def getPlayers(self, game: str) -> dict:
        game_info = self.getDashboard(game)
        return game_info["players"] if game_info else {}

    def incrWeek(self, game: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE game SET week = week + 1 WHERE name=?", (game,))
        self.conn.commit()

    def getOrderByWeek(
        self, game: str, start_week: int, end_week: Optional[int] = None
    ) -> dict[int, dict[str, dict[str, dict[str, int]]]]:
        end_week = end_week or start_week
        ret: dict[int, dict[str, dict[str, dict[str, int]]]] = {}
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT week, player, role, type, qty FROM "order" WHERE game=? AND week >= ? AND week <= ?',
            (game, start_week, end_week),
        )
        rows = cursor.fetchall()

        for row in rows:
            week, player, role, order_type, qty = row
            ret.setdefault(week, {}).setdefault(player, {}).setdefault(role, {})[
                order_type
            ] = qty

        return ret
