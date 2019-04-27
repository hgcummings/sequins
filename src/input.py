import mido

MIDI_NOTES = [41, 45, 48, 57, 42, 60, 62, 43, 37, 38, 40, 75, 49, 35, 36, 55]


class Input:
    def __init__(self, presenter):
        self.presenter = presenter

    def start(self, input_name):
        def process_message(message):
            if message.type == 'note_on':
                self.presenter.note_on(MIDI_NOTES.index(message.note))
            elif message.type == 'note_off':
                self.presenter.note_off(MIDI_NOTES.index(message.note))
            elif message.type == 'program_change':
                self.presenter.program_change()

        mido.open_input(input_name, callback=process_message)
