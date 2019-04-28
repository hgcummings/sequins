class Pattern:
    def __init__(self):
        self.clear()

    def clear(self):
        self.frames = []
        self.next_frame()

    def next_frame(self):
        self.current_frame = Frame()
        self.frames.append(self.current_frame)

    def set_velocity(self, pad, velocity):
        self.current_frame.velocities[pad] = velocity


class Frame:
    def __init__(self):
        self.velocities = [0] * 16
