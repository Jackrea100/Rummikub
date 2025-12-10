from Solver import Solver
from Board import Board
from Rack import Rack
from Meld import Meld
from Tile import Tile


# 1. Helper to recreate your specific board state
def parse_smart_line(text):
    tokens = text.strip().split()
    if not tokens: return []
    color_map = {'r': 'Red', 'b': 'Blue', 'o': 'Orange', 'k': 'Black'}

    # Group: "1 rbko"
    if len(tokens) == 2 and tokens[0].isdigit() and tokens[1].isalpha():
        val = int(tokens[0])
        return [Tile(color_map[c], val) for c in tokens[1].lower()]
    # Run: "b 1 4"
    if len(tokens) == 3 and tokens[0].isalpha():
        color = color_map[tokens[0].lower()]
        return [Tile(color, v) for v in range(int(tokens[1]), int(tokens[2]) + 1)]
    # Single: "r3"
    if len(tokens) == 1:
        t = tokens[0]
        return [Tile(color_map[t[0].lower()], int(t[1:]))]
    return []


# 2. Build the Board
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

board = Board()
for line in board_str.strip().split('\n'):
    tiles = parse_smart_line(line.strip())
    if tiles: board.melds.append(Meld(tiles))

rack = Rack(parse_smart_line(rack_str))

print(f"Board created with {len(board.melds)} melds.")
print(f"Rack: {rack}")

# 3. Manually Run Phase 4 (Scavenging) Logic to debug
solver = Solver()

print("\n--- DEBUGGING LOOSE TILES ---")
# Copy-paste the loose tile identification logic roughly here to verify
loose_options = []
for m in board.melds:
    # Logic from your Solver
    if len(m.tiles) > 3:
        real_vals = {t.val for t in m.tiles if not t.is_joker}
        is_group = len(real_vals) == 1
        if is_group:
            print(f"Found loose GROUP tiles in: {m}")
            for t in m.tiles:
                if t.val in [1, 2] and t.color == 'Red':
                    print(f"  -> FOUND TARGET: {t}")
        else:
            print(f"Found loose RUN ends in: {m}")

print("\n--- RUNNING FULL SOLVER ---")
result = solver.find_best_move(rack, board)

if result:
    print("\nSUCCESS! Solution found.")
    # Check tile count difference
    old_count = len(board.get_all_tiles())
    new_count = sum(len(m.tiles) for m in result)
    print(f"Tile Count: {old_count} -> {new_count} (Diff: {new_count - old_count})")

    # Print the specific move
    for m in result:
        if any(t.color == 'Red' and t.val == 3 for t in m.tiles):
            print(f"Meld with Red 3: {m}")
else:
    print("\nFAILURE: Solver returned None (No moves found).")