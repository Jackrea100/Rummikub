from typing import List
from Tile import Tile
from Rack import Rack
from Board import Board
from Meld import Meld


class Player:
    def __init__(self, name: str):
        # Corrected: Player starts with an empty, new rack
        self.name: str = name
        self.rack: Rack = Rack([])
        self.has_made_initial_meld: bool = False

    def __repr__(self) -> str:
        return f"Player({self.name}, {len(self.rack)} tiles, initial meld: {'Yes' if self.has_made_initial_meld else 'No'})"

    def draw_initial_hand(self, tiles: List[Tile]):
        # Logic to add all starting tiles to the rack
        for tile in tiles:
            self.rack.add_tile(tile)

    def draw_tile(self, tile: Tile):
        # Simple wrapper to add a single tile
        self.rack.add_tile(tile)

    def play_turn(self, board: Board) -> List[Meld] | None:
        """
        PLACEHOLDER: This method will call the Solver and process the result.

        It should return:
        - List[Meld]: The new board state (melds) if a move was made.
        - None: If no move was made (signaling the Game loop to draw a tile).
        """
        print(f"It's {self.name}'s turn! The Solver needs to run here.")
        # Eventually: return Solver().find_best_move(...)
        return None