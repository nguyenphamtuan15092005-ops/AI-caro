import time
from typing import Dict, List, Optional, Tuple

from game import AI, EMPTY, HUMAN, WIN_LENGTH, Board, Move

INF = 10**12


class AIPlayer:
    """
    AI cho Caro gom 3 muc bat buoc va 1 muc nang cao:
    - minimax: Level 1.
    - alphabeta: Level 2.
    - benchmark trong benchmark.py: Level 3.
    - advanced: Alpha-Beta + sap xep nuoc di + bat thang/chan thang + cache.
    """

    def __init__(
        self,
        player: str = AI,
        opponent: str = HUMAN,
        mode: str = "alphabeta",
        max_depth: int = 3,
        max_candidates: int = 24,
    ):
        self.player = player
        self.opponent = opponent
        self.mode = mode
        # Cho phep depth 5 de AI manh hon. Depth cao hon nua se rat cham
        # voi Minimax/Alpha-Beta tren ban 9x9.
        self.max_depth = max(1, min(5, max_depth))
        self.max_candidates = max_candidates

        self.nodes = 0
        self.cutoffs = 0
        self.cache_hits = 0
        self.transposition: Dict[Tuple[Tuple[Tuple[str, ...], ...], int, bool], int] = {}

    def choose_move(self, board: Board) -> Tuple[Optional[Move], dict]:
        """Chon nuoc di va tra ve thong tin do dac theo yeu cau bao cao."""
        start_time = time.perf_counter()
        self.nodes = 0
        self.cutoffs = 0
        self.cache_hits = 0
        self.transposition.clear()

        if board.game_over():
            return None, self._info(None, 0, time.perf_counter() - start_time)

        if self.mode == "minimax":
            value, move = self._minimax_root(board)
        elif self.mode == "advanced":
            value, move = self._advanced_root(board)
        else:
            value, move = self._alphabeta_root(board)

        elapsed = time.perf_counter() - start_time
        return move, self._info(move, value, elapsed)

    def _info(self, move: Optional[Move], value: int, elapsed: float) -> dict:
        return {
            "mode": self.mode,
            "move": move,
            "value": value,
            "nodes": self.nodes,
            "cutoffs": self.cutoffs,
            "cache_hits": self.cache_hits,
            "time": elapsed,
            "depth": self.max_depth,
        }

    # ============================================================
    # HAM DANH GIA TRANG THAI
    # ============================================================
    def evaluate(self, board: Board) -> int:
        """Diem duong tot cho AI, diem am tot cho nguoi choi."""
        if board.check_win(self.player):
            return 10_000_000
        if board.check_win(self.opponent):
            return -10_000_000

        return self._evaluate_player(board, self.player) - self._evaluate_player(
            board, self.opponent
        )

    def _evaluate_player(self, board: Board, player: str) -> int:
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        total = 0

        for r in range(board.size):
            for c in range(board.size):
                if board.grid[r][c] != player:
                    continue

                for dr, dc in directions:
                    # Chi cham diem tai dau chuoi de tranh dem trung.
                    prev_r, prev_c = r - dr, c - dc
                    if board.in_bounds(prev_r, prev_c) and board.grid[prev_r][prev_c] == player:
                        continue

                    count = 0
                    rr, cc = r, c
                    while board.in_bounds(rr, cc) and board.grid[rr][cc] == player:
                        count += 1
                        rr += dr
                        cc += dc

                    open_ends = 0
                    if board.in_bounds(rr, cc) and board.grid[rr][cc] == EMPTY:
                        open_ends += 1

                    before_r, before_c = r - dr, c - dc
                    if board.in_bounds(before_r, before_c) and board.grid[before_r][before_c] == EMPTY:
                        open_ends += 1

                    total += self._pattern_score(count, open_ends)

        return total

    def _pattern_score(self, count: int, open_ends: int) -> int:
        if count >= WIN_LENGTH:
            return 10_000_000
        if count == 3 and open_ends == 2:
            return 80_000
        if count == 3 and open_ends == 1:
            return 12_000
        if count == 2 and open_ends == 2:
            return 2_000
        if count == 2 and open_ends == 1:
            return 400
        if count == 1 and open_ends > 0:
            return 20
        return 0

    # ============================================================
    # LEVEL 1: MINIMAX
    # ============================================================
    def _minimax_root(self, board: Board) -> Tuple[int, Optional[Move]]:
        best_value = -INF
        best_move = None

        for move in self._candidate_moves(board, ordered=False):
            board.make_move(move[0], move[1], self.player)
            value = self._minimax(board, depth=1, maximizing=False)
            board.undo_move(move[0], move[1])

            if value > best_value:
                best_value = value
                best_move = move

        return int(best_value), best_move

    def _minimax(self, board: Board, depth: int, maximizing: bool) -> int:
        self.nodes += 1
        terminal = self._terminal_value(board, depth)
        if terminal is not None:
            return terminal
        if depth >= self.max_depth:
            return self.evaluate(board)

        if maximizing:
            best_value = -INF
            current_player = self.player
        else:
            best_value = INF
            current_player = self.opponent

        for move in self._candidate_moves(board, ordered=False):
            board.make_move(move[0], move[1], current_player)
            value = self._minimax(board, depth + 1, not maximizing)
            board.undo_move(move[0], move[1])

            if maximizing:
                best_value = max(best_value, value)
            else:
                best_value = min(best_value, value)

        return int(best_value)

    # ============================================================
    # LEVEL 2: ALPHA-BETA PRUNING
    # ============================================================
    def _alphabeta_root(self, board: Board) -> Tuple[int, Optional[Move]]:
        best_value = -INF
        best_move = None
        alpha = -INF
        beta = INF

        for move in self._candidate_moves(board, ordered=False):
            board.make_move(move[0], move[1], self.player)
            value = self._alphabeta(board, depth=1, maximizing=False, alpha=alpha, beta=beta)
            board.undo_move(move[0], move[1])

            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)

        return int(best_value), best_move

    def _alphabeta(self, board: Board, depth: int, maximizing: bool, alpha: int, beta: int) -> int:
        self.nodes += 1
        terminal = self._terminal_value(board, depth)
        if terminal is not None:
            return terminal
        if depth >= self.max_depth:
            return self.evaluate(board)

        moves = self._candidate_moves(board, ordered=False)

        if maximizing:
            value = -INF
            for move in moves:
                board.make_move(move[0], move[1], self.player)
                value = max(
                    value,
                    self._alphabeta(board, depth + 1, False, alpha, beta),
                )
                board.undo_move(move[0], move[1])

                alpha = max(alpha, value)
                if beta <= alpha:
                    self.cutoffs += 1
                    break
            return int(value)

        value = INF
        for move in moves:
            board.make_move(move[0], move[1], self.opponent)
            value = min(
                value,
                self._alphabeta(board, depth + 1, True, alpha, beta),
            )
            board.undo_move(move[0], move[1])

            beta = min(beta, value)
            if beta <= alpha:
                self.cutoffs += 1
                break
        return int(value)

    # ============================================================
    # NANG CAO: ALPHA-BETA + MOVE ORDERING + CACHE
    # ============================================================
    def _advanced_root(self, board: Board) -> Tuple[int, Optional[Move]]:
        tactical_move = self._find_immediate_tactical_move(board)
        if tactical_move is not None:
            board.make_move(tactical_move[0], tactical_move[1], self.player)
            value = self.evaluate(board)
            board.undo_move(tactical_move[0], tactical_move[1])
            return value, tactical_move

        best_value = -INF
        best_move = None
        alpha = -INF
        beta = INF

        for move in self._candidate_moves(board, ordered=True):
            board.make_move(move[0], move[1], self.player)
            value = self._advanced_alphabeta(board, 1, False, alpha, beta)
            board.undo_move(move[0], move[1])

            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)

        return int(best_value), best_move

    def _advanced_alphabeta(
        self, board: Board, depth: int, maximizing: bool, alpha: int, beta: int
    ) -> int:
        self.nodes += 1
        terminal = self._terminal_value(board, depth)
        if terminal is not None:
            return terminal
        if depth >= self.max_depth:
            return self.evaluate(board)

        cache_key = (board.key(), self.max_depth - depth, maximizing)
        if cache_key in self.transposition:
            self.cache_hits += 1
            return self.transposition[cache_key]

        if maximizing:
            value = -INF
            player = self.player
        else:
            value = INF
            player = self.opponent

        for move in self._candidate_moves(board, ordered=True):
            board.make_move(move[0], move[1], player)
            child_value = self._advanced_alphabeta(board, depth + 1, not maximizing, alpha, beta)
            board.undo_move(move[0], move[1])

            if maximizing:
                value = max(value, child_value)
                alpha = max(alpha, value)
            else:
                value = min(value, child_value)
                beta = min(beta, value)

            if beta <= alpha:
                self.cutoffs += 1
                break

        self.transposition[cache_key] = int(value)
        return int(value)

    def _candidate_moves(self, board: Board, ordered: bool) -> List[Move]:
        moves = board.legal_moves(radius=1)
        if ordered:
            moves = sorted(moves, key=lambda move: self._move_score(board, move), reverse=True)
        return moves[: self.max_candidates]

    def _move_score(self, board: Board, move: Move) -> int:
        """Diem sap xep nuoc di: uu tien thang, chan thang, va gan trung tam."""
        r, c = move
        center = board.size // 2

        board.make_move(r, c, self.player)
        if board.check_win(self.player):
            board.undo_move(r, c)
            return 100_000_000
        attack_score = self.evaluate(board)
        board.undo_move(r, c)

        board.make_move(r, c, self.opponent)
        opponent_wins = board.check_win(self.opponent)
        block_score = self._evaluate_player(board, self.opponent)
        board.undo_move(r, c)

        center_score = 20 - (abs(r - center) + abs(c - center))
        if opponent_wins:
            return 90_000_000 + center_score
        return attack_score + block_score + center_score

    def _find_immediate_tactical_move(self, board: Board) -> Optional[Move]:
        """Neu co the thang ngay thi danh, neu doi thu sap thang thi chan."""
        moves = self._candidate_moves(board, ordered=True)

        for move in moves:
            board.make_move(move[0], move[1], self.player)
            wins = board.check_win(self.player)
            board.undo_move(move[0], move[1])
            if wins:
                return move

        for move in moves:
            board.make_move(move[0], move[1], self.opponent)
            opponent_wins = board.check_win(self.opponent)
            board.undo_move(move[0], move[1])
            if opponent_wins:
                return move

        return None

    def _terminal_value(self, board: Board, depth: int) -> Optional[int]:
        if board.check_win(self.player):
            return 10_000_000 - depth
        if board.check_win(self.opponent):
            return -10_000_000 + depth
        if board.is_full():
            return 0
        return None
