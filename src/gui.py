from guizero import App, Box, Waffle


class Gui:
    def __init__(self):
        self.app = App(title="Sequins", width=1024, height=640, bg=(0, 0, 0))
        grid = Box(self.app, layout="grid", border=8)
        self.frames = [
            Waffle(
                grid,
                height=4,
                width=4,
                dim=12,
                pad=2,
                color=(64, 32, 32),
                grid=[i % 16, i // 16]
            )
            for i in range(32)
        ]

    def start(self):
        self.app.display()

    def clear(self):
        for frame in self.frames:
            frame.set_all((64, 32, 32))

    def display_frame(self, index, frame):
        if index >= 32:
            return

        for note in frame.notes:
            self.frames[index].set_pixel(note % 4, note // 4, (255, 32, 32))
