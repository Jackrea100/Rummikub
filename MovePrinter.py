from typing import List
from collections import Counter
from Meld import Meld
from Rack import Rack
from Board import Board


class MovePrinter:
    """
    A helper class to explain the difference between the game state
    before and after a move.
    """

    @staticmethod
    def print_move_guide(old_rack: Rack, old_board: Board, new_melds: List[Meld]):
        print(f"\n{'-' * 15} MOVE GUIDE {'-' * 15}")

        # --- Part 1: What did I play? ---
        old_board_tiles = old_board.get_all_tiles()
        new_board_tiles = [t for meld in new_melds for t in meld.tiles]

        old_board_counter = Counter(old_board_tiles)
        new_board_counter = Counter(new_board_tiles)

        new_board_counter.subtract(old_board_counter)

        played_from_rack = []
        for tile, count in new_board_counter.items():
            if count > 0:
                played_from_rack.extend([tile] * count)

        played_from_rack.sort()

        if not played_from_rack:
            print("👉 No tiles played from rack (Rearrangement only?)")
        else:
            print(f"👉 PLAY these tiles from your Rack: {played_from_rack}")

        # --- Part 2: How does the board look now? ---

        print("\n👉 FORM this new Board Configuration:")

        # IMPROVED COMPARISON: Use sets of tiles instead of strings.
        # This handles cases where [R1, R2, R3] becomes [R3, R2, R1] gracefully.
        old_meld_sets = [frozenset(m.tiles) for m in old_board.melds]

        for i, meld in enumerate(new_melds, 1):
            # Check if the set of tiles in this new meld existed in the old board
            if frozenset(meld.tiles) in old_meld_sets:
                print(f"   {i}. {meld} (Unchanged)")
            else:
                print(f"   {i}. {meld} *** NEW / MODIFIED ***")

        print(f"{'-' * 42}\n")