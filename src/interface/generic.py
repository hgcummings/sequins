import mido

PAD_NOTES = [41, 45, 48, 57, 42, 60, 62, 43, 37, 38, 40, 75, 49, 35, 36, 55]  # TODO: Config


class Input:
    def __init__(self, input_name, presenter):
        self.presenter = presenter
        self.midi_input = mido.open_input(input_name, callback=self.process_message)

    def process_message(self, message):
        if message.type == 'note_on' and message.note in PAD_NOTES:
            self.presenter.pad_on(PAD_NOTES.index(message.note), message.velocity)
        elif message.type == 'note_off' and message.note in PAD_NOTES:
            self.presenter.pad_off(PAD_NOTES.index(message.note))
        else:
            self.presenter.pass_through(message)

        if message.type == 'program_change':  # TODO: Config
            self.presenter.reset()

    def close(self):
        self.midi_input.close()
