from guizero import App, Drawing
from threading import Thread

U = 16
W = 64
H = 9

class Gui():
    def __init__(self):
        self.app = App(title="drumlights", width=W*U)
        self.drawing = Drawing(self.app, width=W*U, height=H*U)

    def start(self):
        self.drawing.rectangle(0,0,W*U,H*U)
        self.clear()
        self.app.display()

    def clear(self):
        for i in range(32):
            self._render_frame(i, range(16), (64,32,32))

    def display_frame(self, index, frame):
        if (index >= 32):
            return
        
        self._render_frame(index, frame.notes, (255,0,0))

    def _render_frame(self, index, notes, color):
        fx = index if index < 16 else index % 16
        fx = fx * 4
        fy = 0 if index < 16 else 5

        for note in notes:
            nx = note % 4
            ny = note // 4

            x = fx + nx
            y = fy + ny

            x1 = x * U + (2 if nx == 0 else 1)
            y1 = y * U + (2 if ny == 0 else 1)
            x2 = (x + 1) * U - (2 if nx == 3 else 1)
            y2 = (y + 1) * U - (2 if ny == 3 else 1)

            self.drawing.rectangle(x1, y1, x2, y2, color=color)
