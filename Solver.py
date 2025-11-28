from itertools import combinations
from typing import List, Optional, Dict, FrozenSet, Tuple
from Tile import Tile
from Rack import Rack
from Board import Board
from Meld import Meld
from collections import defaultdict


class Solver:
    def __init__(self):
        # Cache stores: {frozenset(tiles_to_cover): (best_score, best_meld_list)}
        self.memo: Dict[FrozenSet[Tile], Tuple[int, List[Meld]]] = {}

    def _calculate_meld_score(self, meld: Meld) -> int:
        """
        Calculates the strategic score for a single meld (Heuristic Brain).
        This method must be implemented by the user based on desired strategy.
        """
        # score = len(meld.tiles)  # Base score: tile count
        #
        # # Example Heuristics (User must implement):
        # for tile in meld.tiles:
        #     if tile.val in [10, 11, 12, 13]:  # Risk Aversion (Dump high value)
        #         score += 15
        #
        # # You would need a meld.is_run() helper here:
        # # if meld.is_run(): score += 10 # Flexibility bonus

        return len(meld.tiles)

    def find_best_move(self, rack: Rack, board: Board, initial_meld_points: int = 30) -> Optional[List[Meld]]:
        # 1. Clear the cache for this new turn
        self.memo = {}

        # 2. Get *all* tiles you're allowed to use (from rack AND board)
        available_tiles = rack.tiles + board.get_all_tiles()

        # 3. Find all possible melds (The Accountant step)
        all_possible_melds = self._find_all_possible_melds(available_tiles)

        # 4. Find the best combination (The Strategist step)
        # This calls the recursive function, which returns (score, meld_list)
        (best_score, best_meld_list) = self._find_best_combination(
            tuple(available_tiles),  # The initial problem state
            all_possible_melds
        )

        # 5. Check if the move is actually worth playing (e.g., score > 0)
        if best_score > 0:
            # (TODO: Add logic here to check for 30-point initial meld rule)
            return best_meld_list

        return None

    # --- Recursive Core ---
    def _find_best_combination(self, tiles_to_cover: tuple[Tile, ...], all_melds: List[Meld]) -> Tuple[int, List[Meld]]:
        """
        RECURSIVE MAX SET PACKING ALGORITHM (User must implement the logic described in the guide)
        """
        tiles_key = frozenset(tiles_to_cover)
        # The logic here must implement the four steps:
        # 1. Cache Check
        if tiles_key in self.memo:
            return self.memo[tiles_key]

        # 2. Base Case: if not tiles_to_cover: return (0, [])
        if not tiles_to_cover:
            return (0, [])

        # 3. Recursive Loop with 'best_solution_so_far' tracking
        best_solution = (0, [])
        for meld in all_melds:
            if set(meld).issubset(tiles_to_cover):
                current_score = self._calculate_meld_score(meld)
                remaining_tiles = tuple(set(tiles_to_cover) - set(meld))
                remainder_score, remainder_melds = self._find_best_combination(remaining_tiles, all_melds)
                total_score = current_score + remainder_score
                if total_score > best_solution[0]:
                    best_solution = (total_score, [meld] + remainder_melds)

        # 4. Cache and Return the final result
        self.memo[tiles_key] = best_solution

        # This must return a tuple[int, List[Meld]]
        return best_solution


        # --- Accountant Helpers (User must implement these) ---

    def _find_all_possible_melds(self, tiles: List[Tile]) -> List[Meld]:
        # Calls the two sub-helpers
        all_groups = self._find_all_groups(tiles)
        all_runs = self._find_all_runs(tiles)
        return all_groups + all_runs

    def _find_all_groups(self, tiles: List[Tile]) -> List[Meld]:
        """
        Finds all valid groups (same value, different colors) using combinations.
        """
        # 1. Group tiles by value
        sorted_tiles = defaultdict(list)
        for t in tiles:
            if not t.is_joker:  # Ignoring Jokers for now as planned
                sorted_tiles[t.val].append(t)

        melds_lst = []

        # 2. Iterate through each value bucket
        for val, tiles_of_val in sorted_tiles.items():

            # Find all 3-tile combinations
            if len(tiles_of_val) >= 3:
                for combo_tuple in combinations(tiles_of_val, 3):
                    new_meld = Meld(list(combo_tuple))
                    if new_meld.is_valid():
                        melds_lst.append(new_meld)

            # Find all 4-tile combinations
            # (Note: Using 'if' instead of 'elif' so we catch both cases)
            if len(tiles_of_val) >= 4:
                for combo_tuple in combinations(tiles_of_val, 4):
                    new_meld = Meld(list(combo_tuple))
                    if new_meld.is_valid():
                        melds_lst.append(new_meld)

        return melds_lst

    def _find_all_runs(self, tiles: List[Tile]) -> List[Meld]:
        """
        Finds all valid runs (same color, consecutive values) using contiguous slicing.
        """
        # 1. Group tiles by color
        tiles_by_color = defaultdict(list)
        for t in tiles:
            if not t.is_joker:
                tiles_by_color[t.color].append(t)

        runs_lst = []

        # 2. Iterate through each color bucket
        for color, tiles_of_color in tiles_by_color.items():
            # Crucial: Sort the tiles by value to find sequences
            tiles_of_color.sort()

            # 3. Find all contiguous slices
            # Outer loop: Start index
            for i in range(len(tiles_of_color)):
                # Inner loop: End index (start at i + 2 to ensure min length 3)
                for j in range(i + 2, len(tiles_of_color)):

                    # Create the specific slice
                    # j+1 because python slicing is exclusive at the end
                    potential_run_list = tiles_of_color[i: j + 1]

                    new_meld = Meld(potential_run_list)

                    if new_meld.is_valid():
                        runs_lst.append(new_meld)
                    else:
                        # Optimization: If [5, 6, 8] is invalid (gap),
                        # then [5, 6, 8, 9] will definitely be invalid.
                        # Break inner loop to save time.
                        break

        return runs_lst