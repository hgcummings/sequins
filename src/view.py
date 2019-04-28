from guizero import App, Box, Combo, MenuBar, Text, Waffle, Window
from guizero.utilities import convert_color
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

    def close(self):
        self.app.destroy()

    def create_menu(self, menu_options):
        MenuBar(self.app,
                toplevel=[menu for menu in menu_options.keys()],
                options=[option for option in menu_options.values()])

    def clear(self):
        reset_color = convert_color((32, 16, 16))

        for frame in self.frames:
            # Setting pixels to their existing colour is quite slow (presumably because it causes a re-render)
            # The following is significantly faster than set_all() for typical use cases
            # To clear 64 Waffles (each 4x4), set_all takes 0.6s while the below takes ~0.1s
            for x in range(0, 4):
                for y in range(0, 4):
                    if frame.get_pixel(x, y) != reset_color:
                        frame.set_pixel(x, y, reset_color)

    def display_frame(self, index, frame):
        if index >= 64:
            return

        for note in frame.notes:
            self.frames[index].set_pixel(note % 4, note // 4, (127, 32, 32))

    def select_config(self, config_input, config_output, available_inputs, available_outputs, callback):
        config = Window(self.app, bg=(0,0,0), title="Sequins - Configuration")
        config.hide()

        def close_config():
            config.destroy()
            callback()

        config.on_close(close_config)

        Text(config, text="Select configuration")

        def set_input(port):
            config_input['port'] = port

        def set_output(port):
            config_output['port'] = port

        config_form = Box(config, layout="grid", width="fill")

        Text(config_form, text="Input port:", grid=[0, 0], align="right")
        Combo(
            config_form,
            grid=[1, 0],
            align="left",
            options=available_inputs,
            selected=config_input.get('port'),
            command=set_input)

        Text(config_form, text="Output port:", grid=[0, 1], align="right")
        Combo(
            config_form,
            grid=[1, 1],
            align="left",
            options=available_outputs,
            selected=config_output.get('port'),
            command=set_output)

        config.show(wait=True)
