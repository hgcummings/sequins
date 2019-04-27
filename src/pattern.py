class Pattern:
    def __init__(self):
        self.clear()

    def clear(self):
        self.frames = []
        self.next_frame()

    def next_frame(self):
        self.current_frame = Frame()
        self.frames.append(self.current_frame)

    def add_note(self, note):
        self.current_frame.notes.append(note)


class Frame:
    def __init__(self):
        self.notes = []
