from threading import Thread
from interface.generic import Input
from model.pattern import Pattern
from model.config import UserConfig
import mido

MIDI_NOTES = [41, 45, 48, 57, 42, 60, 62, 43, 37, 38, 40, 75, 49, 35, 36, 55]  # TODO: PatternConfig


class Presenter(Thread):
    def __init__(self, view):
        Thread.__init__(self)
        self.view = view

        self.config = UserConfig()
        self.pattern = Pattern()
        self.active_notes = 0
        self.active_frame = 0

        self.view.create_menu({
            'File': [['Configuration', self.update_config], ['Exit', self.exit]]
        })

        self.input = None
        self.output = None

    def run(self):
        self.config.load()
        self.apply_config()

    def exit(self):
        self._close_midi_ports()
        self.view.close()

    def update_config(self):
        self.view.select_config(
            self.config.get_input(), self.config.get_output(),
            mido.get_input_names(), mido.get_output_names(),
            self.config_updated)

    def apply_config(self):
        if ((self.config.get_input().get('port') in mido.get_input_names()) and
                (self.config.get_output().get('port') in mido.get_output_names())):
            self._close_midi_ports()
            self._open_midi_ports()
            return True
        else:
            self.update_config()
            return False

    def config_updated(self):
        if self.apply_config():
            self.config.save()

    def _close_midi_ports(self):
        if self.input:
            self.input.close()

        if self.output:
            self.output.close()

    def _open_midi_ports(self):
        self.input = Input(self.config.get_input()['port'], self)
        self.output = mido.open_output(self.config.get_output()['port'])

    def note_on(self, note, velocity):
        self.pass_through(mido.Message(type="note_on", note=MIDI_NOTES[note], velocity=velocity))
        self.pattern.add_note(note)  # TODO: Store velocity in pattern
        self.view.display_frame(self.active_frame, self.pattern.current_frame)
        self.active_notes += 1

    def note_off(self, note):
        self.pass_through(mido.Message(type="note_off", note=MIDI_NOTES[note]))
        self.active_notes -= 1
        if self.active_notes == 0:
            self.pattern.next_frame()
            self.active_frame += 1

    def reset(self):
        self.active_frame = 0
        self.pattern.clear()
        self.view.clear()

    def pass_through(self, message):
        self.output.send(message)

    @staticmethod
    def _config_is_valid(config_input, config_output):
        return
