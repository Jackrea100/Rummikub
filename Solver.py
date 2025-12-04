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

    @staticmethod
    def _calculate_meld_score(meld: Meld) -> int:
        """
        Calculates the strategic score for a single meld (Heuristic Brain).
        This method must be implemented by the user based on desired strategy.
        """
        # score = len(meld.tiles)  # Base score: tile count
        #
        # # Example Heuristics (User must implement):
        # for tile in meld.tiles:
        #     if tile.val in [10, 11, 12, 13]: # Risk Aversion (Dump high value)
        #         score += 15
        #
        # # You would need a meld.is_run() helper here:
        # # if meld.is_run(): score += 10 # Flexibility bonus

        return len(meld.tiles)

    def find_best_move(self, rack: Rack, board: Board, initial_meld_points: int = 30) -> Optional[List[Meld]]:
        import time
        print("--- SOLVER STARTED ---")

        self.memo = {}
        all_tiles = rack.tiles + board.get_all_tiles()

        # 1. Identify IDs for rack usage
        rack_tile_ids = {id(t) for t in rack.tiles}

        # 2. Identify Existing Melds (Exact & Subsets)
        existing_meld_sets = [frozenset(m.tiles) for m in board.melds]

        tile_components = self._get_connected_components(all_tiles)

        sizes = [len(c) for c in tile_components]
        print(f"DEBUG: Found {len(tile_components)} components. Sizes: {sizes}")

        final_solution_melds = []

        for i, component_tiles in enumerate(tile_components):
            comp_start = time.time()
            timeout = 5.0 if len(component_tiles) > 20 else 0

            # print(f"  > Solving Component {i+1} (Size {len(component_tiles)})...")
            possible_melds = self._find_all_possible_melds(component_tiles)

            # --- UPGRADED PRIORITY LOGIC ---
            def meld_priority(m: Meld):
                m_set = frozenset(m.tiles)

                # Priority 1: Rack Usage
                rack_usage = sum(1 for t in m.tiles if id(t) in rack_tile_ids)

                # Priority 2: Exact Match (Perfect Stability)
                is_exact = 1 if m_set in existing_meld_sets else 0

                # Priority 3: Subset Match (Partial Stability) [NEW]
                # If this meld is a subset of an OLD meld, it preserves the "style" (Run vs Group)
                is_subset = 0
                if not is_exact:  # Only check if not exact
                    for old_set in existing_meld_sets:
                        if m_set.issubset(old_set):
                            is_subset = 1
                            break

                # Priority 4: Size (Bigger is better)
                # Priority 5: Type Preference (Tie-breaker: Prefer Runs to Groups to reduce chaos)
                is_run = 1 if m.is_run() else 0  # You might need to add is_run() to Meld, or check logic

                return rack_usage, is_exact, is_subset, len(m.tiles), is_run

            possible_melds.sort(key=meld_priority, reverse=True)
            # -------------------------------

            (score, best_melds) = self._find_best_combination(tuple(component_tiles), possible_melds, time.time(),
                                                              timeout)

            if best_melds:
                final_solution_melds.extend(best_melds)

            print(f"    - Finished in {time.time() - comp_start:.4f}s")

        print(f"--- SOLVER FINISHED ---")

        if final_solution_melds:
            return final_solution_melds

        return None

    # Update Signature to accept start_time and timeout
    def _find_best_combination(self, tiles_to_cover: tuple[Tile, ...], all_melds: List[Meld], start_time: float = 0,
                               timeout: float = 0) -> Tuple[int, List[Meld]]:
        import time

        # 1. Timeout Check
        if timeout > 0 and (time.time() - start_time > timeout):
            return 0, []

        # 2. Cache Check
        tiles_key = frozenset(tiles_to_cover)
        if tiles_key in self.memo:
            return self.memo[tiles_key]

        # 3. Base Case
        if not tiles_to_cover:
            return 0, []

        best_solution = (0, [])

        for meld in all_melds:
            # Check Timeout inside loop
            if timeout > 0 and (time.time() - start_time > timeout):
                break

            # Optimization: Only attempt if subset (Value-based check)
            if set(meld).issubset(tiles_to_cover):
                current_score = self._calculate_meld_score(meld)

                # --- FIX: Use Standard Removal (Equality) ---
                # This guarantees the list shrinks by exactly len(meld) tiles.
                # It removes the first matching tile it finds.
                try:
                    temp_remaining = list(tiles_to_cover)
                    for tile in meld:
                        temp_remaining.remove(tile)
                    remaining_tiles = tuple(temp_remaining)
                except ValueError:
                    # Should not happen given issubset check, but safe fallback
                    continue
                # --------------------------------------------

                remainder_score, remainder_melds = self._find_best_combination(remaining_tiles, all_melds, start_time,
                                                                               timeout)

                total_score = current_score + remainder_score
                if total_score > best_solution[0]:
                    best_solution = (total_score, [meld] + remainder_melds)

        self.memo[tiles_key] = best_solution
        return best_solution

    def _find_all_possible_melds(self, tiles: List[Tile]) -> List[Meld]:
        # Calls the two sub-helpers
        all_groups = self._find_all_groups(tiles)
        all_runs = self._find_all_runs(tiles)
        return all_groups + all_runs

    @staticmethod
    def _find_all_groups(tiles: List[Tile]) -> List[Meld]:
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

    @staticmethod
    def _find_all_runs(tiles: List[Tile]) -> List[Meld]:
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

    @staticmethod
    def _build_intersection_graph(tiles: List[Tile]) -> Dict[Tile, List[Tile]]:
        graph = defaultdict(list)
        for i in range(len(tiles)):
            for j in range(i + 1, len(tiles)):
                t1, t2 = tiles[i], tiles[j]

                is_group = t1.val == t2.val and t1.color != t2.color
                is_run = t1.color == t2.color and abs(t1.val - t2.val) == 1

                if is_group or is_run:
                    graph[t1].append(t2)
                    graph[t2].append(t1)

        return graph

    def _get_connected_components(self, tiles: List[Tile]) -> List[List[Tile]]:
        graph = self._build_intersection_graph(tiles)
        visited_ids = set()  # Track by ID (memory address) to handle duplicates
        components = []

        for tile in tiles:
            # Check by ID, not value!
            if id(tile) in visited_ids:
                continue

            stack = [tile]
            curr_component = [tile]
            visited_ids.add(id(tile))  # Mark start as visited

            while stack:
                curr_tile = stack.pop()

                for neighbor in graph[curr_tile]:
                    # Check by ID
                    if id(neighbor) not in visited_ids:
                        visited_ids.add(id(neighbor))
                        stack.append(neighbor)
                        curr_component.append(neighbor)

            components.append(curr_component)

        return components