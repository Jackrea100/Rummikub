import tkinter as tk
from collections import Counter
from tkinter import messagebox, simpledialog, scrolledtext
from typing import List

# Import your existing game classes
from MovePrinter import MovePrinter
from Tile import Tile
from Meld import Meld
from Rack import Rack
from Board import Board
from Solver import Solver


class RummikubGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rummikub Solver & Analyzer")
        self.root.geometry("1000x800")

        # Game State
        self.board = Board()
        self.rack = Rack([])
        self.solver = Solver()

        # --- UI Layout ---

        # 1. Top Control Panel
        control_frame = tk.Frame(root, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Button(control_frame, text="Setup Board / Rack", command=self.open_setup_dialog, bg="#dddddd",
                  font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Button(control_frame, text="Run Solver (Find Best Move)", command=self.run_solver, bg="#4CAF50", fg="white",
                  font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(control_frame, text="Clear All", command=self.clear_all, bg="#ffcccc").pack(side=tk.RIGHT, padx=10)

        # 2. The Board View (Scrollable)
        tk.Label(root, text="Current Board (Melds)", font=("Arial", 14, "bold")).pack(pady=(10, 0))

        self.board_canvas = tk.Canvas(root, bg="#2e8b57")  # Classic felt green table color
        self.board_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 3. The Rack View
        tk.Label(root, text="Your Rack", font=("Arial", 14, "bold")).pack(pady=(10, 0))

        self.rack_frame = tk.Frame(root, bg="#8B4513", height=150)  # Wood color for rack
        self.rack_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        self.rack_frame.pack_propagate(False)  # Don't shrink

        # Initial Draw
        self.refresh_display()

    # --- Drawing Logic ---

    def refresh_display(self):
        """Redraws the entire board and rack using a smart Flow Layout."""
        # 1. Clear Board Canvas
        self.board_canvas.delete("all")

        # Layout Constants
        start_x = 20
        start_y = 20
        current_x = start_x
        current_y = start_y

        tile_width = 40  # Must match what is used in draw_meld
        tile_gap = 5  # Must match what is used in draw_meld
        meld_gap = 30  # Horizontal space between distinct melds
        row_height = 70  # Vertical space for each row of melds

        # Get current window width to know when to wrap
        # Default to 1000 if window hasn't initialized/drawn yet
        window_width = self.board_canvas.winfo_width()
        if window_width < 100:
            window_width = 1000

            # Draw each Meld on the board
        for meld in self.board.melds:
            # Calculate the pixel width of this specific meld
            # Width = (Tiles * 40) + (Gaps * 5)
            num_tiles = len(meld.tiles)
            meld_pixel_width = (num_tiles * tile_width) + ((num_tiles - 1) * tile_gap)

            # Check if this meld fits on the current line
            # If (current X + width) goes past the edge, wrap to new line.
            if current_x + meld_pixel_width > window_width - 20:
                current_x = start_x  # Reset X
                current_y += row_height  # Move Y down

            # Draw the meld at the calculated position
            self.draw_meld(self.board_canvas, meld, current_x, current_y)

            # Move X pointer to the right for the next meld
            current_x += meld_pixel_width + meld_gap

        # 2. Draw Rack (Standard flow)
        for widget in self.rack_frame.winfo_children():
            widget.destroy()

        for tile in self.rack.tiles:
            lbl = self.create_tile_widget(self.rack_frame, tile)
            lbl.pack(side=tk.LEFT, padx=2, pady=10)

    def draw_meld(self, canvas, meld, start_x, start_y):
        """Draws a grouping of tiles on the canvas to represent a Meld."""
        tile_width = 40
        tile_height = 50
        gap = 5

        current_x = start_x

        for tile in meld.tiles:
            # Draw Tile Rectangle
            canvas.create_rectangle(current_x, start_y, current_x + tile_width, start_y + tile_height, fill="#f0f0f0",
                                    outline="black", width=2)

            # Draw Text (Color mapping)
            text_color = tile.color.lower()
            if text_color == "joker": text_color = "purple"

            display_text = "J" if tile.is_joker else str(tile.val)

            canvas.create_text(current_x + tile_width / 2, start_y + tile_height / 2, text=display_text,
                               fill=text_color, font=("Arial", 16, "bold"))

            current_x += tile_width + gap

    def create_tile_widget(self, parent, tile):
        """Creates a Label widget acting as a Tile for the Rack frame."""
        color_map = {"Red": "red", "Blue": "blue", "Orange": "dark orange", "Black": "black", "Joker": "purple"}
        fg_color = color_map.get(tile.color, "black")
        text = "☺" if tile.is_joker else str(tile.val)

        lbl = tk.Label(parent, text=text, fg=fg_color, bg="#fff8dc", width=3, height=2, font=("Arial", 14, "bold"),
                       relief="raised", borderwidth=2)
        return lbl

    # --- Setup & Parsing Logic ---

    def open_setup_dialog(self):
        """Opens a window to type in the board/rack state manually."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Setup Game State")
        dialog.geometry("600x600")

        tk.Label(dialog, text="Board Melds (One per line, e.g. 'R10 B10 O10')", font=("Arial", 10, "bold")).pack(pady=5)
        board_input = scrolledtext.ScrolledText(dialog, height=10, width=50)
        board_input.pack(pady=5)

        tk.Label(dialog, text="Rack Tiles (Space separated, e.g. 'R1 R2 J B13')", font=("Arial", 10, "bold")).pack(
            pady=5)
        rack_input = scrolledtext.ScrolledText(dialog, height=5, width=50)
        rack_input.pack(pady=5)

        def apply_setup():
            try:
                # --- Parse Board (Updated to use Smart Parser) ---
                new_melds = []
                board_text = board_input.get("1.0", tk.END).strip()
                if board_text:
                    for line in board_text.split('\n'):
                        if line.strip():
                            # OLD: tiles = self.parse_tile_string(line.strip())
                            # NEW: Use the smart parser
                            tiles = self.parse_smart_line(line.strip())
                            new_melds.append(Meld(tiles))

                # --- Parse Rack (Kept Standard as requested) ---
                rack_text = rack_input.get("1.0", tk.END).strip()
                new_rack_tiles = []
                if rack_text:
                    # Rack usually contains random tiles, so standard parsing is safer
                    new_rack_tiles = self.parse_tile_string(rack_text)

                # Apply
                self.board.melds = new_melds
                self.rack = Rack(new_rack_tiles)
                self.refresh_display()
                dialog.destroy()
                messagebox.showinfo("Success", "Board and Rack updated!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse input:\n{e}")

        tk.Button(dialog, text="Apply State", command=apply_setup, bg="#4CAF50", fg="white").pack(pady=20)

    def parse_smart_line(self, text: str) -> List[Tile]:
        """
        Parses a line of text using smart shorthands or falls back to standard parsing.

        Formats:
        1. Group Shorthand: "10 rob" -> Red 10, Orange 10, Blue 10
        2. Run Shorthand:   "b 3 8"  -> Blue 3, 4, 5, 6, 7, 8
        3. Standard:        "R10 O10 B10"
        """
        tokens = text.strip().split()
        if not tokens:
            return []

        color_map = {'r': 'Red', 'b': 'Blue', 'o': 'Orange', 'k': 'Black'}

        # --- Pattern 1: Group Shorthand ("10 rob") ---
        # Logic: 2 tokens. First is a Number, Second is Letters.
        if len(tokens) == 2 and tokens[0].isdigit() and tokens[1].isalpha():
            val = int(tokens[0])
            color_codes = tokens[1].lower()

            tiles = []
            for char in color_codes:
                if char in color_map:
                    tiles.append(Tile(color=color_map[char], val=val))
                else:
                    raise ValueError(f"Unknown color code '{char}' in group shorthand '{tokens[1]}'")
            return tiles

        # --- Pattern 2: Run Shorthand ("b 3 8") ---
        # Logic: 3 tokens. First is 1 Letter, Second/Third are Numbers.
        if len(tokens) == 3 and tokens[0].isalpha() and len(tokens[0]) == 1 and tokens[1].isdigit() and tokens[
            2].isdigit():
            color_char = tokens[0].lower()
            start_val = int(tokens[1])
            end_val = int(tokens[2])

            if color_char not in color_map:
                raise ValueError(f"Unknown color code '{color_char}' in run shorthand.")

            if start_val > end_val:
                raise ValueError(f"Run start ({start_val}) cannot be greater than end ({end_val}).")

            # Generate the range of tiles
            return [Tile(color=color_map[color_char], val=v) for v in range(start_val, end_val + 1)]

        # --- Fallback: Standard Parsing ---
        return self.parse_tile_string(text)

    def parse_tile_string(self, text: str) -> List[Tile]:
        """Helper to convert strings like 'R10 B10 J' into Tile objects."""
        tiles = []
        tokens = text.split()

        color_map = {'R': 'Red', 'B': 'Blue', 'O': 'Orange', 'K': 'Black'}

        for token in tokens:
            token = token.upper()
            if token == 'J' or token == 'JOKER':
                tiles.append(Tile(is_joker=True))
                continue

            # Parse standard tile (e.g. R13)
            char_code = token[0]
            val_str = token[1:]

            if char_code not in color_map:
                raise ValueError(f"Unknown color code: {char_code} in '{token}'")
            if not val_str.isdigit():
                raise ValueError(f"Invalid number: {val_str} in '{token}'")

            tiles.append(Tile(color=color_map[char_code], val=int(val_str)))

        return tiles

    # --- Solver Integration ---

    def run_solver(self):
        """Calls the Solver class."""
        messagebox.showinfo("Solver", "Running Solver... (Check console for details)")

        # 1. Capture OLD state
        old_board_tiles = self.board.get_all_tiles()

        # 2. Run Solver
        best_move = self.solver.find_best_move(self.rack, self.board)

        # 3. Handle Result
        if best_move:
            MovePrinter.print_move_guide(self.rack, self.board, best_move)

            new_board_tiles = [t for meld in best_move for t in meld.tiles]

            tiles_to_remove_counter = Counter(new_board_tiles) - Counter(old_board_tiles)
            tiles_to_remove = list(tiles_to_remove_counter.elements())

            # Remove them from the rack
            self.rack.remove_tiles(tiles_to_remove)
            self.board.melds = best_move

            # Note: A real game loop would also remove the tiles from the rack.
            # For this visualizer, we might just update the board to show the 'Solution'.
            # Or we could calculate which tiles were used and remove them.

            self.refresh_display()
            messagebox.showinfo("Solver Result", "Best move found and applied to board!")
        else:
            messagebox.showwarning("Solver Result", "No valid moves found.")

    def clear_all(self):
        self.board = Board()
        self.rack = Rack([])
        self.refresh_display()


# --- Main Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = RummikubGUI(root)
    root.mainloop()