from dataclasses import dataclass


@dataclass
class GameConfig:
    delivery_weeks: int = 2
    out_of_stock_penalty: int = 2
    inventory_penalty: int = 1
    init_inventory: int = 12


CONFIG = GameConfig()
