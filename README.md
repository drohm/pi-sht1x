# pi-sht1x #
----------
The pi-sht1x package is a Python 3 library used to communicate and control the Sensirion SHT1x series of temperature and humidity sensors. It was designed to be used primarily with the Raspberry Pi and depends on the [RPi.GPIO](http://pypi.python.org/pypi/RPi.GPIO) library.

SHT1x (including SHT10, SHT11 and SHT15) is Sensirion’s family of surface mountable relative humidity and temperature sensors. The sensors integrate sensor elements plus signal processing on a tiny foot print and provide a fully calibrated digital output. A unique capacitive sensor element is used for measuring relative humidity while temperature is measured by a band-gap sensor.

The package was tested using the Raspberry Pi B+ and Raspberry Pi 2. There shouldn't be issues running this on the older models, but no guarantees. If you do run into any problems, please let me know or create an [issue](https://github.com/drohm/pi-sht1x/issues) on the GitHub project page:

	https://github.com/drohm/pi-sht1x

The data sheet for the SHT1x series of sensors can be found here:

	http://bit.ly/1Pafs6j

This library provides the following functionality:

- Taking temperature measurements
- Taking humidity measurements
- Make dew point calculations
- Change the supplied voltage (5V, 4V, 3.5V, 3V, 2.5V)
- Enable or disable CRC checking
- Reading the Status Register
- Writing to the Status Register, provides the following functionality:
    - Turn `otp_no_reload` on (will save about 10ms per measurement)
    - Turn on the internal heater element (for functionality analysis, refer to the data sheet list above for more information)
    - Change the resolution of measurements, High (14-bit temperature and 12-bit humidity) or Low (12-bit temperature and 8-bit humidity)

## Installation ##
Installation is pretty simple:

	pip3 install pi-sht1x

> Note that to install packages into the system-wide PATH and site-packages, elevated privileges are often required (sudo). You can try using `install –user` or [virtualenv](https://pypi.python.org/pypi/virtualenv) to do unprivileged installs.

## Usage ##
When instantiating a SHT1x object, the following default values are used if not specified:

	gpio_mode:		GPIO.BOARD
	vdd:			3.5V
	resolution:		High (14-bit temperature & 12-bit humidity)
	heater:			False
	otp_no_reload:	False
	crc_check:		True
	

### Command Line - REPL ###
You can invoke the SHT1x class directly from the REPL. In order to use the library you need to import the package:

	from pi_sht1x import SHT1x

Now you can create the sensor object and take measurements:

    with SHT1x(18, 23, gpio_mode=GPIO.BCM) as sensor:
        temp = sensor.read_temperature()
        humidity = sensor.read_humidity(temp)
        sensor.calculate_dew_point(temp, humidity)
        print(sensor)

This will create the SHT1x object using `data_pin=18`, `sck_pin=23`, `gpio_mode=GPIO.BCM`, and default values for `vdd` (3.5V), `resolution` (High), `heater` (False), `otp_no_reload` (False), and `crc_check` (True). The output will look something like this:

	Temperature: 24.05*C [75.25*F]
	Humidity: 22.80%
	Dew Point: 1.38*C

> Note that this library should be used with a context manager like the `with` statement. Using it with a context manager will allow the program to properly clean up after itself and reset the GPIO pins back to default states.

### examples.py ###
This script, located in the examples folder, includes several ways to use the SHT1x class to take temperature, humidity, and dew point measurements. In order to use the script, be sure to update the `DATA_PIN` and `SCK_PIN` constants near the top of the file with the pin numbers you're using locally in your setup:

	DATA_PIN = 18
	SCK_PIN = 23

Based on the fact that the data sheet recommends 3.3V to power the sensor, the default voltage, if not specified when instantiating the object, is 3.5V. If you're using 5V to power the sensor, be sure to set that value when creating the object. To run the script:

	sudo python3 examples/examples.py

Running the script exercises all of the functionality for the sensor. Be sure to look through the script to see what you can do and how to customize using the sensor. Sample output:

	$ sudo python3 examples/examples.py
	Test: using default values: 3.5V, High resolution, no heater, otp_no_reload off, CRC checking enabled...
	Temperature: 24.49*C [76.04*F]
	Humidity: 20.68%
	Dew Point: 0.47*C
	
	Temperature: 24.48*C [76.02*F]
	Humidity: 20.68%
	Dew Point: 0.46*C
	
	Temperature: 24.47*C [76.01*F]
	Humidity: 20.68%
	Dew Point: 0.45*C
	
	Temperature: 24.51*C [76.06*F]
	Humidity: 20.68%
	Dew Point: 0.47*C
	
	Temperature: 24.51*C [76.06*F]
	Humidity: 20.68%
	Dew Point: 0.47*C
	Test complete.
	
	Test: reading all measurements using GPIO.BCM mode, 3V, High resolution, heater off, otp_no_reload off, and CRC check on.
	Temperature: 24.48*C [76.02*F]
	Humidity: 20.61%
	Dew Point: 0.42*C
	
	Temperature: 24.46*C [75.98*F]
	Humidity: 20.61%
	Dew Point: 0.40*C
	
	Temperature: 24.46*C [75.98*F]
	Humidity: 20.61%
	Dew Point: 0.40*C
	
	Temperature: 24.48*C [76.02*F]
	Humidity: 20.68%
	Dew Point: 0.46*C
	
	Temperature: 24.48*C [76.02*F]
	Humidity: 20.65%
	Dew Point: 0.44*C
	Test complete.
	.
	.
	.

> The [RPi.GPIO](http://pypi.python.org/pypi/RPi.GPIO) module requires root privileges in order to communicate with the GPIO pins on the Raspberry Pi so you need to run your scripts as root (sudo).

### sensor.py ###
This script is callable from the terminal and the sensor parameters are passed into the script.

	sudo python3 sensor.py 18 23 -g 'BCM'

This executes the sensor script using `data_pin=18`, `sck_pin=23`, and `gpio_mode=GPIO.BCM`. The script will then create an instance of the SHT1x class and read in the temperature, humidity, and calculate the dew point five times, sleeping 2 seconds in between each measurement. The output will looks something like this:

	$ sudo python3 examples/sensor.py 18 23 -g 'BCM'
	Temperature: 24.05*C [75.25*F]
	Humidity: 22.79%
	Dew Point: 1.37*C
	
	Temperature: 24.03*C [75.21*F]
	Humidity: 22.79%
	Dew Point: 1.36*C
	
	Temperature: 24.01*C [75.16*F]
	Humidity: 22.79%
	Dew Point: 1.33*C
	
	Temperature: 24.01*C [75.17*F]
	Humidity: 22.86%
	Dew Point: 1.38*C
	
	Temperature: 24.02*C [75.19*F]
	Humidity: 22.86%
	Dew Point: 1.39*C

To get a listing of all the parameters you can provide to the script, use `python3 sensor.py -h` for help:

	$ sudo python3 examples/sensor.py -h
	usage: sensor.py [-h] [-g {BCM,BOARD}] [-v {5V,4V,3.5V,3V,2.5V}]
	                 [-r {HIGH,LOW}] [-e] [-o] [-c]
	                 data-pin sck-pin
	
	Reads the temperature and relative humidity from the SHT1x series of sensors
	using the pi_sht1x library.
	
	positional arguments:
	  data-pin              Data pin used to connect to the sensor.
	  sck-pin               SCK pin used to connect to the sensor.
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -g {BCM,BOARD}, --gpio-mode {BCM,BOARD}
	                        RPi.GPIO mode used, either GPIO.BOARD or GPIO.BCM.
	                        Defaults to GPIO.BCM.
	  -v {5V,4V,3.5V,3V,2.5V}, --vdd {5V,4V,3.5V,3V,2.5V}
	                        Voltage used to power the sensor. Defaults to 3.5V.
	  -r {HIGH,LOW}, --resolution {HIGH,LOW}
	                        Resolution used by the sensor, 14/12-bit or 12-8-bit.
	                        Defaults to High.
	  -e, --heater          Used to turn the internal heater on (used for
	                        calibration).
	  -o, --otp-no-reload   Used to enable OTP no reload, will save about 10ms per
	                        measurement.
	  -c, --no-crc-check    Performs CRC checking.

## Credits ##
This module was done for fun and to learn how to communicate with serial devices using Python and the Raspberry Pi. I referred to the following projects from time to time when I hit a stumbling block (there were many...):

- [Jonathan Oxer](https://github.com/practicalarduino/SHT1x)
- [Luca Nobili](https://bitbucket.org/lunobili/rpisht1x)
