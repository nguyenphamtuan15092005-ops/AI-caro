import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import pygame

from ai import AIPlayer
from game import AI, EMPTY, HUMAN, Board

CELL = 56
BOARD_SIZE = 9
SIDE_WIDTH = 320
TOP_MARGIN = 24
WIDTH = CELL * BOARD_SIZE + SIDE_WIDTH
HEIGHT = CELL * BOARD_SIZE + TOP_MARGIN * 2

BG = (245, 247, 250)
PANEL = (232, 236, 241)
GRID = (55, 65, 81)
TEXT = (17, 24, 39)
MUTED = (100, 116, 139)
BLUE = (37, 99, 235)
GREEN = (22, 163, 74)
RED = (220, 38, 38)
WHITE = (255, 255, 255)


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    value: str


class CaroGUI:
    """Giao dien pygame co ban cho nguoi choi dau voi AI."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Caro AI")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.big_font = pygame.font.SysFont("arial", 34, bold=True)

        self.board = Board(BOARD_SIZE)
        self.mode = "alphabeta"
        self.depth = 3
        self.first = "human"
        self.running = True
        self.started = False
        self.game_message = "Choose options, then Start"
        self.last_report = ""
        self.ai_player = self.create_ai()

        self.buttons = self.create_buttons()

    def create_ai(self) -> AIPlayer:
        return AIPlayer(mode=self.mode, max_depth=self.depth)

    def create_buttons(self) -> list[Button]:
        x = CELL * BOARD_SIZE + 24
        return [
            Button(pygame.Rect(x, 95, 86, 34), "Minimax", "mode:minimax"),
            Button(pygame.Rect(x + 96, 95, 96, 34), "AlphaBeta", "mode:alphabeta"),
            Button(pygame.Rect(x + 202, 95, 76, 34), "Advanced", "mode:advanced"),
            Button(pygame.Rect(x, 170, 44, 34), "1", "depth:1"),
            Button(pygame.Rect(x + 52, 170, 44, 34), "2", "depth:2"),
            Button(pygame.Rect(x + 104, 170, 44, 34), "3", "depth:3"),
            Button(pygame.Rect(x + 156, 170, 44, 34), "4", "depth:4"),
            Button(pygame.Rect(x + 208, 170, 44, 34), "5", "depth:5"),
            Button(pygame.Rect(x, 245, 104, 34), "Human first", "first:human"),
            Button(pygame.Rect(x + 116, 245, 82, 34), "AI first", "first:ai"),
            Button(pygame.Rect(x, 330, 116, 38), "Start/Reset", "action:start"),
            Button(pygame.Rect(x + 128, 330, 72, 38), "Undo", "action:undo"),
        ]

    def reset_game(self) -> None:
        self.board = Board(BOARD_SIZE)
        self.ai_player = self.create_ai()
        self.started = True
        self.last_report = ""
        self.game_message = "Human turn"

        if self.first == "ai":
            self.ai_move()

    def undo_last_pair(self) -> None:
        """Undo don gian: go 2 quan cuoi cung neu dang muon thu lai."""
        stones = [(r, c) for r in range(self.board.size) for c in range(self.board.size) if self.board.grid[r][c] != EMPTY]
        for row, col in reversed(stones[-2:]):
            self.board.undo_move(row, col)
        self.game_message = "Human turn"

    def ai_move(self) -> None:
        move, info = self.ai_player.choose_move(self.board)
        if move is None:
            return

        self.board.make_move(move[0], move[1], AI)
        self.last_report = (
            f"Move {move} | value {info['value']} | nodes {info['nodes']} | "
            f"{info['time']:.3f}s"
        )

        if self.board.check_win(AI):
            self.game_message = "AI wins"
        elif self.board.is_full():
            self.game_message = "Draw"
        else:
            self.game_message = "Human turn"

    def handle_button(self, value: str) -> None:
        kind, data = value.split(":", 1)

        if kind == "mode":
            self.mode = data
            self.ai_player = self.create_ai()
        elif kind == "depth":
            self.depth = int(data)
            self.ai_player = self.create_ai()
        elif kind == "first":
            self.first = data
        elif data == "start":
            self.reset_game()
        elif data == "undo" and self.started and not self.board.game_over():
            self.undo_last_pair()

    def board_cell_from_mouse(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        x, y = pos
        if x < 0 or x >= CELL * BOARD_SIZE:
            return None
        if y < TOP_MARGIN or y >= TOP_MARGIN + CELL * BOARD_SIZE:
            return None
        return (y - TOP_MARGIN) // CELL, x // CELL

    def human_move(self, row: int, col: int) -> None:
        if not self.started or self.board.game_over():
            return
        if not self.board.make_move(row, col, HUMAN):
            self.game_message = "Invalid move"
            return

        if self.board.check_win(HUMAN):
            self.game_message = "Human wins"
            return
        if self.board.is_full():
            self.game_message = "Draw"
            return

        self.game_message = "AI thinking..."
        self.draw()
        pygame.display.flip()
        self.ai_move()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    if button.rect.collidepoint(event.pos):
                        self.handle_button(button.value)
                        return

                cell = self.board_cell_from_mouse(event.pos)
                if cell:
                    self.human_move(cell[0], cell[1])

    def draw_text(self, text: str, x: int, y: int, color=TEXT, font=None) -> None:
        surface = (font or self.font).render(text, True, color)
        self.screen.blit(surface, (x, y))

    def draw_button(self, button: Button) -> None:
        selected = False
        if button.value == f"mode:{self.mode}":
            selected = True
        if button.value == f"depth:{self.depth}":
            selected = True
        if button.value == f"first:{self.first}":
            selected = True

        color = BLUE if selected else WHITE
        text_color = WHITE if selected else TEXT
        pygame.draw.rect(self.screen, color, button.rect, border_radius=6)
        pygame.draw.rect(self.screen, (148, 163, 184), button.rect, 1, border_radius=6)

        label = self.small_font.render(button.label, True, text_color)
        label_rect = label.get_rect(center=button.rect.center)
        self.screen.blit(label, label_rect)

    def draw_board(self) -> None:
        board_rect = pygame.Rect(0, TOP_MARGIN, CELL * BOARD_SIZE, CELL * BOARD_SIZE)
        pygame.draw.rect(self.screen, WHITE, board_rect)

        for i in range(BOARD_SIZE + 1):
            x = i * CELL
            y = TOP_MARGIN + i * CELL
            pygame.draw.line(self.screen, GRID, (x, TOP_MARGIN), (x, TOP_MARGIN + CELL * BOARD_SIZE), 1)
            pygame.draw.line(self.screen, GRID, (0, y), (CELL * BOARD_SIZE, y), 1)

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                center = (c * CELL + CELL // 2, TOP_MARGIN + r * CELL + CELL // 2)
                cell = self.board.grid[r][c]
                if cell == HUMAN:
                    offset = 16
                    pygame.draw.line(self.screen, RED, (center[0] - offset, center[1] - offset), (center[0] + offset, center[1] + offset), 4)
                    pygame.draw.line(self.screen, RED, (center[0] + offset, center[1] - offset), (center[0] - offset, center[1] + offset), 4)
                elif cell == AI:
                    pygame.draw.circle(self.screen, GREEN, center, 18, 4)

    def draw_panel(self) -> None:
        x = CELL * BOARD_SIZE
        pygame.draw.rect(self.screen, PANEL, (x, 0, SIDE_WIDTH, HEIGHT))
        self.draw_text("Caro AI", x + 24, 24, TEXT, self.big_font)

        self.draw_text("Algorithm", x + 24, 70, MUTED, self.small_font)
        self.draw_text("Search depth", x + 24, 145, MUTED, self.small_font)
        self.draw_text("First move", x + 24, 220, MUTED, self.small_font)

        for button in self.buttons:
            self.draw_button(button)

        self.draw_text("Status", x + 24, 395, MUTED, self.small_font)
        self.draw_text(self.game_message, x + 24, 420, TEXT, self.font)
        if self.depth >= 5:
            self.draw_text("Depth 5: use Advanced for faster play", x + 24, 445, MUTED, self.small_font)
        self.draw_text("AI report", x + 24, 465, MUTED, self.small_font)

        words = self.last_report or "No AI move yet"
        max_chars = 30
        for idx in range(0, len(words), max_chars):
            self.draw_text(words[idx : idx + max_chars], x + 24, 490 + (idx // max_chars) * 22, TEXT, self.small_font)

    def draw(self) -> None:
        self.screen.fill(BG)
        self.draw_board()
        self.draw_panel()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    CaroGUI().run()
