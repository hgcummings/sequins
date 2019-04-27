from guizero import App, Box, Waffle
from os import path
import sys


class Gui:
    def __init__(self):
        self.app = App(title="Sequins", width=1024, height=640, bg=(0, 0, 0))
        self.app.text_color = (216, 216, 216)
        self.app.tk.iconbitmap(path.join(path.dirname(path.realpath(sys.argv[0])), 'logo.ico'))

        grid = Box(self.app, layout="grid", border=8)
        self.frames = [
            Waffle(
                grid,
                height=4,
                width=4,
                dim=12,
                pad=2,
                color=(32, 16, 16),
                grid=[i % 16, i // 16]
            )
            for i in range(64)
        ]

    def start(self):
        self.app.display()

    def clear(self):
        for frame in self.frames:
            frame.set_all((64, 32, 32))

    def display_frame(self, index, frame):
        if index >= 64:
            return

        for note in frame.notes:
            self.frames[index].set_pixel(note % 4, note // 4, (255, 32, 32))
