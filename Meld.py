from typing import List, Optional
from itertools import combinations
from Tile import Tile
from collections import defaultdict  # Needed for run validation setup


class Meld:
    def __init__(self, tiles: List[Tile]):
        self.tiles = tiles

    def __repr__(self):
        return f"Meld: {self.tiles}"

    def __iter__(self):
        """
        Allows the Meld to be treated like a list/sequence.
        Enables: set(meld), list(meld), for tile in meld
        """
        return iter(self.tiles)

    def is_valid(self) -> bool:
        """
        The 'Traffic Cop' method. Checks if a list of tiles forms a single,
        valid Rummikub set (Group or Run).
        """
        tiles = self.tiles

        # 1. Minimum Size Check (Already filtered out many small lists)
        if len(tiles) < 3:
            return False

        tiles.sort()  # Sorts tiles in place

        # Separate Jokers and real tiles
        jokers = [t for t in tiles if t.is_joker]
        real_tiles = [t for t in tiles if not t.is_joker]
        num_jokers = len(jokers)

        # 2. Defensive Check: Must have at least one real tile
        if not real_tiles:
            return False

        # --- Traffic Cop Routing ---

        # Check if all real tiles have the same value (Group Candidate)
        is_group_candidate = (len(set(t.val for t in real_tiles)) == 1)

        if is_group_candidate:
            # Send to Group validation
            return self._group(real_tiles, num_jokers)

        else:
            # If not a Group, it must try to be a Run
            # We must check the Run condition here to ensure it's not a garbage list
            is_run_candidate = (len(set(t.color for t in real_tiles)) == 1)

            if is_run_candidate:
                # Send to Run validation
                return self._run(real_tiles, num_jokers)

            return False  # Failed both Group and Run checks

    # --- Internal Validation Helpers ---
    @staticmethod
    def _group(real_tiles: List[Tile], num_jokers: int) -> bool:
        # 1. Total Size Check (Max 4 tiles)
        if len(real_tiles) + num_jokers not in [3, 4]:
            return False

        # 2. Unique Colors Check
        colors = [t.color for t in real_tiles]
        if len(colors) != len(set(colors)):
            return False  # Duplicate color found

        return True

    @staticmethod
    def _run(real_tiles: List[Tile], num_jokers: int) -> bool:
        # 1. Duplicate Number Check (Must not have R5 and R5, handled by the traffic cop)
        # 2. Calculate Gaps (Consecutive sequence check)

        values = [t.val for t in real_tiles]
        needed_jokers = 0

        # Check for gaps between real tiles
        for i in range(len(values) - 1):
            gap = values[i + 1] - values[i]

            if gap == 0:
                return False  # Duplicate value found in a run

            # gap of 1 (5->6) needs 0 jokers. gap of 2 (5->7) needs 1 joker.
            needed_jokers += (gap - 1)

        # 3. Check Joker Sufficiency
        if num_jokers >= needed_jokers:
            return True  # Valid Run

        return False

    def is_run(self) -> bool:
        # Simple check: Are colors same?
        if not self.tiles: return False
        # Filter jokers
        real = [t for t in self.tiles if not t.is_joker]
        if not real: return True  # All jokers are ambiguous, treat as run?
        return len(set(t.color for t in real)) == 1