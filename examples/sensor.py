from time import sleep
import argparse
import RPi.GPIO as GPIO
from pi_sht1x import SHT1x

import logging
import sys

logger = logging.getLogger()
logging.basicConfig(stream=sys.stdout, level=logging.ERROR)


class Choices(list):
    def __contains__(self, item):
        return super(Choices, self).__contains__(item.upper())


def main():
    vdd_choices = Choices(['5V', '4V', '3.5V', '3V', '2.5V'])
    resolution_choices = Choices(['HIGH', 'LOW'])

    parser = argparse.ArgumentParser(description='Reads the temperature and relative humidity from the SHT1x series '
                                                 'of sensors using the pi_sht1x library.')
    parser.add_argument('data_pin', type=int, metavar='data-pin', help='Data pin used to connect to the sensor.')
    parser.add_argument('sck_pin', type=int, metavar='sck-pin', help='SCK pin used to connect to the sensor.')
    parser.add_argument('-g', '--gpio-mode', choices=['BCM', 'BOARD'], default='BCM',
                        help='RPi.GPIO mode used, either GPIO.BOARD or GPIO.BCM. Defaults to GPIO.BCM.')
    parser.add_argument('-v', '--vdd', choices=vdd_choices, default='3.5V',
                        help='Voltage used to power the sensor. Defaults to 3.5V.')
    parser.add_argument('-r', '--resolution', choices=resolution_choices, default='HIGH',
                        help='Resolution used by the sensor, 14/12-bit or 12-8-bit. Defaults to High.')
    parser.add_argument('-e', '--heater', action='store_true',
                        help='Used to turn the internal heater on (used for calibration).')
    parser.add_argument('-o', '--otp-no-reload', action='store_true',
                        help='Used to enable OTP no reload, will save about 10ms per measurement.')
    parser.add_argument('-c', '--no-crc-check', action='store_false', help='Performs CRC checking.')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging.')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    mode = GPIO.BCM if args.gpio_mode.upper() == 'BCM' else GPIO.BOARD
    with SHT1x(args.data_pin, args.sck_pin, gpio_mode=mode, vdd=args.vdd, resolution=args.resolution,
               heater=args.heater, otp_no_reload=args.otp_no_reload, crc_check=args.no_crc_check,
               logger=logger) as sensor:
        for i in range(5):
            temp = sensor.read_temperature()
            humidity = sensor.read_humidity(temp)
            sensor.calculate_dew_point(temp, humidity)
            print(sensor)
            sleep(2)


if __name__ == "__main__":
    main()
