from __future__ import annotations

import math
import random
from array import array

import pygame

SAMPLE_RATE = 22050
VOLUME = 0.25

SOUND_DEFINITIONS = {
    "move": [(520, 520, 0.04, "square")],
    "select": [(660, 990, 0.09, "square")],
    "collect": [(523, 523, 0.07, "square"), (659, 659, 0.07, "square"),
                (784, 784, 0.07, "square"), (1047, 1047, 0.16, "square")],
    "level_up": [(392, 392, 0.1, "sine"), (523, 523, 0.18, "sine")],
    "death": [(420, 60, 0.7, "noise")],
    "summon": [(70, 140, 1.6, "sine")],
    "victory": [(523, 523, 0.14, "square"), (659, 659, 0.14, "square"), (784, 784, 0.14, "square"),
                (1047, 1047, 0.5, "square")],
}


def _wave(kind: str, phase: float) -> float:
    if kind == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if kind == "noise":
        return random.uniform(-1, 1) * 0.6 + math.sin(phase) * 0.4
    return math.sin(phase)


def synthesize(notes, channels: int, rate: int = SAMPLE_RATE) -> array:
    samples = array("h")
    phase = 0.0
    for start_freq, end_freq, duration, kind in notes:
        count = int(rate * duration)
        for i in range(count):
            t = i / count
            freq = start_freq + (end_freq - start_freq) * t 
            phase += 2 * math.pi * freq / rate
            envelope = min(1.0, i / 200) * (1 - t) ** 1.5
            value = int(32767 * VOLUME * envelope * _wave(kind, phase))
            samples.extend([value] * channels)
    return samples


class Audio:
    def __init__(self):
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.muted = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
            rate, sample_format, channels = pygame.mixer.get_init()
            if sample_format != -16:  
                return
            for name, notes in SOUND_DEFINITIONS.items():
                self.sounds[name] = pygame.mixer.Sound(buffer=synthesize(notes, channels, rate).tobytes())
        except (pygame.error, TypeError):
            self.sounds = {}

    def play(self, name: str) -> None:
        if not self.muted and name in self.sounds:
            self.sounds[name].play()

    def toggle_mute(self) -> None:
        self.muted = not self.muted
