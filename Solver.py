from typing import List, Optional, Tuple, Set
from collections import defaultdict, Counter
import copy

from Tile import Tile
from Rack import Rack
from Board import Board
from Meld import Meld


class Solver:
    def __init__(self):
        pass

    def find_best_move(self, rack: Rack, board: Board, initial_meld_points: int = 30) -> Optional[List[Meld]]:
        """
        The 'Delta Solver' Manager.
        Executes 4 phases of increasing complexity to find the best move.
        Does NOT dissolve the board; only modifies it incrementally.
        """
        # 0. Clone the board so we don't break the real game state during analysis
        # We need a deep copy of the melds and tiles
        board_copy_melds = [Meld(m.tiles[:]) for m in board.melds]

        # We track 'rack_tiles' as a list we can mutate (remove from) as we play
        current_rack_tiles = rack.tiles[:]

        # --- PHASE 1: JOKER RETRIEVAL (The "Rescue" Mission) ---
        # "Can I free a Joker from the board by replacing it with a tile from my hand?"
        self._phase_joker_retrieval(current_rack_tiles, board_copy_melds)

        # --- PHASE 2: RACK-ONLY MELDS (Standard Play) ---
        # "Can I play a valid set using ONLY the tiles currently in my hand?"
        new_melds = self._phase_rack_only(current_rack_tiles)
        if new_melds:
            board_copy_melds.extend(new_melds)

        # --- PHASE 3: EXTENSIONS (The "Snap-On") ---
        # "Can I add a single tile from my hand to an existing board meld?"
        self._phase_extensions(current_rack_tiles, board_copy_melds)

        # --- PHASE 4: LOOSE TILE SCAVENGING (The "Chain" Move) ---
        # "Can I take 'spare parts' from the board to help my hand tiles?"
        scavenged_melds = self._phase_loose_tile_scavenging(current_rack_tiles, board_copy_melds)
        if scavenged_melds:
            board_copy_melds.extend(scavenged_melds)

        # --- FINAL VALIDATION ---
        # Check if we actually played anything?
        # (Compare lengths or check if rack is smaller)
        if len(current_rack_tiles) < len(rack.tiles):
            return board_copy_melds

        return None

    # =========================================================================
    # PHASE 1: JOKER RETRIEVAL
    # =========================================================================
    def _phase_joker_retrieval(self, rack_tiles: List[Tile], board_melds: List[Meld]):
        """
        Scans board for Jokers. Determines their 'identity'.
        If rack has that tile, performs the swap.
        """
        for meld in board_melds:
            # Skip if no joker
            if not any(t.is_joker for t in meld.tiles):
                continue

            # Identify what the Joker stands for
            joker_indices = [i for i, t in enumerate(meld.tiles) if t.is_joker]

            for j_idx in joker_indices:
                target_identity = self._get_joker_identity(meld, j_idx)
                if not target_identity:
                    continue  # Could not determine (e.g. 2 jokers in a row is hard)

                target_color, target_val = target_identity

                # Search rack for this specific tile
                swap_candidate = None
                for rt in rack_tiles:
                    if not rt.is_joker and rt.color == target_color and rt.val == target_val:
                        swap_candidate = rt
                        break

                if swap_candidate:
                    # PERFORM SWAP
                    # 1. Remove tile from rack
                    rack_tiles.remove(swap_candidate)
                    # 2. Add Joker to rack
                    # (Find the specific joker object in the meld to remove)
                    joker_obj = meld.tiles[j_idx]
                    meld.tiles[j_idx] = swap_candidate  # Replace on board
                    rack_tiles.append(joker_obj)  # Add to hand

                    # We only do one swap per meld per pass to avoid index confusion
                    break

    def _get_joker_identity(self, meld: Meld, joker_idx: int) -> Optional[Tuple[str, int]]:
        """
        Sherlock Holmes logic: Deduce what a Joker represents.
        Returns (Color, Value) or None.
        """
        tiles = meld.tiles

        # 1. Is it a Group? (Different colors, same value)
        # Check neighbors
        real_neighbors = [t for t in tiles if not t.is_joker]
        if not real_neighbors: return None  # All jokers?

        # Heuristic: If neighbors have different colors but same value, it's a group
        if len(set(t.val for t in real_neighbors)) == 1 and len(set(t.color for t in real_neighbors)) > 1:
            group_val = real_neighbors[0].val
            existing_colors = {t.color for t in tiles if not t.is_joker}
            all_colors = {"Red", "Orange", "Blue", "Black"}
            missing = list(all_colors - existing_colors)
            if missing:
                return (missing[0], group_val)
            return None

        # 2. Is it a Run? (Same color, consecutive values)
        # Check neighbors to determine color and value
        # Look Left
        if joker_idx > 0 and not tiles[joker_idx - 1].is_joker:
            left = tiles[joker_idx - 1]
            return (left.color, left.val + 1)
        # Look Right
        if joker_idx < len(tiles) - 1 and not tiles[joker_idx + 1].is_joker:
            right = tiles[joker_idx + 1]
            return (right.color, right.val - 1)

        return None

    # =========================================================================
    # PHASE 2: RACK-ONLY MELDS
    # =========================================================================
    def _phase_rack_only(self, rack_tiles: List[Tile]) -> List[Meld]:
        """
        Standard solver logic, but applied ONLY to the rack.
        """
        # We can reuse the recursive logic here because N is small (rack size)
        # Generate all possible sets from hand
        possible_melds = self._find_valid_sets_in_pool(rack_tiles)

        # Use a simplified Greedy approach or Max Packing for the rack
        # (For simplicity in Delta Solver, we just greedily take the largest ones)

        formed_melds = []

        # Sort by size descending
        possible_melds.sort(key=lambda m: len(m.tiles), reverse=True)

        used_indices = set()  # Track by ID/Index to prevent reuse

        for meld in possible_melds:
            # Check if we still have these tiles in rack
            needed_tiles = meld.tiles

            # Verify availability
            # We need to match objects or identities.
            # Since _find_valid_sets_in_pool creates NEW Meld objects, we map back to rack.

            temp_rack = rack_tiles[:]
            can_make = True
            to_remove = []

            for t in needed_tiles:
                found = False
                for i, rt in enumerate(temp_rack):
                    # Check Identity if possible, or Value if newly generated
                    # Because we are generating fresh lists, check Value/Color/Joker
                    if t.is_joker and rt.is_joker:
                        found = True
                        temp_rack.pop(i)
                        to_remove.append(rt)
                        break
                    elif not t.is_joker and not rt.is_joker and t.val == rt.val and t.color == rt.color:
                        found = True
                        temp_rack.pop(i)
                        to_remove.append(rt)
                        break

                if not found:
                    can_make = False
                    break

            if can_make:
                # Execute
                formed_melds.append(meld)
                for tr in to_remove:
                    rack_tiles.remove(tr)  # Remove specific object from main rack list

        return formed_melds

    # =========================================================================
    # PHASE 3: EXTENSIONS
    # =========================================================================
    def _phase_extensions(self, rack_tiles: List[Tile], board_melds: List[Meld]):
        """
        Try to snap remaining rack tiles onto board melds.
        """
        # Iterate backwards so we can remove safely
        for i in range(len(rack_tiles) - 1, -1, -1):
            tile = rack_tiles[i]

            played = False
            for meld in board_melds:
                if played: break

                # Check if fits (Simplified Check)
                if self._can_extend(meld, tile):
                    meld.tiles.append(tile)
                    meld.tiles.sort()  # Re-sort to look nice
                    if meld.is_valid():
                        rack_tiles.pop(i)
                        played = True
                    else:
                        # Revert if it broke validity (e.g. run order issues)
                        meld.tiles.remove(tile)

    def _can_extend(self, meld: Meld, tile: Tile) -> bool:
        # Heuristic checks before full validation
        if not meld.tiles: return False

        # Is it a Joker?
        if tile.is_joker: return True  # Jokers fit anywhere generally

        # Analyze Meld Type
        first = meld.tiles[0]
        # (Assume sorted)
        # Determine if Group or Run
        real_tiles = [t for t in meld.tiles if not t.is_joker]
        if not real_tiles: return True  # All jokers?

        # Group Check
        vals = {t.val for t in real_tiles}
        if len(vals) == 1:
            # It's a group. Does tile match value but differ in color?
            if tile.val == list(vals)[0]:
                existing_colors = {t.color for t in real_tiles}
                if tile.color not in existing_colors:
                    return True

        # Run Check
        colors = {t.color for t in real_tiles}
        if len(colors) == 1:
            # It's a run. Does tile match color?
            if tile.color == list(colors)[0]:
                # Check value (Start - 1 or End + 1)
                # Note: This is a loose check; meld.is_valid() does the heavy lifting
                return True

        return False

    # =========================================================================
    # PHASE 4: LOOSE TILE SCAVENGING
    # =========================================================================
    def _phase_loose_tile_scavenging(self, rack_tiles: List[Tile], board_melds: List[Meld]) -> List[Meld]:
        """
        Identifies removable tiles on board. Pools them with rack.
        Tries to form NEW melds.
        """
        # 0. Ensure Melds are sorted (Crucial for identifying Run ends)
        for m in board_melds:
            m.tiles.sort()

        # 1. Identify Loose Tiles
        loose_options = []

        for meld in board_melds:
            if len(meld.tiles) > 3:
                # Check if it's a Group (Same Value) or Run (Same Color)
                real_tiles = [t for t in meld.tiles if not t.is_joker]
                if not real_tiles: continue  # Should not happen

                is_group = len(set(t.val for t in real_tiles)) == 1

                if is_group:
                    # GROUP: Every tile is a candidate!
                    for t in meld.tiles:
                        loose_options.append((t, meld))
                else:
                    # RUN: Only ends are candidates
                    loose_options.append((meld.tiles[0], meld))
                    loose_options.append((meld.tiles[-1], meld))

        if not loose_options:
            return []

        # 2. Create Pool
        scavenge_pool = rack_tiles[:]

        # Add loose tiles
        for tile, source_meld in loose_options:
            scavenge_pool.append(tile)

        # 3. Solve Pool
        # Find valid sets using this combined pool
        potential_new_melds = self._find_valid_sets_in_pool(scavenge_pool)

        # 4. Execute Moves
        final_new_melds = []

        # Sort by size to prefer bigger moves
        potential_new_melds.sort(key=lambda m: len(m.tiles), reverse=True)

        # Track which sources we have damaged in this pass
        # We cannot take 2 tiles from a Group of 4, or it becomes size 2 (Invalid).
        source_damage = defaultdict(int)

        for new_meld in potential_new_melds:
            uses_rack = False
            needed_loose = []  # List of (Tile, SourceMeld)

            # Check ingredients
            valid_meld_construction = True

            # Helper to consume local copies of available tiles so we don't double count
            # 1. Available Rack Indices
            avail_rack_indices = set(range(len(rack_tiles)))
            # 2. Available Loose Options (indices in loose_options list)
            avail_loose_indices = set(range(len(loose_options)))

            temp_needed_loose_indices = []
            temp_rack_indices_used = []

            for t in new_meld.tiles:
                found_in_rack = False
                # Try to find in Rack first
                for i in avail_rack_indices:
                    rt = rack_tiles[i]
                    if (t.is_joker and rt.is_joker) or (t.val == rt.val and t.color == rt.color):
                        uses_rack = True
                        found_in_rack = True
                        avail_rack_indices.remove(i)
                        temp_rack_indices_used.append(i)
                        break

                if not found_in_rack:
                    # Must be a loose tile
                    found_loose = False
                    for i in avail_loose_indices:
                        l_tile, l_source = loose_options[i]
                        # Check match
                        if (l_tile.is_joker and t.is_joker) or (l_tile.val == t.val and l_tile.color == t.color):
                            # Found match
                            temp_needed_loose_indices.append(i)
                            avail_loose_indices.remove(i)
                            found_loose = True
                            break

                    if not found_loose:
                        valid_meld_construction = False
                        break

            if valid_meld_construction and uses_rack:
                # SAFETY CHECK: Does removing these loose tiles break the source melds?
                # Calculate damage for this specific move
                current_move_damage = defaultdict(int)
                for i in temp_needed_loose_indices:
                    _, src = loose_options[i]
                    current_move_damage[id(src)] += 1

                is_safe = True
                for src_id, count in current_move_damage.items():
                    # Find the actual source object
                    src_obj = next(src for _, src in loose_options if id(src) == src_id)
                    remaining_len = len(src_obj.tiles) - source_damage[src_id] - count
                    if remaining_len < 3:
                        is_safe = False
                        break

                if is_safe:
                    # COMMIT MOVE

                    # 1. Update Damage Tracker
                    for src_id, count in current_move_damage.items():
                        source_damage[src_id] += count

                    # 2. Remove used rack tiles (in reverse index order to be safe)
                    for idx in sorted(temp_rack_indices_used, reverse=True):
                        rack_tiles.pop(idx)

                    # 3. Remove loose tiles from source melds
                    for i in temp_needed_loose_indices:
                        l_tile, l_source = loose_options[i]
                        # Remove specific object if possible, else value match
                        if l_tile in l_source.tiles:
                            l_source.tiles.remove(l_tile)

                    final_new_melds.append(new_meld)

                    # Remove used options from future consideration in this loop?
                    # The 'avail_loose_indices' logic handled the inner loop,
                    # but we should remove them from the master list or just rely on 'source_damage'
                    # to block invalid moves.
                    # For simplicity, we just proceed. 'source_damage' protects validity.

        return final_new_melds

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _find_valid_sets_in_pool(self, pool: List[Tile]) -> List[Meld]:
        """
        Generates all valid Groups and Runs from a list of tiles (Rack or Pool).
        Includes Joker logic.
        """
        valid_melds = []

        # 1. Find Groups (Value Match)
        # Group by value
        by_val = defaultdict(list)
        jokers = []
        for t in pool:
            if t.is_joker:
                jokers.append(t)
            else:
                by_val[t.val].append(t)

        for val, tiles in by_val.items():
            # Try to form groups of 3 or 4
            # We need at least 3 tiles total (Real + Jokers)
            if len(tiles) + len(jokers) >= 3:
                # Distinct colors
                unique_color_tiles = []
                seen_colors = set()
                for t in tiles:
                    if t.color not in seen_colors:
                        unique_color_tiles.append(t)
                        seen_colors.add(t.color)

                # If we have 3 distinct colors, easy
                if len(unique_color_tiles) >= 3:
                    valid_melds.append(Meld(unique_color_tiles[:3]))
                if len(unique_color_tiles) == 4:
                    valid_melds.append(Meld(unique_color_tiles[:4]))

                # If we have 2 distinct colors + 1 Joker
                if len(unique_color_tiles) == 2 and jokers:
                    valid_melds.append(Meld(unique_color_tiles + [jokers[0]]))

        # 2. Find Runs (Color Match)
        # Group by color
        by_color = defaultdict(list)
        for t in pool:
            if not t.is_joker: by_color[t.color].append(t)

        for color, tiles in by_color.items():
            tiles.sort(key=lambda x: x.val)
            # Sliding window of 3
            if len(tiles) < 2 and not jokers: continue

            # Simple Run Detection (No Jokers for basic speed, add Joker logic if needed)
            # Find consecutive sequences
            current_run = []
            for i in range(len(tiles)):
                if not current_run:
                    current_run.append(tiles[i])
                else:
                    if tiles[i].val == current_run[-1].val + 1:
                        current_run.append(tiles[i])
                    elif tiles[i].val == current_run[-1].val:
                        continue  # Duplicate
                    else:
                        # Gap
                        # Try to fill gap with Joker?
                        if jokers and tiles[i].val == current_run[-1].val + 2:
                            # Gap of 1 (e.g. 3, 5). Fill with Joker.
                            temp_run = current_run + [jokers[0], tiles[i]]
                            if len(temp_run) >= 3: valid_melds.append(Meld(temp_run))

                        # Save old run if valid
                        if len(current_run) >= 3:
                            valid_melds.append(Meld(current_run[:]))
                        current_run = [tiles[i]]

            if len(current_run) >= 3:
                valid_melds.append(Meld(current_run[:]))

        return valid_melds