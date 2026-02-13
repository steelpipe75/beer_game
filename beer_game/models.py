from .config import CONFIG


def GAME_TEMPLATE():
    return {"week": 0, "players": {}}


def ORDER_TEMPLATE():
    return {"buy": 0, "delivery": 0}


def STAT_TEMPLATE():
    return {
        "inventory": CONFIG.init_inventory,
        "cost": 0,
        "out_of_stock": 0,
    }


def PLAYER_TEMPLATE():
    return {
        "shop": False,
        "retailer": False,
        "factory": False,
    }
