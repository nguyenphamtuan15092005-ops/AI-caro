import csv
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from ai import AIPlayer
from game import AI, HUMAN, Board

CaseFactory = Callable[[], Board]
PROJECT_DIR = Path(__file__).resolve().parent.parent
GAME_DATA_SUMMARY = PROJECT_DIR / "game_data_results" / "game_data_summary.csv"
BENCHMARK_OUTPUT = PROJECT_DIR / "benchmark_results.csv"


def board_from_moves(moves: List[Tuple[int, int, str]]) -> Board:
    board = Board(9)
    for row, col, player in moves:
        board.make_move(row, col, player)
    return board


def case_opening() -> Board:
    """Dau van: moi ben co it quan."""
    return board_from_moves([(4, 4, HUMAN), (4, 5, AI)])


def case_middle_game() -> Board:
    """Giua van: co nhieu nhanh hop le hon."""
    return board_from_moves(
        [
            (4, 4, HUMAN),
            (4, 5, AI),
            (3, 4, HUMAN),
            (5, 5, AI),
            (3, 5, HUMAN),
            (5, 4, AI),
            (2, 6, HUMAN),
            (6, 6, AI),
        ]
    )


def case_ai_can_win() -> Board:
    """AI co the thang ngay bang cach noi thanh 4 quan."""
    return board_from_moves(
        [
            (4, 3, AI),
            (4, 4, AI),
            (4, 5, AI),
            (3, 3, HUMAN),
            (3, 4, HUMAN),
        ]
    )


def case_human_must_be_blocked() -> Board:
    """Nguoi choi sap thang, AI can chan."""
    return board_from_moves(
        [
            (1, 1, AI),
            (2, 2, HUMAN),
            (3, 3, HUMAN),
            (4, 4, HUMAN),
            (5, 2, AI),
            (5, 3, AI),
        ]
    )


def case_both_attack() -> Board:
    """Hai ben deu co co hoi tan cong."""
    return board_from_moves(
        [
            (4, 2, HUMAN),
            (4, 3, HUMAN),
            (2, 4, AI),
            (3, 4, AI),
            (5, 5, HUMAN),
            (5, 4, AI),
        ]
    )


def case_many_branches() -> Board:
    """Nhieu quan rai rac de kiem tra so node va thoi gian."""
    return board_from_moves(
        [
            (1, 1, HUMAN),
            (1, 2, AI),
            (2, 6, HUMAN),
            (3, 6, AI),
            (4, 4, HUMAN),
            (4, 5, AI),
            (6, 2, HUMAN),
            (6, 4, AI),
            (7, 7, HUMAN),
            (7, 6, AI),
        ]
    )


TEST_CASES: List[Tuple[str, CaseFactory]] = [
    ("opening", case_opening),
    ("middle_game", case_middle_game),
    ("ai_can_win", case_ai_can_win),
    ("human_must_be_blocked", case_human_must_be_blocked),
    ("both_attack", case_both_attack),
    ("many_branches", case_many_branches),
]

CSV_COLUMNS = [
    "benchmark_type",
    "case",
    "depth",
    "mode",
    "first_player",
    "move",
    "value",
    "nodes",
    "cutoffs",
    "cache_hits",
    "time_s",
    "same_move_as_minimax",
    "node_reduction_vs_minimax_%",
    "time_reduction_vs_minimax_%",
    "games",
    "x_wins",
    "o_wins",
    "draws",
    "first_player_wins",
    "first_player_win_rate",
    "avg_move_count",
    "avg_nodes_per_move",
    "avg_search_time_s",
    "avg_total_cutoffs",
    "avg_total_cache_hits",
    "note",
]


def empty_row() -> Dict[str, object]:
    return {column: "" for column in CSV_COLUMNS}


def pct_reduction(baseline: float, value: float) -> str:
    if baseline <= 0:
        return ""
    return f"{(baseline - value) * 100.0 / baseline:.2f}"


