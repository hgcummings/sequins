import mido
from pattern import Pattern
from gui import Gui

pattern = Pattern()
active_notes = 0
active_frame = 0
midi_notes = [41,45,48,57,42,60,62,43,37,38,40,75,49,35,36,55]

gui = Gui()

def process_message(message):
    global active_notes, active_frame
    if (message.type == 'note_on' and message.note in midi_notes):
        pattern.add_note(midi_notes.index(message.note))
        gui.display_frame(active_frame, pattern.current_frame)
        active_notes += 1
    elif (message.type == 'note_off'):
        active_notes -= 1
        if (active_notes == 0):
            pattern.next_frame()
            active_frame += 1
    elif (message.type == 'program_change'):
        active_frame = 0
        gui.clear()

for input in mido.get_input_names():
    if input.startswith('loopMIDI Port'):
        mido.open_input(input, callback=process_message)
        break

gui.start()
