class Tile:
    # Corrected list format
    COLORS = ["Red", "Orange", "Blue", "Black"]

    def __init__(self, color: str = None, val: int = None, is_joker: bool = False):
        if is_joker:
            self.color = "Joker"
            self.val = 30  # For end-game scoring simplicity
            self.is_joker = True
        else:
            if color not in self.COLORS or val is None or not (1 <= val <= 13):
                raise ValueError(f"Invalid tile creation: Color={color}, Value={val}.")

            self.color = color
            self.val = val
            self.is_joker = False

    def get_points(self) -> int:
        # Returns the face value (used for initial meld point total)
        return self.val

    def __repr__(self):
        if self.is_joker:
            return "JOKER"
        return f"{self.color[0]}{self.val}"

    def __lt__(self, other):
        # Sorts by value, then color
        return (self.val, self.color) < (other.val, other.color)

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return (self.color, self.val, self.is_joker) == (other.color, other.val, other.is_joker)

    def __hash__(self):
        # Necessary for using Tiles in sets or as dict keys
        return hash((self.color, self.val, self.is_joker))