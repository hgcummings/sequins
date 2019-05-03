from pyftdi.i2c import I2cController


class I2cDriver:
    def __init__(self):
        self.__monkey_patch_pyusb_backend()
        self._ctrl = I2cController()
        self._ctrl.configure('ftdi://ftdi:232h/1', frequency=400000.0)
        self._led_registers = [[0 for _ in range(18)] for _ in range(4)]
        self._active_brightness_registers = [[] for _ in range(4)]
        self._prev_frame = None
        for address in range(0x74, 0x78):
            port = self._ctrl.get_port(address)
            if not port.poll(relax=False):
                raise Exception(f'Could not connect to display at address {address:#04x}')

            print(f'Initialising display at address {address:#04x}')
            port.write([0xfd, 0x00], relax=False)

            print(f' - Initialising registers')
            # Set all pixels to off
            for pixel in range(0x12):
                port.write([pixel, 0], relax=False)

            # And set colour to white
            for pixel in range(0x24, 0xB4):
                port.write([pixel, 255], relax=False)

            print(f' - Starting')
            port.write([0xfd, 0x0b], relax=False)
            port.write([0x0a, 1], relax=False)

            # Write to frame buffer zero from here on
            port.write([0xfd, 0x00], relax=True)

    def clear(self):
        for matrix in range(4):
            port = self._ctrl.get_port(0x74 + matrix)
            for reg_addr in range(0x12):
                port.write([reg_addr, 0], relax=False)
                self._led_registers[matrix][reg_addr] = 0
            for register in self._active_brightness_registers[matrix]:
                port.write([register, 255], relax=False)
            self._active_brightness_registers[matrix].clear()

    def display_frame(self, index, frame):
        if index >= 32:
            return

        (matrix, port) = self._get_matrix_for_index(index)

        reg_offset = ((index % 4) // 2) + (0x0a if index >= 16 else 0)
        shift = 4 if index % 2 == 1 else 0

        for row in range(4):
            reg_addr = reg_offset + 2 * row
            current = self._led_registers[matrix][reg_addr]
            value = current
            for col in range(4):
                bit = (1 << col) << shift
                if frame.velocities[(4 * row) + col] > 0:
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

            x_offset = 4 * (index % 4)
            y_offset = 0 if index < 16 else 5
            for (pad, velocity) in enumerate(frame.velocities):
                if velocity > 0:
                    register = 0x24 + 16 * (y_offset + pad // 4) + (x_offset + pad % 4)
                    port.write([register, velocity], False)
                    self._active_brightness_registers[matrix].append(register)

            self._prev_frame = None

    def _get_matrix_for_index(self, index):
        matrix = ((index % 16) // 4)
        port = self._ctrl.get_port(0x74 + matrix)
        return matrix, port


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