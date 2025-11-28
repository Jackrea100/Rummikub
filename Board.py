from typing import List
from Meld import Meld
from Tile import Tile

class Board:
    def __init__(self):
        self.melds: List[Meld] = []

    def __repr__(self):
        return f"Board ({len(self.melds)} melds): {self.melds}"

    def get_all_tiles(self) -> List[Tile]:
        # The correct Pythonic way to flatten the list of lists
        return [t for meld in self.melds for t in meld.tiles]

    def is_valid_state(self) -> bool:
        # Checks if ALL melds on the board are valid
        return all(meld.is_valid() for meld in self.melds)

    def apply_move(self, new_melds: List[Meld]):
        """
        Replaces the old board state with the new, validated state provided by the solver.
        """
        self.melds = new_melds