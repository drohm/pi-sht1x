"""
SHT1x library
"""
import time
import math


class SHT1xError(Exception):
    pass


try:
    import RPi.GPIO as GPIO
except ImportError:
    raise SHT1xError('Could not import the RPi.GPIO package (http://pypi.python.org/pypi/RPi.GPIO). Exiting.')

GPIO_FUNCS = {-1: 'GPIO.UNKNOWN', 0: 'GPIO.OUT', 1: 'GPIO.IN', 10: 'GPIO.BOARD', 11: 'GPIO.BCM',
              40: 'GPIO.SERIAL', 41: "GPIO.SPI", 42: "GPIO.I2C", 43: "GPIO.HARD_PWM"}


class COF():
    D1_VDD_C = {5: -40.1, 4: -39.8, 3.5: -39.7, 3: -39.6, 2.5: -39.4}
    D1_VDD_F = {5: -40.2, 4: -39.6, 3.5: -39.5, 3: -39.3, 2.5: -38.9}
    D2_SO_C = {14: 0.01, 12: 0.04}
    D2_SO_F = {14: 0.018, 12: 0.072}
    C1_SO = {12: -2.0468, 8: -2.0468}
    C2_SO = {12: 0.0367, 8: 0.5872}
    C3_SO = {12: -0.0000015955, 8: -0.00040845}
    T1_SO = {12: 0.01, 8: 0.01}
    T2_SO = {12: 0.00008, 8: 0.00128}


class CRC():
    LOOK_UP = [0, 49, 98, 83, 196, 245, 166, 151, 185, 136, 219, 234, 125, 76, 31, 46, 67, 114, 33, 16, 135,
               182, 229, 212, 250, 203, 152, 169, 62, 15, 92, 109, 134, 183, 228, 213, 66, 115, 32, 17, 63,
               14, 93, 108, 251, 202, 153, 168, 197, 244, 167, 150, 1, 48, 99, 82, 124, 77, 30, 47, 184, 137,
               218, 235, 61, 12, 95, 110, 249, 200, 155, 170, 132, 181, 230, 215, 64, 113, 34, 19, 126, 79,
               28, 45, 186, 139, 216, 233, 199, 246, 165, 148, 3, 50, 97, 80, 187, 138, 217, 232, 127, 78, 29,
               44, 2, 51, 96, 81, 198, 247, 164, 149, 248, 201, 154, 171, 60, 13, 94, 111, 65, 112, 35, 18,
               133, 180, 231, 214, 122, 75, 24, 41, 190, 143, 220, 237, 195, 242, 161, 144, 7, 54, 101, 84,
               57, 8, 91, 106, 253, 204, 159, 174, 128, 177, 226, 211, 68, 117, 38, 23, 252, 205, 158, 175,
               56, 9, 90, 107, 69, 116, 39, 22, 129, 176, 227, 210, 191, 142, 221, 236, 123, 74, 25, 40, 6,
               55, 100, 85, 194, 243, 160, 145, 71, 118, 37, 20, 131, 178, 225, 208, 254, 207, 156, 173, 58,
               11, 88, 105, 4, 53, 102, 87, 192, 241, 162, 147, 189, 140, 223, 238, 121, 72, 27, 42, 193, 240,
               163, 146, 5, 52, 103, 86, 120, 73, 26, 43, 188, 141, 222, 239, 130, 179, 224, 209, 70, 119, 36,
               21, 59, 10, 89, 104, 255, 206, 157, 172]


