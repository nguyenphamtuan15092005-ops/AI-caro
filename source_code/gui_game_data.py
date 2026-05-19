import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from ai import AIPlayer
from game import AI, EMPTY, HUMAN, Board, Move

pygame = None

# ============================================================
# CAU HINH THUC NGHIEM
# ============================================================
# 5 do sau * 2 kieu di truoc * 10 van = 100 van cho moi thuat toan.
DEPTHS = [1, 2, 3, 4, 5]
GAMES_PER_SIDE = 10
FIRST_PLAYERS = ["ai", "human"]
ALL_MODES = ["minimax", "alphabeta", "advanced"]
BOARD_SIZE = 9

# Gioi han nay giup thu nghiem 100-300 van chay duoc trong thoi gian hop ly.
# Ham danh gia van la ham evaluate trong ai.py, dung chung cho Minimax/Alpha-Beta/Advanced.
DATA_MAX_CANDIDATES = 3
MAX_MOVES_PER_GAME = 60

# 10 nuoc mo dau khac nhau de moi depth co 10 van khong bi trung hoan toan.
# Cung mot game_index thi Minimax/Alpha-Beta/Advanced dung cung opening, dam bao cong bang.
OPENING_MOVES = [
    (4, 4),
    (4, 3),
    (3, 4),
    (4, 5),
    (5, 4),
    (3, 3),
    (3, 5),
    (5, 3),
    (5, 5),
    (4, 2),
]

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "game_data_results"
RAW_CSV = OUTPUT_DIR / "game_data_raw.csv"
SUMMARY_CSV = OUTPUT_DIR / "game_data_summary.csv"
REPORT_TXT = OUTPUT_DIR / "game_data_report.txt"

WIDTH = 980
HEIGHT = 620
BG = (245, 247, 250)
PANEL = (229, 234, 242)
TEXT = (17, 24, 39)
MUTED = (100, 116, 139)
BLUE = (37, 99, 235)
GREEN = (22, 163, 74)
RED = (220, 38, 38)
WHITE = (255, 255, 255)


@dataclass
class Button:
    rect: object
    label: str
    action: str


@dataclass
class GameJob:
    mode: str
    depth: int
    first_player: str
    game_index: int


def build_jobs(modes: Iterable[str]) -> List[GameJob]:
    jobs = []
    for mode in modes:
        for depth in DEPTHS:
            for first_player in FIRST_PLAYERS:
                for game_index in range(1, GAMES_PER_SIDE + 1):
                    jobs.append(GameJob(mode, depth, first_player, game_index))
    return jobs


