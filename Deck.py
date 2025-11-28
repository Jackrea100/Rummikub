import random
from typing import List, Optional
from Tile import Tile


class Deck:
    COLORS = ["Red", "Orange", "Blue", "Black"]
    VALUES = list(range(1, 14))
    NUM_SETS = 2
    NUM_JOKERS = 2

    def __init__(self):
        self.tiles: List[Tile] = []

        # Add Jokers first
        for _ in range(self.NUM_JOKERS):
            self.tiles.append(Tile(is_joker=True))

        # Add all 104 standard tiles
        for color in self.COLORS:
            for val in self.VALUES:
                for _ in range(self.NUM_SETS):
                    self.tiles.append(Tile(color, val))

        self.shuffle()  # Shuffle immediately after creation

    def __len__(self):
        return len(self.tiles)

    def shuffle(self):
        random.shuffle(self.tiles)

    def draw_tile(self) -> Tile | None:
        # Pythonic one-liner to pop if not empty, otherwise return None
        return self.tiles.pop() if self.tiles else None

    def draw_initial_hand(self, num_tiles: int = 14) -> List[Tile]:
        """
        Draws tiles, safely stopping if the deck runs out.
        """
        hand = []
        for _ in range(num_tiles):
            tile = self.draw_tile()
            if tile:
                hand.append(tile)
            else:
                break
        return hand