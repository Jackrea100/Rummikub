from typing import List
from Tile import Tile
from collections import Counter  # For potentially advanced methods


class Rack:
    def __init__(self, initial_tiles: List[Tile]):
        self.tiles: List[Tile] = sorted(initial_tiles)

    def __repr__(self):
        return f"Rack: {self.tiles}"

    def __len__(self) -> int:
        return len(self.tiles)

    def __contains__(self, tile: Tile) -> bool:
        # Allows for 'if tile in rack:' syntax
        return tile in self.tiles

    def add_tile(self, tile: Tile):
        self.tiles.append(tile)
        self.tiles.sort()  # Correctly sorts in place

    def remove_tiles(self, tiles_to_remove: List[Tile]) -> bool:
        """
        Robustly removes a list of tiles, handling duplicates.
        """
        # Create a temporary copy to test the removal (CRUCIAL)
        rack_backup = self.tiles[:]

        for tile in tiles_to_remove:
            # This relies on the Tile object equality to find and remove
            # the *first* matching instance, correctly tracking counts.
            try:
                rack_backup.remove(tile)
            except ValueError:
                # Tile was not found, so the move is invalid.
                return False

        # If loop finishes, update the actual rack
        self.tiles = rack_backup
        self.tiles.sort()
        return True

    def get_points_val(self) -> int:
        """
        Calculates the total point value of tiles left on the rack (end-game scoring).
        Uses the simpler logic since Jokers have val=30.
        """
        # The '# noinspection PyTypeChecker' comment is used here to silence the false positive
        # noinspection PyTypeChecker
        return sum(t.val for t in self.tiles if t.val is not None)