def simulate_game(job: GameJob) -> Dict[str, object]:
    board = Board(BOARD_SIZE)
    x_player = AIPlayer(
        player=HUMAN,
        opponent=AI,
        mode=job.mode,
        max_depth=job.depth,
        max_candidates=DATA_MAX_CANDIDATES,
    )
    o_player = AIPlayer(
        player=AI,
        opponent=HUMAN,
        mode=job.mode,
        max_depth=job.depth,
        max_candidates=DATA_MAX_CANDIDATES,
    )

    current = AI if job.first_player == "ai" else HUMAN
    first_symbol = current
    opening_move = OPENING_MOVES[(job.game_index - 1) % len(OPENING_MOVES)]
    move_count = 0
    x_stats = empty_side_stats()
    o_stats = empty_side_stats()
    started = time.perf_counter()

    while not board.game_over() and move_count < MAX_MOVES_PER_GAME:
        if move_count == 0:
            move = opening_move
            if not board.make_move(move[0], move[1], current):
                break
            info = {
                "nodes": 0,
                "time": 0.0,
                "value": 0,
                "cutoffs": 0,
                "cache_hits": 0,
            }
        else:
            player = o_player if current == AI else x_player
            move, info = player.choose_move(board)
            if move is None:
                break

            board.make_move(move[0], move[1], current)

        if current == AI:
            update_side_stats(o_stats, info)
            current = HUMAN
        else:
            update_side_stats(x_stats, info)
            current = AI

        move_count += 1

    elapsed = time.perf_counter() - started
    winner = board.winner()
    if winner == AI:
        result = "ai_win"
    elif winner == HUMAN:
        result = "human_win"
    elif board.is_full() or move_count >= MAX_MOVES_PER_GAME:
        result = "draw"
    else:
        result = "unfinished"

    return {
        "mode": job.mode,
        "depth": job.depth,
        "first_player": job.first_player,
        "first_symbol": first_symbol,
        "game_index": job.game_index,
        "opening_move": opening_move,
        "winner": winner or ".",
        "result": result,
        "move_count": move_count,
        "x_moves": x_stats["moves"],
        "o_moves": o_stats["moves"],
        "x_total_nodes": x_stats["nodes"],
        "o_total_nodes": o_stats["nodes"],
        "total_nodes": x_stats["nodes"] + o_stats["nodes"],
        "x_avg_nodes_per_move": safe_div(x_stats["nodes"], x_stats["moves"]),
        "o_avg_nodes_per_move": safe_div(o_stats["nodes"], o_stats["moves"]),
        "avg_nodes_per_move": safe_div(x_stats["nodes"] + o_stats["nodes"], x_stats["moves"] + o_stats["moves"]),
        "x_total_time_s": x_stats["time"],
        "o_total_time_s": o_stats["time"],
        "total_search_time_s": x_stats["time"] + o_stats["time"],
        "x_avg_time_s": safe_div(x_stats["time"], x_stats["moves"]),
        "o_avg_time_s": safe_div(o_stats["time"], o_stats["moves"]),
        "avg_search_time_s": safe_div(x_stats["time"] + o_stats["time"], x_stats["moves"] + o_stats["moves"]),
        "x_avg_evaluation": mean(x_stats["values"]),
        "o_avg_evaluation": mean(o_stats["values"]),
        "x_total_cutoffs": x_stats["cutoffs"],
        "o_total_cutoffs": o_stats["cutoffs"],
        "total_cutoffs": x_stats["cutoffs"] + o_stats["cutoffs"],
        "x_cache_hits": x_stats["cache_hits"],
        "o_cache_hits": o_stats["cache_hits"],
        "total_cache_hits": x_stats["cache_hits"] + o_stats["cache_hits"],
        "wall_time_s": elapsed,
        "max_candidates": DATA_MAX_CANDIDATES,
        "max_moves": MAX_MOVES_PER_GAME,
    }


def empty_side_stats() -> Dict[str, object]:
    return {
        "moves": 0,
        "nodes": 0,
        "time": 0.0,
        "values": [],
        "cutoffs": 0,
        "cache_hits": 0,
    }


def update_side_stats(stats: Dict[str, object], info: Dict[str, object]) -> None:
    stats["moves"] = int(stats["moves"]) + 1
    stats["nodes"] = int(stats["nodes"]) + int(info["nodes"])
    stats["time"] = float(stats["time"]) + float(info["time"])
    stats["values"].append(float(info["value"]))
    stats["cutoffs"] = int(stats["cutoffs"]) + int(info["cutoffs"])
    stats["cache_hits"] = int(stats["cache_hits"]) + int(info.get("cache_hits", 0))


def safe_div(total: float, count: float) -> float:
    if count == 0:
        return 0.0
    return float(total / count)


def mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def aggregate_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[Tuple[str, int, str], List[Dict[str, object]]] = {}
    for row in rows:
        key = (str(row["mode"]), int(row["depth"]), str(row["first_player"]))
        groups.setdefault(key, []).append(row)

    summary = []
    for (mode, depth, first_player), group in sorted(groups.items()):
        games = len(group)
        ai_wins = sum(1 for row in group if row["result"] == "ai_win")
        human_wins = sum(1 for row in group if row["result"] == "human_win")
        draws = sum(1 for row in group if row["result"] == "draw")
        first_wins = sum(1 for row in group if row["winner"] == row["first_symbol"])

        summary.append(
            {
                "mode": mode,
                "depth": depth,
                "first_player": first_player,
                "games": games,
                "o_wins": ai_wins,
                "x_wins": human_wins,
                "draws": draws,
                "o_win_rate": ai_wins / games if games else 0.0,
                "x_win_rate": human_wins / games if games else 0.0,
                "first_player_wins": first_wins,
                "first_player_win_rate": first_wins / games if games else 0.0,
                "avg_move_count": mean_values(group, "move_count"),
                "avg_total_nodes": mean_values(group, "total_nodes"),
                "avg_nodes_per_move": mean_values(group, "avg_nodes_per_move"),
                "avg_x_nodes_per_move": mean_values(group, "x_avg_nodes_per_move"),
                "avg_o_nodes_per_move": mean_values(group, "o_avg_nodes_per_move"),
                "avg_total_search_time_s": mean_values(group, "total_search_time_s"),
                "avg_search_time_s": mean_values(group, "avg_search_time_s"),
                "avg_x_time_s": mean_values(group, "x_avg_time_s"),
                "avg_o_time_s": mean_values(group, "o_avg_time_s"),
                "avg_x_evaluation": mean_values(group, "x_avg_evaluation"),
                "avg_o_evaluation": mean_values(group, "o_avg_evaluation"),
                "avg_total_cutoffs": mean_values(group, "total_cutoffs"),
                "avg_total_cache_hits": mean_values(group, "total_cache_hits"),
            }
        )

    return summary


