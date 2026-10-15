from __future__ import annotations

import pygame

from . import settings as cfg
from .audio import Audio
from .highscore import HighScore
from .states.base import State
from .states.instructions import InstructionsState
from .states.menu import MenuState
from .states.play import PlayState
from .ui import text


class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        text.reset_cache()
        pygame.display.set_caption(cfg.TITLE)
        self.screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.highscore = HighScore()
        self.running = True
        self.state: State = MenuState(self)

    def change_state(self, state: State) -> None:
        self.state = state

    def start_new_game(self) -> None:
        self.audio.play("select")
        self.change_state(PlayState(self))

    def show_menu(self, backdrop=None) -> None:
        self.change_state(MenuState(self, backdrop))

    def show_instructions(self, backdrop=None) -> None:
        self.audio.play("select")
        self.change_state(InstructionsState(self, backdrop))

    def quit(self) -> None:
        self.running = False

    def run(self, max_frames: int | None = None) -> None:
        frames = 0
        while self.running:
            dt = min(self.clock.tick(cfg.FPS) / 1000.0, cfg.MAX_FRAME_TIME)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                else:
                    self.state.handle_event(event)

            self.state.update(dt)
            self.state.draw(self.screen)
            pygame.display.flip()

            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
        self._record_unfinished_match()
        pygame.quit()

    def _record_unfinished_match(self) -> None:
        session = getattr(self.state, "session", None)
        if session is not None:
            self.highscore.submit(session.score)
