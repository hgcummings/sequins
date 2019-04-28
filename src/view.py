from guizero import App, Box, Combo, Text, Waffle, Window
from os import path
import sys


class View:
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
            self.frames[index].set_pixel(note % 4, note // 4, (127, 32, 32))

    def select_config(self, config_input, config_output, available_inputs, available_outputs, callback):
        config = Window(self.app)
        config.hide()

        def close_config():
            config.destroy()
            callback()

        config.on_close(close_config)

        Text(config, text="Select configuration")

        config_form = Box(config, layout="grid")
        Text(config, text="Input port:", grid=[0, 0])

        def set_input(port):
            config_input['port'] = port

        def set_output(port):
            config_output['port'] = port

        Combo(
            config_form,
            grid=[1, 0],
            options=available_inputs,
            selected=config_input.get('port'),
            command=set_input)

        Text(config, text="Output port:", grid=[0, 1])
        Combo(
            config_form,
            grid=[1, 1],
            options=available_outputs,
            selected=config_output.get('port'),
            command=set_output)

        config.show(wait=True)