def mean_values(rows: List[Dict[str, object]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return float(sum(values) / len(values)) if values else 0.0


def save_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_outputs(rows: List[Dict[str, object]]) -> None:
    summary = aggregate_rows(rows)
    save_csv(RAW_CSV, rows)
    save_csv(SUMMARY_CSV, summary)
    write_report(rows, summary)


def write_report(raw_rows: List[Dict[str, object]], summary_rows: List[Dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "CARO AI GAME DATA REPORT",
        "",
        "Thiet ke thi nghiem:",
        f"- Depth: {DEPTHS}",
        f"- Moi depth: AI di truoc {GAMES_PER_SIDE} van, HUMAN di truoc {GAMES_PER_SIDE} van.",
        "- Tong moi thuat toan: 5 * 2 * 10 = 100 van.",
        "- Neu chay ca 3 mode thi tong la 300 van: Minimax, Alpha-Beta, Advanced.",
        "- Day la self-play: X va O deu la search agent cung thuat toan, cung depth, cung evaluate.",
        "- Moi game_index dung mot opening seed khac nhau, nhung cac thuat toan dung cung seed de so sanh cong bang.",
        f"- Candidate cap khi thu nghiem: {DATA_MAX_CANDIDATES}.",
        f"- Gioi han so nuoc moi van: {MAX_MOVES_PER_GAME}.",
        "",
        "Bang tom tat:",
    ]

    for row in summary_rows:
        lines.append(
            f"- {row['mode']} depth {row['depth']} first={row['first_player']}: "
            f"first-player win {row['first_player_wins']}/{row['games']} "
            f"({float(row['first_player_win_rate']) * 100:.1f}%), "
            f"X win {row['x_wins']}, O win {row['o_wins']}, draw {row['draws']}, "
            f"avg nodes/move {float(row['avg_nodes_per_move']):.1f}, "
            f"avg time/move {float(row['avg_search_time_s']):.4f}s"
        )

    lines.extend(
        [
            "",
            "Goi y viet bao cao:",
            "- Dung first_player_win_rate de nhan xet loi the cua ben di truoc.",
            "- Dung avg_nodes_per_move va avg_search_time_s de nhan xet chi phi tim kiem.",
            "- So sanh Minimax, Alpha-Beta va Advanced tai cung depth vi ca ba dung chung evaluate.",
            "- Alpha-Beta thuong giam thoi gian va node nho cat nhanh beta <= alpha.",
            "- Advanced them move ordering, bat thang/chan thang ngay va cache nen co the manh/nhanh hon trong mot so trang thai.",
            "- Ket qua co tinh thuc nghiem vi day la AI self-play, khong phai nguoi that.",
        ]
    )

    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")


def parse_modes(args: List[str]) -> List[str]:
    if not args or "all" in args:
        return ALL_MODES[:]

    modes = []
    for arg in args:
        if arg in ALL_MODES and arg not in modes:
            modes.append(arg)

    if not modes:
        raise ValueError("Mode hop le: minimax, alphabeta, advanced, all")
    return modes


def run_console(modes: List[str]) -> None:
    jobs = build_jobs(modes)
    rows: List[Dict[str, object]] = []
    started = time.perf_counter()
    total = len(jobs)

    print("CARO AI GAME DATA - CONSOLE MODE")
    print(f"Modes: {', '.join(modes)}")
    print(f"Total games: {total}")
    print(f"Output dir: {OUTPUT_DIR}")
    print()

    try:
        for index, job in enumerate(jobs, start=1):
            row = simulate_game(job)
            rows.append(row)
            elapsed = time.perf_counter() - started
            print(
            f"[{index:03d}/{total}] {job.mode:9s} depth={job.depth} "
            f"first={job.first_player:5s} game={job.game_index:02d} "
            f"result={row['result']:9s} nodes={row['total_nodes']} "
            f"time={float(row['total_search_time_s']):.3f}s elapsed={elapsed:.1f}s"
        )

            # Luu checkpoint de neu dung giua chung van co du lieu tam.
            if index % 10 == 0:
                save_outputs(rows)
    except KeyboardInterrupt:
        print("\nStopped by user. Saving completed games...")

    save_outputs(rows)

    print()
    print("DONE")
    print(f"Raw CSV    : {RAW_CSV}")
    print(f"Summary CSV: {SUMMARY_CSV}")
    print(f"Report TXT : {REPORT_TXT}")


class DataGUI:
    """GUI nho de chay batch game data va xuat CSV."""

    def __init__(self) -> None:
        global pygame
        if pygame is None:
            import pygame as pygame_module

            pygame = pygame_module

        pygame.init()
        pygame.display.set_caption("Caro AI Game Data")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.big_font = pygame.font.SysFont("arial", 32, bold=True)

        self.buttons = [
            Button(pygame.Rect(36, 130, 170, 42), "Alpha-Beta 100", "alphabeta"),
            Button(pygame.Rect(216, 130, 150, 42), "Minimax 100", "minimax"),
            Button(pygame.Rect(376, 130, 160, 42), "Advanced 100", "advanced"),
            Button(pygame.Rect(546, 130, 150, 42), "All 300", "all"),
            Button(pygame.Rect(706, 130, 120, 42), "Stop", "stop"),
        ]

        self.jobs: List[GameJob] = []
        self.rows: List[Dict[str, object]] = []
        self.running = True
        self.started = False
        self.status = "Choose one run mode."
        self.last_result = ""
        self.start_time = 0.0

    def start_jobs(self, action: str) -> None:
        if action == "all":
            modes = ALL_MODES
        else:
            modes = [action]

        self.jobs = build_jobs(modes)
        self.rows = []
        self.started = True
        self.start_time = time.perf_counter()
        self.status = f"Running {len(self.jobs)} games..."
        self.last_result = ""

    def stop_jobs(self) -> None:
        if self.rows:
            self.finish_jobs(stopped=True)
        self.jobs = []
        self.started = False
        self.status = "Stopped."

    def finish_jobs(self, stopped: bool = False) -> None:
        save_outputs(self.rows)

        prefix = "Stopped and saved" if stopped else "Done"
        self.status = f"{prefix}: {len(self.rows)} games. Output: {OUTPUT_DIR}"
        self.started = False

    def step_one_game(self) -> None:
        if not self.jobs:
            if self.started:
                self.finish_jobs()
            return

        job = self.jobs.pop(0)
        row = simulate_game(job)
        self.rows.append(row)

        done = len(self.rows)
        total = done + len(self.jobs)
        elapsed = time.perf_counter() - self.start_time
        self.status = f"Progress {done}/{total} games, elapsed {elapsed:.1f}s"
        self.last_result = (
            f"{row['mode']} depth={row['depth']} first={row['first_player']} "
            f"game={row['game_index']} result={row['result']} "
            f"nodes={row['total_nodes']} time={float(row['total_search_time_s']):.3f}s"
        )

        if len(self.rows) % 10 == 0:
            save_outputs(self.rows)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    if button.rect.collidepoint(event.pos):
                        if button.action == "stop":
                            self.stop_jobs()
                        elif not self.started:
                            self.start_jobs(button.action)

    def draw_text(self, text: str, x: int, y: int, color=TEXT, font=None) -> None:
        surface = (font or self.font).render(text, True, color)
        self.screen.blit(surface, (x, y))

    def draw_wrapped_text(self, text: str, x: int, y: int, max_chars: int, color=TEXT) -> None:
        for index in range(0, len(text), max_chars):
            self.draw_text(text[index : index + max_chars], x, y + (index // max_chars) * 24, color, self.small_font)

    def draw_button(self, button: Button) -> None:
        color = RED if button.action == "stop" else BLUE
        pygame.draw.rect(self.screen, color, button.rect, border_radius=6)
        label = self.small_font.render(button.label, True, WHITE)
        self.screen.blit(label, label.get_rect(center=button.rect.center))

    def draw(self) -> None:
        self.screen.fill(BG)
        pygame.draw.rect(self.screen, PANEL, (24, 24, WIDTH - 48, HEIGHT - 48), border_radius=8)

        self.draw_text("Caro AI Game Data Runner", 36, 42, TEXT, self.big_font)
        self.draw_text(
            "Each mode: 10 AI-first and 10 Human-first games at each depth 1..5.",
            36,
            88,
            MUTED,
            self.small_font,
        )

        for button in self.buttons:
            self.draw_button(button)

        self.draw_text("Status", 36, 215, MUTED, self.small_font)
        self.draw_wrapped_text(self.status, 36, 242, 100)

        self.draw_text("Last game", 36, 310, MUTED, self.small_font)
        self.draw_wrapped_text(self.last_result or "No game completed yet.", 36, 337, 105)

        self.draw_text("Output files", 36, 410, MUTED, self.small_font)
        self.draw_wrapped_text(str(RAW_CSV), 36, 437, 110)
        self.draw_wrapped_text(str(SUMMARY_CSV), 36, 464, 110)
        self.draw_wrapped_text(str(REPORT_TXT), 36, 491, 110)

        self.draw_text("Notes", 36, 540, MUTED, self.small_font)
        self.draw_text(
            "Default console run: all 300 games. Minimax depth 5 can be slow.",
            36,
            565,
            TEXT,
            self.small_font,
        )

    def run(self) -> None:
        while self.running:
            self.handle_events()
            if self.started:
                self.step_one_game()
            self.draw()
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    # Mac dinh chay console de khong can mo man hinh.
    # Vi du:
    #   python gui_game_data.py
    #   python gui_game_data.py alphabeta advanced
    #   python gui_game_data.py --gui
    if "--gui" in sys.argv:
        DataGUI().run()
    else:
        cli_args = [arg for arg in sys.argv[1:] if arg != "--console"]
        try:
            run_console(parse_modes(cli_args))
        except ValueError as exc:
            print(exc)
            sys.exit(1)
