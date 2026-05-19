from typing import Iterable, List, Optional, Tuple

# Ky hieu tren ban co.
EMPTY = "."
HUMAN = "X"
AI = "O"
WIN_LENGTH = 4

Move = Tuple[int, int]


class Board:
    """Quan ly trang thai ban co Caro 9x9 va cac luat co ban."""

    def __init__(self, size: int = 9):
        if size < 9:
            raise ValueError("Board size must be at least 9.")

        self.size = size
        self.grid = [[EMPTY for _ in range(size)] for _ in range(size)]

    def copy(self) -> "Board":
        """Tao ban sao de AI thu nuoc di ma khong lam doi ban co that."""
        new_board = Board(self.size)
        new_board.grid = [row[:] for row in self.grid]
        return new_board

    def reset(self) -> None:
        """Xoa toan bo quan co tren ban."""
        self.grid = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]

    def display(self) -> None:
        """In ban co ra console."""
        print()
        print("   ", end="")
        for c in range(self.size):
            print(f"{c:2d}", end=" ")
        print()

        for r in range(self.size):
            print(f"{r:2d}", end=" ")
            for c in range(self.size):
                print(f" {self.grid[r][c]}", end=" ")
            print()
        print()

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def make_move(self, row: int, col: int, player: str) -> bool:
        """Danh quan neu o hop le va dang trong."""
        if self.in_bounds(row, col) and self.grid[row][col] == EMPTY:
            self.grid[row][col] = player
            return True
        return False

    def undo_move(self, row: int, col: int) -> None:
        """Go quan vua thu, dung trong tim kiem de tranh tao qua nhieu object."""
        if self.in_bounds(row, col):
            self.grid[row][col] = EMPTY

    def is_full(self) -> bool:
        return all(cell != EMPTY for row in self.grid for cell in row)

    def stones(self) -> Iterable[Move]:
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != EMPTY:
                    yield (r, c)

    def empty_cells(self) -> Iterable[Move]:
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == EMPTY:
                    yield (r, c)

    def check_win(self, player: str) -> bool:
        """Thang khi co 4 quan lien tiep ngang/doc/cheo, khong xet chan 2 dau."""
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != player:
                    continue

                for dr, dc in directions:
                    count = 0
                    rr, cc = r, c

                    while self.in_bounds(rr, cc) and self.grid[rr][cc] == player:
                        count += 1
                        if count >= WIN_LENGTH:
                            return True
                        rr += dr
                        cc += dc

        return False

    def winner(self) -> Optional[str]:
        if self.check_win(HUMAN):
            return HUMAN
        if self.check_win(AI):
            return AI
        return None

    def game_over(self) -> bool:
        return self.winner() is not None or self.is_full()

    def legal_moves(self, radius: int = 1) -> List[Move]:
        """
        Sinh nuoc di gan cac quan da co de giam khong gian tim kiem.
        Day la cai tien hop le theo de bai, giup Minimax/Alpha-Beta chay duoc
        o do sau 3-4 tren ban 9x9.
        """
        stones = list(self.stones())
        if not stones:
            center = self.size // 2
            return [(center, center)]

        moves = set()
        for r, c in stones:
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if self.in_bounds(rr, cc) and self.grid[rr][cc] == EMPTY:
                        moves.add((rr, cc))

        center = self.size // 2
        return sorted(moves, key=lambda mv: abs(mv[0] - center) + abs(mv[1] - center))

    def key(self) -> Tuple[Tuple[str, ...], ...]:
        """Khoa hash dung cho transposition table cua che do nang cao."""
        return tuple(tuple(row) for row in self.grid)