def run_position_benchmark(depths: List[int] | None = None) -> List[Dict[str, object]]:
    """Benchmark theo yeu cau Level 3 tren 6 trang thai co dinh."""
    if depths is None:
        depths = [1, 2, 3]

    rows: List[Dict[str, object]] = []
    for case_name, factory in TEST_CASES:
        for depth in depths:
            minimax_move = None
            minimax_nodes = 0
            minimax_time = 0.0

            mode_results = []
            for mode in ["minimax", "alphabeta", "advanced"]:
                board = factory()
                ai_player = AIPlayer(mode=mode, max_depth=depth)
                move, info = ai_player.choose_move(board)
                mode_results.append((mode, move, info))

                if mode == "minimax":
                    minimax_move = move
                    minimax_nodes = info["nodes"]
                    minimax_time = info["time"]

            for mode, move, info in mode_results:
                row = empty_row()
                row.update(
                    {
                        "benchmark_type": "fixed_position",
                        "case": case_name,
                        "depth": depth,
                        "mode": mode,
                        "move": move,
                        "value": info["value"],
                        "nodes": info["nodes"],
                        "cutoffs": info["cutoffs"],
                        "cache_hits": info["cache_hits"],
                        "time_s": f"{info['time']:.6f}",
                        "same_move_as_minimax": move == minimax_move,
                        "node_reduction_vs_minimax_%": pct_reduction(minimax_nodes, info["nodes"]),
                        "time_reduction_vs_minimax_%": pct_reduction(minimax_time, info["time"]),
                        "note": "6 trang thai co dinh trong benchmark.py",
                    }
                )
                rows.append(row)

    return rows


def read_game_data_summary() -> List[Dict[str, object]]:
    if not GAME_DATA_SUMMARY.exists():
        return []

    with GAME_DATA_SUMMARY.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def run_self_play_summary() -> List[Dict[str, object]]:
    """Doc ket qua 300 van self-play tu gui_game_data.py va dua vao benchmark_results.csv."""
    summary_rows = read_game_data_summary()
    if not summary_rows:
        return []

    baselines: Dict[Tuple[str, str], Dict[str, float]] = {}
    for row in summary_rows:
        if row["mode"] == "minimax":
            key = (row["depth"], row["first_player"])
            baselines[key] = {
                "nodes": float(row["avg_nodes_per_move"]),
                "time": float(row["avg_search_time_s"]),
            }

    rows: List[Dict[str, object]] = []
    for source in summary_rows:
        key = (source["depth"], source["first_player"])
        baseline = baselines.get(key, {"nodes": 0.0, "time": 0.0})

        row = empty_row()
        row.update(
            {
                "benchmark_type": "self_play_300_games",
                "case": "game_data_results",
                "depth": source["depth"],
                "mode": source["mode"],
                "first_player": source["first_player"],
                "nodes": source["avg_total_nodes"],
                "cutoffs": source["avg_total_cutoffs"],
                "cache_hits": source["avg_total_cache_hits"],
                "time_s": source["avg_total_search_time_s"],
                "node_reduction_vs_minimax_%": pct_reduction(
                    baseline["nodes"], float(source["avg_nodes_per_move"])
                ),
                "time_reduction_vs_minimax_%": pct_reduction(
                    baseline["time"], float(source["avg_search_time_s"])
                ),
                "games": source["games"],
                "x_wins": source["x_wins"],
                "o_wins": source["o_wins"],
                "draws": source["draws"],
                "first_player_wins": source["first_player_wins"],
                "first_player_win_rate": source["first_player_win_rate"],
                "avg_move_count": source["avg_move_count"],
                "avg_nodes_per_move": source["avg_nodes_per_move"],
                "avg_search_time_s": source["avg_search_time_s"],
                "avg_total_cutoffs": source["avg_total_cutoffs"],
                "avg_total_cache_hits": source["avg_total_cache_hits"],
                "note": "Tong hop tu gui_game_data.py, self-play 300 van, candidate cap = 3",
            }
        )
        rows.append(row)

    return rows


def print_table(rows: List[Dict[str, object]]) -> None:
    headers = [
        "benchmark_type",
        "case",
        "depth",
        "mode",
        "first_player",
        "nodes",
        "time_s",
        "node_reduction_vs_minimax_%",
        "first_player_win_rate",
    ]

    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        print("| " + " | ".join(str(row[h]) for h in headers) + " |")


def save_csv(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    fixed_position_rows = run_position_benchmark()
    self_play_rows = run_self_play_summary()
    rows = fixed_position_rows + self_play_rows

    print_table(rows)
    save_csv(rows, BENCHMARK_OUTPUT)
    print(f"\nSaved CSV: {BENCHMARK_OUTPUT}")
    print(f"Fixed-position rows: {len(fixed_position_rows)}")
    print(f"Self-play summary rows: {len(self_play_rows)}")


if __name__ == "__main__":
    main()