class SHT1x:
    Commands = {'Temperature': 0b00000011,
                'Humidity': 0b00000101,
                'ReadStatusRegister': 0b00000111,
                'WriteStatusRegister': 0b00000110,
                'SoftReset': 0b00011110,
                'NoOp': 0b00000000}
    RESOLUTION = {'High': [14, 12], 'Low': [12, 8]}
    VDD = {'5V': 5, '4V': 4, '3.5V': 3.5, '3V': 3, '2.5V': 2.5}

    def __init__(self, data_pin, sck_pin, gpio_mode=GPIO.BOARD, vdd='3.5V', resolution='High',
                 heater=False, otp_no_reload=False, crc_check=True, logger=None):
        self.data_pin = data_pin
        self.sck_pin = sck_pin
        self.gpio_mode = gpio_mode
        self.vdd = self.VDD.get(vdd.upper(), self.VDD['3.5V'])
        self._resolution = self.RESOLUTION.get(resolution.capitalize(), self.RESOLUTION['High'])
        self._heater = heater
        self._otp_no_reload = otp_no_reload
        self.crc_check = crc_check
        self._command = self.Commands['NoOp']
        self._status_register = 0b00000000
        self.temperature_celsius = None
        self.temperature_fahrenheit = None
        self.humidity = None
        self.dew_point = None
        self._logger = logger

        GPIO.setmode(self.gpio_mode)
        self.initialize_sensor()

        self.logger.info('Initial configuration:\nData Pin: {0}\nClock Pin: {1}\nGPIO mode: {2}\nVdd: {3}\n'
                         'Resolution: {4}\nHeater: {5}\nOTP no reload: {6}\nCRC check: {7}'
                         .format(self.data_pin, self.sck_pin, GPIO_FUNCS[gpio_mode], self.vdd, resolution,
                                 self._heater, self._otp_no_reload, self.crc_check))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.info('GPIO channel function status:\nData pin [{0}]: {1}\nClock pin [{2}]: {3}'
                         .format(self.data_pin, GPIO_FUNCS[GPIO.gpio_function(self.data_pin)],
                                 self.sck_pin, GPIO_FUNCS[GPIO.gpio_function(self.sck_pin)]))
        GPIO.cleanup()
        if exc_type is not None:
            self.logger.error('Exception in with block: {0}\n{1}\n{2}'.format(exc_type, exc_val, exc_tb))
            return False

    @property
    def heater(self):
        return self._heater

    @heater.setter
    def heater(self, value):
        self._heater = value
        self.initialize_sensor()

    @property
    def otp_no_reload(self):
        return self._otp_no_reload

    @otp_no_reload.setter
    def otp_no_reload(self, value):
        self._otp_no_reload = value
        self.initialize_sensor()

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    def resolution(self, value):
        self._resolution = value
        self.initialize_sensor()

    @property
    def logger(self):
        """
        A :class:`logging.Logger` object for this application.
        """
        if self._logger:
            return self._logger
        from pi_sht1x.logging import create_logger
        self._logger = create_logger(__name__)
        return self._logger

    def initialize_sensor(self):
        """
        Resets the connection to the sensor and then initializes the SHT1x's status register based on the values
        of the object:
            Heater: default is 0
            No reload from OTP: default is 0
            Resolution: default is 0
        The status register mask is built based on the object attributes.

        :return: None.
        """
        self.reset_connection()

        mask = 0
        if self._heater:
            mask += 4
        if self._otp_no_reload:
            mask += 2
        if self._resolution[0] == self.RESOLUTION['Low'][0]:
            mask += 1

        self.logger.info('Initializing sensor using bit mask: {0:08b}'.format(mask))
        self._write_status_register(mask)

    def read_temperature(self):
        """
        Sends command to the SHT1x sensor to read the temperature. Values for both celsius and fahrenheit are
        calculated.
        :return: String.
        """
        self._command = self.Commands['Temperature']
        self._send_command()
        raw_temperature = self._read_measurement()

        self.temperature_celsius = round(raw_temperature * COF.D2_SO_C[self._resolution[0]] +
                                         COF.D1_VDD_C[self.vdd], 2)
        self.temperature_fahrenheit = round(raw_temperature * COF.D2_SO_F[self._resolution[0]] +
                                            COF.D1_VDD_F[self.vdd], 2)

        self.logger.info('Temperature: {0}*C [{1}*F]'.format(self.temperature_celsius, self.temperature_fahrenheit))
        return self.temperature_celsius

    def read_humidity(self, temperature=None):
        """
        Sends command to the SHT1x sensor to read the temperature compensated humidity. If the read_temperature
        function has not been called previously and the temperature parameter is not used, it will read the
        temperature from the sensor.

        :param temperature: Optional, temperature, in celsius, used to compensate when temperatures are significantly
        different from 25C (~77F) when calculating relative humidity.
        :return: String.
        """
        if temperature is None:
            if self.temperature_celsius is None:
                self.read_temperature()
            temperature = self.temperature_celsius

        self._command = self.Commands['Humidity']
        self._send_command()
        raw_humidity = self._read_measurement()

        linear_humidity = COF.C1_SO[self._resolution[1]] + (COF.C2_SO[self._resolution[1]] * raw_humidity) + (
            COF.C3_SO[self._resolution[1]] * raw_humidity ** 2)

        self.humidity = round((temperature - 25) * (
            COF.T1_SO[self._resolution[1]] + COF.T2_SO[self._resolution[1]] * raw_humidity) + linear_humidity, 2)

        self.logger.info('Relative Humidity: {0}%'.format(self.humidity))
        return self.humidity

    def calculate_dew_point(self, temperature=None, humidity=None):
        """
        Calculates the dew point, based on the given temperature and humidity. If the temperature or humidity are not
        given it will read in the values from the sensor.

        :param temperature: Temperature in degrees celsius.
        :param humidity: Humidity.
        :return:
        """
        if temperature is None:
            if self.temperature_celsius is None:
                self.read_temperature()
            temperature = self.temperature_celsius

        if humidity is None:
            if self.humidity is None:
                self.read_humidity(self.temperature_celsius)
            humidity = self.humidity

        tn = 243.12
        m = 17.62
        if self.temperature_celsius <= 0:
            tn = 272.62
            m = 22.46

        log_humidity = math.log(humidity / 100.0)
        ew = (m * temperature) / (tn + temperature)
        self.dew_point = round(tn * (log_humidity + ew) / m - (log_humidity + ew), 2)

        self.logger.info('Dew Point: {0}*C'.format(self.dew_point))
        return self.dew_point

    def _send_command(self, measurement=True):
        """
        Sends the given command to the SHT1x sensor and verifies acknowledgement. If the command is for
        taking a measurement it will also ensure that the measurement is taking place and waits for the
        measurement to complete.

        :param measurement: Indicates if the command is for taking a measurement for temperature or humidity.
        :return: None.
        """
        command_name = [key for key in self.Commands.keys() if self.Commands[key] == self._command]
        if not command_name:
            message = "The command was not found: {0}".format(self._command)
            self.logger.error(message)
            raise SHT1xError(message)

        self._transmission_start()
        self._send_byte(self._command)
        self._get_ack(command_name)

        if measurement:
            ack = GPIO.input(self.data_pin)
            self.logger.info('SHT1x is taking measurement.')
            if ack == GPIO.LOW:
                message = 'SHT1x is not in the proper measurement state: DATA line is LOW.'
                self.logger.error(message)
                raise SHT1xError(message)

            self._wait_for_result()

    def _wait_for_result(self):
        """
        Waits for the sensor to complete measurement. The time to complete depends
        on the number of bits used for measurement:
            8-bit:  20ms
            12-bit: 80ms
            14-bit: 320ms
        Raises an exception if the Data Ready signal hasn't been received after 350 milliseconds.
        :return: None
        """
        GPIO.setup(self.data_pin, GPIO.IN)
        data_ready = GPIO.HIGH

        for i in range(35):
            time.sleep(.01)
            data_ready = GPIO.input(self.data_pin)
            if data_ready == GPIO.LOW:
                self.logger.debug('Measurement complete.')
                break

        if data_ready == GPIO.HIGH:
            raise SHT1xError('Sensor has not completed measurement after max time allotment.\n{0}'.format(self))

    def _read_measurement(self):
        """
        Reads the measurement data from the SHT1x sensor. If crc_check is set to True the CRC value
        will be read and verified, otherwise the transmission will end.
        :return: 16-bit value.
        """
        # Get the MSB
        value = self._get_byte()
        value <<= 8

        self._send_ack()

        # Get the LSB
        value |= self._get_byte()

        if self.crc_check:
            self._validate_crc(value)
        else:
            self._transmission_end()

        return value

    def _get_byte(self):
        """
        Reads a single byte from the SHT1x sensor.
        :return: 8-bit value.
        """
        GPIO.setup(self.data_pin, GPIO.IN)
        GPIO.setup(self.sck_pin, GPIO.OUT)

        data = 0b00000000
        for i in range(8):
            self._toggle_pin(self.sck_pin, GPIO.HIGH)
            data |= GPIO.input(self.data_pin) << (7 - i)
            self._toggle_pin(self.sck_pin, GPIO.LOW)

        return data

    def _send_byte(self, data):
        """
        Sends a single byte to the SHT1x sensor
        :param data: Byte of data to send.
        :return: None
        """
        GPIO.setup(self.data_pin, GPIO.OUT)
        GPIO.setup(self.sck_pin, GPIO.OUT)

        for i in range(8):
            self._toggle_pin(self.data_pin, data & (1 << 7 - i))
            self._toggle_pin(self.sck_pin, GPIO.HIGH)
            self._toggle_pin(self.sck_pin, GPIO.LOW)

    def _toggle_pin(self, pin, state):
        """
        Toggles the state of the specified pin. If the specified pin is the SCK pin, it will sleep
        for 100ns after setting its new state.
        :param pin: Pin to toggle state.
        :param state: State to change the pin, GPIO.LOW or GPIO.HIGH.
        :return: None.
        """
        GPIO.output(pin, state)
        if pin == self.sck_pin:
            time.sleep(0.0000001)

    def _transmission_start(self):
        """
        Sends the transmission start sequence to the sensor to initiate communication.
        :return: None
        """
        GPIO.setup(self.data_pin, GPIO.OUT)
        GPIO.setup(self.sck_pin, GPIO.OUT)

        self._toggle_pin(self.data_pin, GPIO.HIGH)
        self._toggle_pin(self.sck_pin, GPIO.HIGH)
        self._toggle_pin(self.data_pin, GPIO.LOW)
        self._toggle_pin(self.sck_pin, GPIO.LOW)
        self._toggle_pin(self.sck_pin, GPIO.HIGH)
        self._toggle_pin(self.data_pin, GPIO.HIGH)
        self._toggle_pin(self.sck_pin, GPIO.LOW)

    def _transmission_end(self):
        """
        Sends skip ACK by keeping the DATA line high to bypass CRC and end transmission.
        :return: None.
        """
        GPIO.setup(self.data_pin, GPIO.OUT)
        GPIO.setup(self.sck_pin, GPIO.OUT)

        self._toggle_pin(self.data_pin, GPIO.HIGH)
        self._toggle_pin(self.sck_pin, GPIO.HIGH)
        self._toggle_pin(self.sck_pin, GPIO.LOW)

    def _get_ack(self, command_name):
        """
        Gets ACK from the SHT1x confirming data was received by the sensor.
        :param command_name: Command issued to the sensor.
        :return: None
        """
        GPIO.setup(self.data_pin, GPIO.IN)
        GPIO.setup(self.sck_pin, GPIO.OUT)

        self._toggle_pin(self.sck_pin, GPIO.HIGH)

        ack = GPIO.input(self.data_pin)
        self.logger.info('Command {0} [{1:08b}] acknowledged: {1}'.format(command_name, self._command, ack))
        if ack == GPIO.HIGH:
            message = 'SHT1x failed to properly receive command [{0} - {1:08b}]'.format(command_name, self._command)
            self.logger.error(message)
            raise SHT1xError(message)

        self._toggle_pin(self.sck_pin, GPIO.LOW)

    def _send_ack(self):
        """
        Sends ACK to the SHT1x confirming byte measurement data was received by the caller.
        :return: None.
        """
        GPIO.setup(self.data_pin, GPIO.OUT)
        GPIO.setup(self.sck_pin, GPIO.OUT)

        self._toggle_pin(self.data_pin, GPIO.HIGH)
        self._toggle_pin(self.data_pin, GPIO.LOW)
        self._toggle_pin(self.sck_pin, GPIO.HIGH)
        self._toggle_pin(self.sck_pin, GPIO.LOW)

    def read_status_register(self):
        """
        Retrieves the contents of the Status Register as a binary integer.
        :return: None.
        """
        self._command = self.Commands['ReadStatusRegister']
        self._send_command(measurement=False)
        self._status_register = self._get_byte()
        self.logger.debug("Status Register read: {0:08b}".format(self._status_register))

        if self.crc_check:
            self._validate_crc(self._status_register, measurement=False)
        else:
            self._transmission_end()

        self.logger.info("Read Status Register: {0:08b}".format(self._status_register))
        return self._status_register

    def _write_status_register(self, mask):
        """
        Writes the 8-bit value to the Status Register. Only bits 0-2 are R/W, bits 3-7 are read-only.

            bit 2 - Heater: defaults to off
              0: heater off
              1: heater on
            bit 1 - no reload from OTP: defaults to off
              0: reload on
              1: reload off
            bit 0 - measurement resolution: defaults to 0
              0: 14bit Temp/12bit RH
              1: 12bit Temp/8bit RH

            Example value: 0b00000010
                This value uses the highest measurement resolution (14bit Temp/12bit RH), no reload from OTP is enabled
                and the heater is off.

        :param mask: Binary integer used to write to the Status Register.
        :return: None.
        """
        self._command = self.Commands['WriteStatusRegister']
        self._send_command(measurement=False)
        self.logger.info("Writing Status Register: {0:08b}".format(mask))

        self._send_byte(mask)
        self._get_ack('WriteStatusRegister')
        self._status_register = mask

    def reset_status_register(self):
        """
        Resets the Status Register to its default values.
        :return: None.
        """
        self._write_status_register(self.Commands['NoOp'])

    def _reverse_byte(self, data):
        """
        Reverses the byte. Uses the method from Rich Schroeppel:
            http://graphics.stanford.edu/~seander/bithacks.html#ReverseByteWith64BitsDiv
        :param data: Byte to be reversed.
        :return: Byte
        """
        return (data * 8623620610 & 1136090292240) % 1023

    def _reverse_status_register(self):
        """
        Reverses the Status Register byte.
        :return: Status Register byte reversed
        """
        sr_reversed = self._reverse_byte(self._status_register)
        crc_register = (sr_reversed >> 4) << 4
        self.logger.info("Status register reversed: {0:08b}".format(crc_register))

        return crc_register

    def _validate_crc(self, data, measurement=True):
        """
        Performs CRC validation using Byte-wise calculation.
        :param data: Data retrieved from the SHT1x sensor, either measurement data or from the Status Register.
        :param measurement: Indicates if the data parameter is from a measurement or from reading the Status Register.
        :return: None.
        """
        self._send_ack()
        crc_value = self._get_byte()
        self._transmission_end()
        self.logger.info('CRC value from sensor: {0:08b}'.format(crc_value))

        crc_start_value = self._reverse_status_register()
        self.logger.info('CRC start value: {0:08b}'.format(crc_start_value))

        crc_lookup = CRC.LOOK_UP[int(crc_start_value ^ self._command)]
        self.logger.info('CRC command lookup value: {0:08b}'.format(crc_lookup))

        self.logger.info('Sensor data (MSB and LSB): {0:016b}'.format(data))
        if measurement:
            crc_lookup = CRC.LOOK_UP[int(crc_lookup ^ (data >> 8))]
            self.logger.info('CRC MSB lookup value: {0:08b}'.format(crc_lookup))

            crc_final = CRC.LOOK_UP[int(crc_lookup ^ (data & 0b0000000011111111))]
            self.logger.info('CRC LSB lookup value: {0:08b}'.format(crc_final))
        else:
            crc_final = CRC.LOOK_UP[int(crc_lookup ^ data)]
            self.logger.info('CRC data lookup value: {0:08b}'.format(crc_final))

        crc_final_reversed = self._reverse_byte(crc_final)
        self.logger.info('CRC calculated value (reversed): {0:08b}'.format(crc_final_reversed))

        if crc_value != crc_final_reversed:
            self.soft_reset()
            message = 'CRC error! Sensor has been reset, please try again.\n' \
                      'CRC value from sensor: {0:08b}\nCRC calculated value: {1:08b}'.format(crc_value,
                                                                                             crc_final_reversed)
            self.logger.error(message)
            raise SHT1xError(message)

        return

    def reset_connection(self):
        """
        Resets the serial interface to the Sht1x sensor. The status register preserves its content.
        :return: None.
        """
        GPIO.setup(self.data_pin, GPIO.OUT)
        GPIO.setup(self.sck_pin, GPIO.OUT)

        self._toggle_pin(self.data_pin, GPIO.HIGH)
        for i in range(10):
            self._toggle_pin(self.sck_pin, GPIO.HIGH)
            self._toggle_pin(self.sck_pin, GPIO.LOW)

    def soft_reset(self):
        """
        Performs a soft reset of the SHT1x sensor. This resets the interface, clears the status register to
        default values, and waits 15ms (11ms is the recommended minimum) before next command.
        :return: None.
        """
        self._command = self.Commands['SoftReset']
        self._send_command(measurement=False)
        time.sleep(.015)
        self._status_register = 0b00000000

    def __str__(self):
        celsius = self.temperature_celsius if self.temperature_celsius is not None else '-'
        fahrenheit = self.temperature_fahrenheit if self.temperature_fahrenheit is not None else '-'
        humidity = self.humidity if self.humidity is not None else '-'
        dew_point = self.dew_point if self.dew_point is not None else '-'

        return 'Temperature: {0}*C [{1}*F]\nRelative Humidity: {2}%\nDew Point: {3}*C\n'.format(celsius, fahrenheit,
                                                                                                humidity, dew_point)


if __name__ == "__main__":
    pass
