from pyftdi.i2c import I2cController

# Register addresses (see IS31FL3731 docs)
_COMMAND_REGISTER = 0xfd
_SHUTDOWN_REGISTER = 0x0a
_FUNCTION_REGISTER = 0x0b
_PWM_REG_OFFSET = 0x24

# Device properties
_BASE_ADDRESS = 0x74
_BITS_PER_REGISTER = 8
_DEVICE_COUNT = 4
_COL_COUNT = 16
_ROW_COUNT = 9
_REGISTERS_PER_ROW = _COL_COUNT // _BITS_PER_REGISTER

# Frame layout
_FRAME_WIDTH = 4
_FRAME_HEIGHT = 4
_FRAME_ROW_SPACING = 1
_FRAMES_PER_ROW = _COL_COUNT * _DEVICE_COUNT // _FRAME_WIDTH
_FRAMES_PER_COL = 1 + ((_ROW_COUNT - _FRAME_HEIGHT) // (_FRAME_HEIGHT + _FRAME_ROW_SPACING))
_TOTAL_FRAMES = _FRAMES_PER_ROW * _FRAMES_PER_COL
_FRAMES_PER_REGISTER = _BITS_PER_REGISTER // _FRAME_WIDTH

_VELOCITY_GAMMA = [round(191 * ((((v // 4) + 1) / 32) ** 1.7)) for v in range(128)]


class I2cDriver:
    def __init__(self):
        self.__monkey_patch_pyusb_backend()
        self._ctrl = I2cController()
        self._ctrl.configure('ftdi://ftdi:232h/1', frequency=400000.0)
        self._led_registers = [[0 for _ in range(_ROW_COUNT * _REGISTERS_PER_ROW)] for _ in range(_DEVICE_COUNT)]
        self._active_brightness_registers = [[] for _ in range(_DEVICE_COUNT)]
        self._prev_frame = None
        for matrix in range(_DEVICE_COUNT):
            address = self._get_address_for_matrix(matrix)
            port = self._ctrl.get_port(address)
            if not port.poll(relax=False):
                raise Exception(f'Could not connect to display at address {address:#04x}')

            print(f'Initialising display at address {address:#04x}')
            port.write([_COMMAND_REGISTER, 0], relax=False)

            # Set all pixels to off
            for pixel in range(_ROW_COUNT * _REGISTERS_PER_ROW):
                port.write([pixel, 0], relax=False)

            # Set brightness to max (ready for when we switch them on)
            for pixel in range(_PWM_REG_OFFSET, _PWM_REG_OFFSET + _ROW_COUNT * _COL_COUNT):
                port.write([pixel, 255], relax=False)

            port.write([_COMMAND_REGISTER, _FUNCTION_REGISTER], relax=False)
            port.write([_SHUTDOWN_REGISTER, 1], relax=False)

            # Write to frame buffer zero from here on
            port.write([_COMMAND_REGISTER, 0], relax=True)

    def clear(self):
        for matrix in range(_DEVICE_COUNT):
            port = self._ctrl.get_port(self._get_address_for_matrix(matrix))
            for reg_addr in range(_ROW_COUNT * _REGISTERS_PER_ROW):
                port.write([reg_addr, 0], relax=False)
                self._led_registers[matrix][reg_addr] = 0
            for register in self._active_brightness_registers[matrix]:
                port.write([register, 255], relax=False)
            self._active_brightness_registers[matrix].clear()

    def display_frame(self, index, frame):
        if index >= _TOTAL_FRAMES:
            return

        (matrix, port) = self._get_matrix_for_index(index)

        reg_offset = ((index % (_REGISTERS_PER_ROW * _FRAMES_PER_REGISTER)) // _FRAMES_PER_REGISTER) + (
            (_FRAMES_PER_REGISTER * (_FRAME_HEIGHT + _FRAME_ROW_SPACING) * (index // _FRAMES_PER_ROW)))
        shift = _FRAME_WIDTH * (index % _FRAMES_PER_REGISTER)

        for row in range(_DEVICE_COUNT):
            reg_addr = reg_offset + _REGISTERS_PER_ROW * row
            current = self._led_registers[matrix][reg_addr]
            value = current
            for col in range(_FRAME_WIDTH):
                bit = (1 << col) << shift
                if frame.velocities[(_FRAME_WIDTH * row) + col] > 0:
                    value = value | bit
                else:
                    value = value & ~bit
            if value != current:
                port.write([reg_addr, value], relax=True)
                self._led_registers[matrix][reg_addr] = value

        self._prev_frame = (index, frame)

    def next_frame(self):
        if self._prev_frame:
            (index, frame) = self._prev_frame
            (matrix, port) = self._get_matrix_for_index(index)

            x_offset = _FRAME_WIDTH * (index % (_COL_COUNT // _FRAME_WIDTH))
            y_offset = (index // _FRAMES_PER_ROW) * (_FRAME_HEIGHT + _FRAME_ROW_SPACING)
            for (pad, velocity) in enumerate(frame.velocities):
                if velocity > 0:
                    register = (_PWM_REG_OFFSET +
                                _COL_COUNT * (y_offset + pad // _FRAME_HEIGHT) +
                                (x_offset + pad % _FRAME_WIDTH))
                    port.write([register, _VELOCITY_GAMMA[velocity]], False)
                    self._active_brightness_registers[matrix].append(register)

            self._prev_frame = None

    def _get_matrix_for_index(self, index):
        matrix = ((index % _FRAMES_PER_ROW) // _DEVICE_COUNT)
        port = self._ctrl.get_port(self._get_address_for_matrix(matrix))
        return matrix, port

    @staticmethod
    def _get_address_for_matrix(matrix):
        return _BASE_ADDRESS + matrix

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