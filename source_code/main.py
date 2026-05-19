from ai import AIPlayer
from game import AI, HUMAN, Board

MODES = {
    "1": ("minimax", "Level 1 - Minimax"),
    "2": ("alphabeta", "Level 2 - Alpha-Beta"),
    "3": ("advanced", "Nang cao - Alpha-Beta + ordering + cache"),
}


def ask_choice(prompt: str, valid: set[str], default: str) -> str:
    """Nhap lua chon console, neu bo trong thi dung gia tri mac dinh."""
    value = input(prompt).strip()
    if not value:
        return default
    while value not in valid:
        print("Lua chon khong hop le.")
        value = input(prompt).strip() or default
    return value


def print_ai_report(info: dict) -> None:
    print("\n========== AI REPORT ==========")
    print(f"Mode      : {info['mode']}")
    print(f"Best move : {info['move']}")
    print(f"Evaluation: {info['value']}")
    print(f"Depth     : {info['depth']}")
    print(f"Nodes     : {info['nodes']}")
    print(f"Cutoffs   : {info['cutoffs']}")
    print(f"Cache hits: {info['cache_hits']}")
    print(f"Time      : {info['time']:.4f} s")
    print("===============================\n")


def make_ai_move(board: Board, ai_player: AIPlayer) -> bool:
    move, info = ai_player.choose_move(board)
    if move is None:
        return False

    board.make_move(move[0], move[1], AI)
    print_ai_report(info)
    return True


def main() -> None:
    print("===== CARO AI 9x9 - 4 IN A ROW =====")
    print("1. Level 1 - Minimax")
    print("2. Level 2 - Alpha-Beta")
    print("3. Nang cao - Alpha-Beta + ordering + cache")

    mode_key = ask_choice("Chon AI mode [1/2/3, default 2]: ", {"1", "2", "3"}, "2")
    mode, mode_name = MODES[mode_key]

    depth_key = ask_choice(
        "Chon do sau tim kiem [1/2/3/4/5, default 3]: ",
        {"1", "2", "3", "4", "5"},
        "3",
    )
    first_key = ask_choice("Ai di truoc? [h=human/a=ai, default h]: ", {"h", "a"}, "h")

    board = Board(size=9)
    ai_player = AIPlayer(mode=mode, max_depth=int(depth_key))

    print(f"\nDang choi voi {mode_name}, depth = {depth_key}.")
    if int(depth_key) >= 5 and mode == "minimax":
        print("Luu y: Minimax depth 5 co the rat cham. Nen dung Alpha-Beta hoac Nang cao.")
    print("Nhap nuoc di theo dang: row col. Vi du: 4 4")
    print("Nhap q de thoat.\n")

    if first_key == "a":
        make_ai_move(board, ai_player)

    while True:
        board.display()

        if board.check_win(AI):
            print("AI WINS")
            break
        if board.check_win(HUMAN):
            print("HUMAN WINS")
            break
        if board.is_full():
            print("DRAW")
            break

        raw = input("Human move (row col): ").strip().lower()
        if raw == "q":
            print("Thoat game.")
            break

        try:
            row_text, col_text = raw.split()
            row, col = int(row_text), int(col_text)
        except ValueError:
            print("Input sai. Hay nhap 2 so, vi du: 4 4")
            continue

        if not board.make_move(row, col, HUMAN):
            print("Nuoc di khong hop le.")
            continue

        if board.check_win(HUMAN):
            board.display()
            print("HUMAN WINS")
            break
        if board.is_full():
            board.display()
            print("DRAW")
            break

        make_ai_move(board, ai_player)


if __name__ == "__main__":
    main()
