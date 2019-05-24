from pyftdi.i2c import I2cController

# Register addresses (see IS31FL3731 docs)
_COMMAND_REGISTER = 0xfd
_DISPLAY_REGISTER = 0x01
_SHUTDOWN_REGISTER = 0x0a
_FUNCTION_REGISTER = 0x0b
_PWM_REG_OFFSET = 0x24

# Device properties
_BASE_ADDRESS = 0x74
_BITS_PER_REGISTER = 8
_DEVICE_COUNT = 4
_PIXELS_PER_ROW = 16
_PIXELS_PER_COL = 9
_REGISTERS_PER_ROW = _PIXELS_PER_ROW // _BITS_PER_REGISTER
_PAGE_COUNT = 8

# Frame layout
_FRAME_WIDTH = 4
_FRAME_HEIGHT = 4
_FRAME_ROW_SPACING = 1
_FRAMES_PER_ROW = _PIXELS_PER_ROW * _DEVICE_COUNT // _FRAME_WIDTH
_FRAMES_PER_COL = 1 + ((_PIXELS_PER_COL - _FRAME_HEIGHT) // (_FRAME_HEIGHT + _FRAME_ROW_SPACING))
_FRAMES_PER_REGISTER = _BITS_PER_REGISTER // _FRAME_WIDTH

_VELOCITY_GAMMA = [round(191 * ((((v // 4) + 1) / 32) ** 1.7)) for v in range(128)]


class I2cDriver:
    def __init__(self):
        self.__monkey_patch_pyusb_backend()
        self._ctrl = I2cController()
        self._ctrl.configure('ftdi://ftdi:232h/1')
        self._led_registers = self._blank_led_registers()
        self._active_brightness_registers = [[[] for _ in range(_PAGE_COUNT)] for _ in range(_DEVICE_COUNT)]
        self._prev_frame = None
        self._current_page = None
        for device in range(_DEVICE_COUNT):
            address = self._get_address_for_device(device)
            port = self._ctrl.get_port(address)
            if not port.poll(relax=False):
                raise Exception(f'Could not connect to display at address {address:#04x}')

            print(f'Initialising display at address {address:#04x}')

            for page in range(_PAGE_COUNT):
                port.write([_COMMAND_REGISTER, page], relax=False)

                # Set all pixels to off
                for pixel in range(_PIXELS_PER_COL * _REGISTERS_PER_ROW):
                    port.write([pixel, 0], relax=False)

                # Set brightness to max (ready for when we switch them on)
                for pixel in range(_PWM_REG_OFFSET, _PWM_REG_OFFSET + _PIXELS_PER_COL * _PIXELS_PER_ROW):
                    port.write([pixel, 255], relax=False)

            port.write([_COMMAND_REGISTER, _FUNCTION_REGISTER], relax=False)
            port.write([_SHUTDOWN_REGISTER, 1], relax=False)

        self.display_page(0)

    def clear(self):
        for device in range(_DEVICE_COUNT):
            port = self._ctrl.get_port(self._get_address_for_device(device))
            for page in range(_PAGE_COUNT):
                port.write([_COMMAND_REGISTER, page], relax=False)
                for reg_addr in range(_PIXELS_PER_COL * _REGISTERS_PER_ROW):
                    port.write([reg_addr, 0], relax=False)
                for register in self._active_brightness_registers[device][page]:
                    port.write([register, 255], relax=False)
                self._active_brightness_registers[device][page].clear()
        self.display_page(0)

    def display_frame(self, index, frame):
        if index >= _FRAMES_PER_ROW * _PAGE_COUNT * (_FRAMES_PER_COL - 1):
            return

        line = (index // _FRAMES_PER_ROW)
        page = 0 if line == 0 else line - 1
        row = 0 if line == 0 else 1
        col = (index % _FRAMES_PER_ROW)

        self._display_frame_at(frame, page, row, col)

        self._prev_frame = (frame, page, row, col)

    def _display_frame_at(self, frame, page, row, col):
        (device, port) = self._get_device_for_column(col)

        if page != self._current_page:
            self.display_page(page)

        reg_offset = ((col % (_REGISTERS_PER_ROW * _FRAMES_PER_REGISTER)) // _FRAMES_PER_REGISTER) + (
            (_FRAMES_PER_REGISTER * (_FRAME_HEIGHT + _FRAME_ROW_SPACING) * row))
        shift = _FRAME_WIDTH * (col % _FRAMES_PER_REGISTER)

        for led_row in range(_FRAME_HEIGHT):
            reg_addr = reg_offset + _REGISTERS_PER_ROW * led_row
            current = self._led_registers[led_row]
            value = current
            for col in range(_FRAME_WIDTH):
                bit = (1 << col) << shift
                if frame.velocities[(_FRAME_WIDTH * led_row) + col] > 0:
                    value = value | bit
                else:
                    value = value & ~bit
            if value != current:
                port.write([reg_addr, value], relax=True)
                self._led_registers[led_row] = value

    def display_page(self, page):
        print(f'Going to page {page}')
        self._current_page = page
        self._led_registers = self._blank_led_registers()
        for device in range(_DEVICE_COUNT):
            port = self._ctrl.get_port(self._get_address_for_device(device))
            port.write([_COMMAND_REGISTER, _FUNCTION_REGISTER], relax=False)
            port.write([_DISPLAY_REGISTER, self._current_page], relax=False)
            port.write([_COMMAND_REGISTER, self._current_page], relax=True)

    def next_frame(self):
        if self._prev_frame:
            (frame, page, row, col) = self._prev_frame

            (device, port) = self._get_device_for_column(col)

            if row == _FRAMES_PER_COL - 1:
                self._set_frame_velocities(frame, device, port, page + 1, col, 0)

                if (col + 1) % _FRAMES_PER_REGISTER == 0:
                    reg_offset = (col % (_REGISTERS_PER_ROW * _FRAMES_PER_REGISTER)) // _FRAMES_PER_REGISTER
                    for led_row in range(_FRAME_HEIGHT):
                        reg_addr = reg_offset + _REGISTERS_PER_ROW * led_row
                        port.write([reg_addr, self._led_registers[led_row]], relax=False)

            if (col + 1) % _FRAMES_PER_REGISTER == 0:
                self._led_registers = self._blank_led_registers()

            self._set_frame_velocities(frame, device, port, page, col, row)

            self._prev_frame = None
        return

    def _set_frame_velocities(self, frame, device, port, page, col, row):
        port.write([_COMMAND_REGISTER, page], relax=False)
        x_offset = _FRAME_WIDTH * (col % (_PIXELS_PER_ROW // _FRAME_WIDTH))
        y_offset = row * (_FRAME_HEIGHT + _FRAME_ROW_SPACING)
        for (pixel, velocity) in enumerate(frame.velocities):
            if velocity > 0:
                register = (_PWM_REG_OFFSET +
                            _PIXELS_PER_ROW * (y_offset + pixel // _FRAME_HEIGHT) +
                            (x_offset + pixel % _FRAME_WIDTH))
                port.write([register, _VELOCITY_GAMMA[velocity]], False)
                self._active_brightness_registers[device][page].append(register)

    def _get_device_for_column(self, col):
        device = col // _DEVICE_COUNT
        port = self._ctrl.get_port(self._get_address_for_device(device))
        return device, port

    @staticmethod
    def _blank_led_registers():
        return [0 for _ in range(_FRAME_HEIGHT)]

    @staticmethod
    def _get_address_for_device(device):
        return _BASE_ADDRESS + device

    @staticmethod
    def __monkey_patch_pyusb_backend():
        """Monkey patch pyusb to avoid OSError on Windows
        See https://github.com/pyusb/pyusb/pull/227
        """
        import logging
        pyusb_logger = logging.getLogger('usb.backend.libusb1')
        from usb.libloader import LibraryException
        from usb.backend import libusb1

        def patched_get_backend(find_library=None):
            try:
                if libusb1._lib is None:
                    libusb1._lib = libusb1._load_library(find_library=find_library)
                    libusb1._setup_prototypes(libusb1._lib)
                if libusb1._lib_object is None:
                    libusb1._lib_object = libusb1._LibUSB(libusb1._lib)
                return libusb1._lib_object
            except LibraryException:
                # exception already logged (if any)
                pyusb_logger.error('Error loading libusb 1.0 backend', exc_info=False)
                return None
            except Exception:
                pyusb_logger.error('Error loading libusb 1.0 backend', exc_info=True)
                return None

        libusb1.get_backend = patched_get_backend