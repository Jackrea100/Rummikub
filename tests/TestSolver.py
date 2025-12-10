import unittest
from Tile import Tile
from Meld import Meld
from Board import Board
from Rack import Rack
from Solver import Solver


class TestSolver(unittest.TestCase):
    def setUp(self):
        self.solver = Solver()
        self.board = Board()
        self.rack = Rack([])

    def _make_meld(self, text):
        # Helper to quickly make melds like "R1 R2 R3"
        # (Reusing your parsing logic style)
        tiles = []
        tokens = text.split()
        color_map = {'R': 'Red', 'B': 'Blue', 'O': 'Orange', 'K': 'Black'}

        for t in tokens:
            if t == 'J':
                tiles.append(Tile(is_joker=True))
            else:
                c = color_map[t[0]]
                v = int(t[1:])
                tiles.append(Tile(c, v))
        return Meld(tiles)

    def test_phase_2_rack_only(self):
        print("\n--- Test: Rack Only Move ---")
        # Rack has a full run. Board is empty.
        # Expect: Solver plays the run.
        self.rack.tiles = [Tile("Red", 1), Tile("Red", 2), Tile("Red", 3)]

        result = self.solver.find_best_move(self.rack, self.board)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        print("PASS: Found Red 1-2-3")

    def test_phase_3_extension(self):
        print("\n--- Test: Extension Move ---")
        # Board has R1-R2-R3. Rack has R4.
        # Expect: Board becomes R1-R2-R3-R4.
        self.board.melds = [self._make_meld("R1 R2 R3")]
        self.rack.tiles = [Tile("Red", 4)]

        result = self.solver.find_best_move(self.rack, self.board)

        self.assertIsNotNone(result)
        # Check that the first meld now has 4 tiles
        self.assertEqual(len(result[0].tiles), 4)
        print("PASS: Extended to R1-R2-R3-R4")

    def test_phase_4_scavenge_group(self):
        print("\n--- Test: Loose Tile Scavenge (Group) ---")
        # Board has Group of 4s (R4, B4, O4, K4). Rack has R3, R5.
        # Expect: Solver steals R4 from the group to make R3-R4-R5.

        group = self._make_meld("R4 B4 O4 K4")
        self.board.melds = [group]
        self.rack.tiles = [Tile("Red", 3), Tile("Red", 5)]

        result = self.solver.find_best_move(self.rack, self.board)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)  # The group (now size 3) + The new run

        # Verify specific structure
        lengths = sorted([len(m.tiles) for m in result])
        self.assertEqual(lengths, [3, 3])
        print("PASS: Stole R4 to make new run")

    def test_phase_1_joker_rescue(self):
        print("\n--- Test: Joker Rescue ---")
        # Board has [R1, J, R3]. Rack has R2.
        # Expect: Solver swaps R2 for J. Then uses J to make [B10, K10, J].

        run_with_joker = self._make_meld("R1 J R3")
        self.board.melds = [run_with_joker]

        # Rack has the 'key' (R2) and tiles for a new group (B10, K10)
        self.rack.tiles = [Tile("Red", 2), Tile("Blue", 10), Tile("Black", 10)]

        result = self.solver.find_best_move(self.rack, self.board)

        self.assertIsNotNone(result)

        # Verify R1-R2-R3 is now pure
        run_meld = next(m for m in result if m.tiles[0].val == 1)
        has_joker = any(t.is_joker for t in run_meld.tiles)
        self.assertFalse(has_joker, "Joker should be removed from board run")

        # Verify Joker was re-used in a new group
        group_meld = next(m for m in result if m.tiles[0].val == 10)
        self.assertEqual(len(group_meld.tiles), 3)
        print("PASS: Rescued Joker and reused it")


if __name__ == '__main__':
    unittest.main()