from threading import Thread
from input import Input
from pattern import Pattern
import mido


class Presenter(Thread):
    def __init__(self, view):
        Thread.__init__(self)
        self.view = view

        self.pattern = Pattern()
        self.active_notes = 0
        self.active_frame = 0

    def run(self):
        for midi_input in mido.get_input_names():
            if midi_input.startswith('loopMIDI Port'):
                Input(self).start(midi_input)
                break

    def note_on(self, note):
        self.pattern.add_note(note)
        self.view.display_frame(self.active_frame, self.pattern.current_frame)
        self.active_notes += 1

    def note_off(self, _):
        self.active_notes -= 1
        if self.active_notes == 0:
            self.pattern.next_frame()
            self.active_frame += 1

    def programme_change(self):
        self.active_frame = 0
        self.pattern.clear()
        self.view.clear()




