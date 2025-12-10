from Solver import Solver
from Board import Board
from Rack import Rack
from Meld import Meld
from Tile import Tile


def parse_smart_line(text):
    """Parses your shorthand format into Tile lists."""
    tokens = text.strip().split()
    if not tokens:
        return []

    color_map = {'r': 'Red', 'b': 'Blue', 'o': 'Orange', 'k': 'Black'}

    # Format: "5 rbk" (Group)
    if len(tokens) == 2 and tokens[0].isdigit() and tokens[1].isalpha():
        val = int(tokens[0])
        chars = tokens[1].lower()
        return [Tile(color_map[c], val) for c in chars]

    # Format: "b 1 4" (Run)
    if len(tokens) == 3 and tokens[0].isalpha() and len(tokens[0]) == 1:
        color = color_map[tokens[0].lower()]
        start = int(tokens[1])
        end = int(tokens[2])
        return [Tile(color, v) for v in range(start, end + 1)]

    # Format: "r3" (Single/Standard)
    if len(tokens) == 1:
        t = tokens[0]
        if t[0].lower() in color_map:
            return [Tile(color_map[t[0].lower()], int(t[1:]))]

    return []


def run_test():
    # 1. Setup Board
    board_str = """
b 1 4
5 rbk
b 6 9
12 rbko
r 3 5
7 rbko
1 rbko
6 rbo
k 9 11
o 7 9
k 4 7
r 9 12
8 rbo
9 rbko
o 11 13
2 rbko
10 rbo
o 3 6
13 rbo
11 rkb
"""
    rack_str = "r3"

    print("--- Setting up Test Case ---")
    board = Board()
    for line in board_str.strip().split('\n'):
        tiles = parse_smart_line(line.strip())
        if tiles:
            board.melds.append(Meld(tiles))

    rack_tiles = parse_smart_line(rack_str)
    rack = Rack(rack_tiles)

    # 2. Count Initial Red 3s
    board_r3 = sum(1 for m in board.melds for t in m.tiles if t.color == "Red" and t.val == 3)
    rack_r3 = sum(1 for t in rack.tiles if t.color == "Red" and t.val == 3)
    initial_total = board_r3 + rack_r3

    print(f"Initial Red 3s on Board: {board_r3} (from 'r 3 5')")
    print(f"Initial Red 3s in Rack:  {rack_r3}")
    print(f"Total Red 3s:            {initial_total}")

    print("\n--- Running Solver ---")
    solver = Solver()
    best_move = solver.find_best_move(rack, board)

    if best_move:
        # 3. Count Final Red 3s
        final_total = sum(1 for m in best_move for t in m.tiles if t.color == "Red" and t.val == 3)

        print(f"Solution found with {len(best_move)} melds.")
        print(f"Final Red 3 Count:       {final_total}")

        if final_total > initial_total:
            print("❌ FAILURE: Duplication Detected! (Tiles created out of thin air)")
        elif final_total < initial_total:
            print("❌ FAILURE: Tiles Vanished!")
        else:
            print("✅ SUCCESS: Count Preserved. No duplication.")

        print("\nMelds containing Red 3:")
        for m in best_move:
            if any(t.color == "Red" and t.val == 3 for t in m.tiles):
                print(f"  {m}")
    else:
        print("No solution found.")


if __name__ == "__main__":
    run_test()