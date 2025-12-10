from typing import List, Optional
from collections import Counter
from Meld import Meld
from Rack import Rack
from Board import Board


class MovePrinter:
    @staticmethod
    def print_move_guide(old_rack: Rack, old_board: Board, new_melds: List[Meld]):
        print(f"\n{'=' * 25} SOLVER ANALYSIS {'=' * 25}")

        # 1. DIAGNOSTICS (Sanity Check)
        # We verify if the board actually changed size or content.
        old_tiles = old_board.get_all_tiles()
        new_tiles = [t for m in new_melds for t in m.tiles]

        old_count = len(old_tiles)
        new_count = len(new_tiles)
        diff_count = new_count - old_count

        print(f"DEBUG: Board Tile Count {old_count} -> {new_count} (Change: {diff_count:+d})")

        if diff_count == 0:
            # If counts are equal, check if identities changed (Swap?)
            # If not, the solver might have failed to find a move.
            print("WARNING: Tile count unchanged. Did the solver just rearrange the board?")

        # 2. CALCULATE PLAYED TILES (The "Counter" Logic)
        # We use Counters to handle values (Red 5 == Red 5) correctly.
        old_counter = Counter([(t.color, t.val, t.is_joker) for t in old_tiles])
        new_counter = Counter([(t.color, t.val, t.is_joker) for t in new_tiles])

        played_counter = new_counter - old_counter

        played_tiles_desc = []
        for (color, val, is_joker), count in played_counter.items():
            name = "JOKER" if is_joker else f"{color} {val}"
            for _ in range(count):
                played_tiles_desc.append(name)
        played_tiles_desc.sort()

        print(f"\n👉 STEP 1: PLAY FROM RACK")
        if played_tiles_desc:
            print(f"   [ {', '.join(played_tiles_desc)} ]")
        else:
            print("   (No tiles played from rack. Pass turn or check constraints.)")

        # 3. DETAILED ACTION PLAN
        # We try to map the new sets back to the old sets to explain the changes.
        print(f"\n👉 STEP 2: BOARD CHANGES")

        # Snapshot old sets as frozen sets of tile signatures for easy matching
        # Signature: (Color, Val, IsJoker)
        def sig(t):
            return (t.color, t.val, t.is_joker)

        def sig_set(meld):
            return Counter([sig(t) for t in meld.tiles])

        old_meld_sigs = [sig_set(m) for m in old_board.melds]
        matched_indices = set()

        something_changed = False

        for i, new_meld in enumerate(new_melds, 1):
            new_sig = sig_set(new_meld)

            # Try to find exact or partial match in old board
            match_idx = -1
            match_type = "NEW"  # NEW, EXACT, EXTEND, SCAVENGE, MORPH

            # Priority 1: Exact Match
            if new_sig in old_meld_sigs:
                idx = old_meld_sigs.index(new_sig)
                if idx not in matched_indices:
                    match_idx = idx
                    match_type = "EXACT"

            # Priority 2: Extension (Old is subset of New)
            if match_idx == -1:
                for idx, old_sig in enumerate(old_meld_sigs):
                    if idx in matched_indices: continue
                    # Check if old is subset of new (all old keys in new, counts <=)
                    if not (old_sig - new_sig):
                        match_idx = idx
                        match_type = "EXTEND"
                        break

            # Priority 3: Scavenge (New is subset of Old)
            if match_idx == -1:
                for idx, old_sig in enumerate(old_meld_sigs):
                    if idx in matched_indices: continue
                    if not (new_sig - old_sig):
                        match_idx = idx
                        match_type = "SCAVENGE"
                        break

            # Handle the result
            if match_idx != -1:
                matched_indices.add(match_idx)
                old_m = old_board.melds[match_idx]

                if match_type == "EXACT":
                    # Don't print unchanged sets to reduce noise
                    continue
                elif match_type == "EXTEND":
                    added = list((new_sig - old_meld_sigs[match_idx]).elements())
                    pretty_added = [f"{c} {v}" if not j else "JOKER" for c, v, j in added]
                    print(f"   🔹 EXTEND existing set {old_m}")
                    print(f"      + Add: {pretty_added} -> Result: {new_meld}")
                    something_changed = True
                elif match_type == "SCAVENGE":
                    removed = list((old_meld_sigs[match_idx] - new_sig).elements())
                    pretty_removed = [f"{c} {v}" if not j else "JOKER" for c, v, j in removed]
                    print(f"   🔸 SCAVENGE (Take) from {old_m}")
                    print(f"      - Remove: {pretty_removed} -> Leaves: {new_meld}")
                    something_changed = True
            else:
                # Completely new set (created from rack + scavenged parts)
                print(f"   ✨ FORM NEW SET: {new_meld}")
                something_changed = True

        if not something_changed and not played_tiles_desc:
            print("   (Board state matches perfectly. No moves found.)")

        print(f"{'=' * 60}\n")