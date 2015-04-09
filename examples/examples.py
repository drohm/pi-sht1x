from time import sleep
import RPi.GPIO as GPIO
from pi_sht1x import SHT1x

DATA_PIN = 18
SCK_PIN = 23


def main():
    print('Test: using default values: 3.5V, High resolution, no heater, otp_no_reload off, CRC checking enabled...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM) as sensor:
        for i in range(5):
            temp = sensor.read_temperature()
            humidity = sensor.read_humidity(temp)
            sensor.calculate_dew_point(temp, humidity)
            print(sensor)
            sleep(2)
    print('Test complete.\n')

    print('Test: reading all measurements using GPIO.BCM mode, 3V, High resolution, heater off, otp_no_reload off, '
          'and CRC check on.')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM, vdd='3.5V', resolution='High',
               heater=False, otp_no_reload=False, crc_check=True) as sensor:
        for i in range(5):
            temp = sensor.read_temperature()
            humidity = sensor.read_humidity(temp)
            sensor.calculate_dew_point(temp, humidity)
            print(sensor)
            sleep(2)
    print('Test complete.\n')

    print('Test: read humidity without providing the temperature as an argument...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM) as sensor:
        for i in range(5):
            sensor.read_humidity()
            print('Temperature: {0}*C [{1}*F]\nHumidity: {2}'.format(sensor.temperature_celsius,
                                                                     sensor.temperature_fahrenheit, sensor.humidity))
            sleep(2)
    print('Test complete.\n')

    print('Test: calculate dew point without providing temperature and humidity as arguments...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM) as sensor:
        for i in range(5):
            sensor.calculate_dew_point()
            print(sensor)
            sleep(2)
    print('Test complete.\n')

    print('Test: turn otp_no_reload on...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM, otp_no_reload=True) as sensor:
        for i in range(5):
            temp = sensor.read_temperature()
            humidity = sensor.read_humidity(temp)
            sensor.calculate_dew_point(temp, humidity)
            print(sensor)
            sleep(2)
    print('Test complete.\n')

    print('Test: use low resolution...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM, resolution='Low') as sensor:
        for i in range(5):
            temp = sensor.read_temperature()
            humidity = sensor.read_humidity(temp)
            sensor.calculate_dew_point(temp, humidity)
            print(sensor)
            sleep(2)
    print('Test complete.\n')

    print('Test: change resolution after object creation...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM) as sensor:
        print('High resolution...')
        for i in range(5):
            temp = sensor.read_temperature()
            humidity = sensor.read_humidity(temp)
            sensor.calculate_dew_point(temp, humidity)
            print(sensor)
            sleep(2)
        print('Complete.\n')

        sensor.resolution = SHT1x.RESOLUTION['Low']
        print('Low resolution...')
        for i in range(5):
            temp = sensor.read_temperature()
            humidity = sensor.read_humidity(temp)
            sensor.calculate_dew_point(temp, humidity)
            print(sensor)
            sleep(2)
    print('Test complete.\n')

    print('Test: Read the Status Register (default)...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM) as sensor:
        status_register = sensor.read_status_register()
        print('Status Register: {0:08b}'.format(status_register))
    print('Test complete.\n')

    print('Test: Read the Status Register (low resolution, otp_no_reload on)...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM, resolution='Low', otp_no_reload=True) as sensor:
        status_register = sensor.read_status_register()
        print('Status Register: {0:08b}'.format(status_register))
    print('Test complete.\n')

    print('Test: resetting the connection to the sensor...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM) as sensor:
        sensor.reset_connection()
        sensor.read_temperature()
        print('Temperature: {0}*C [{1}*F]'.format(sensor.temperature_celsius, sensor.temperature_fahrenheit))
    print('Test complete.\n')

    print('Test: performing a soft reset of the sensor...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM, otp_no_reload=True) as sensor:
        sensor.soft_reset()
        status_register = sensor.read_status_register()
        print('Status Register: {0:08b}'.format(status_register))
        sensor.read_temperature()
        print('Temperature: {0}*C [{1}*F]'.format(sensor.temperature_celsius, sensor.temperature_fahrenheit))
    print('Test complete.\n')

    print('Test: resetting the status register...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM, otp_no_reload=True) as sensor:
        sensor.reset_status_register()
        status_register = sensor.read_status_register()
        print('Status Register: {0:08b}'.format(status_register))
        sensor.read_temperature()
        print('Temperature: {0}*C [{1}*F]'.format(sensor.temperature_celsius, sensor.temperature_fahrenheit))
    print('Test complete.\n')

    print('Test: CRC disabled...')
    with SHT1x(DATA_PIN, SCK_PIN, gpio_mode=GPIO.BCM, vdd='3.5V', resolution='High',
               heater=False, otp_no_reload=False, crc_check=False) as sensor:
        for i in range(5):
            temp = sensor.read_temperature()
            humidity = sensor.read_humidity(temp)
            sensor.calculate_dew_point(temp, humidity)
            print(sensor)
            sleep(2)
    print('Test complete.\n')


if __name__ == "__main__":
    main()

