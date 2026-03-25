from machine import Pin, I2C
import bme280

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

bme = bme280.BME280(i2c=i2c)

temp = bme.values[0]
pressure = bme.values[1]
humidity = bme.values[2]

print("Temp - " + temp + " Pressure -" + pressure + " Humidity - " + humidity )


