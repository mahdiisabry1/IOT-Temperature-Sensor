from machine import Pin, I2C
import network
import time
import urequests
import bme280


# testing
#led = Pin("LED", Pin.OUT)
#led.off()

#https://script.google.com/macros/s/AKfycbyOl6RBGP-JRb-48QHZqTg4H0MO_QTE1X529i4lTvo8Ha4-dhwhvTM2PUCMTyrnLaHq/exec
#AKfycbxrAbpPJ6gOI6SEu1TkjLb9DiJ7QYyCr2Uu7VwLVrfXhIof2Fp2eGdqncueBINdbBCk

WIFI_SSID = "MyPixel"
WIFI_PASSWORD = "eagle123456"

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyOl6RBGP-JRb-48QHZqTg4H0MO_QTE1X529i4lTvo8Ha4-dhwhvTM2PUCMTyrnLaHq/exec"

LOCATION = "Kitchen"      
TOTAL_READINGS = 20        # 20 readings in one location
DELAY_SECONDS = 5          # 5 seconds between readings

# =========================================
# WIFI CONNECTION
# =========================================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        while not wlan.isconnected():
            time.sleep(1)

    print("Wi-Fi connected")
    print("IP address:", wlan.ifconfig()[0])
    return wlan

# =========================================
# CHECK WIFI STATUS
# =========================================
def ensure_wifi(wlan):
    if not wlan.isconnected():
        print("Wi-Fi lost. Reconnecting...")
        wlan = connect_wifi()
    return wlan

# =========================================
# SENSOR SETUP
# =========================================
def setup_sensor():
    i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
    sensor = bme280.BME280(i2c=i2c)
    print("BME280 sensor ready")
    return sensor

# =========================================
# READ TEMPERATURE
# =========================================
def get_sensor_data(sensor):
    temperature, pressure, humidity = sensor.values

    temp_c = float(temperature[:-1])      # '27.5C' -> 27.5
    pressure_hpa = float(pressure[:-3])   # '1008.3hPa' -> 1008.3
    humidity_pct = float(humidity[:-1])   # '65.2%' -> 65.2

    return temp_c, pressure_hpa, humidity_pct

# =========================================
# SEND DATA TO GOOGLE SHEETS
# =========================================
def send_to_google(temp_c, pressure_hpa, humidity_pct, location, wlan):
    wlan = ensure_wifi(wlan)

    request_url = (
        GOOGLE_SCRIPT_URL
        + "?temp=" + str(temp_c)
        + "&pressure=" + str(pressure_hpa)
        + "&humidity=" + str(humidity_pct)
        + "&location=" + location
    )

    try:
        response = urequests.get(request_url)
        print("Cloud response:", response.text)
        response.close()
    except Exception as e:
        print("Send failed:", e)

    return wlan

# =========================================
# PRINT SUMMARY
# =========================================
def print_summary(readings):
    if len(readings) == 0:
        print("No readings collected.")
        return

    # Initialize max/min for all metrics
    max_temp = min_temp = readings[0]
    max_pressure = min_pressure = readings[0]
    max_humidity = min_humidity = readings[0]

    total_temp = 0
    total_pressure = 0
    total_humidity = 0

    for item in readings:
        # Totals
        total_temp += item["temp"]
        total_pressure += item["pressure"]
        total_humidity += item["humidity"]

        # Temperature
        if item["temp"] > max_temp["temp"]:
            max_temp = item
        if item["temp"] < min_temp["temp"]:
            min_temp = item

        # Pressure
        if item["pressure"] > max_pressure["pressure"]:
            max_pressure = item
        if item["pressure"] < min_pressure["pressure"]:
            min_pressure = item

        # Humidity
        if item["humidity"] > max_humidity["humidity"]:
            max_humidity = item
        if item["humidity"] < min_humidity["humidity"]:
            min_humidity = item

    # Averages
    n = len(readings)
    avg_temp = total_temp / n
    avg_pressure = total_pressure / n
    avg_humidity = total_humidity / n

    # Output
    print("\n========== SUMMARY ==========")

    print("\n--- Temperature ---")
    print("Max: {:.2f} C at {}".format(max_temp["temp"], max_temp["timestamp"]))
    print("Min: {:.2f} C at {}".format(min_temp["temp"], min_temp["timestamp"]))
    print("Avg: {:.2f} C".format(avg_temp))

    print("\n--- Pressure ---")
    print("Max: {:.2f} hPa at {}".format(max_pressure["pressure"], max_pressure["timestamp"]))
    print("Min: {:.2f} hPa at {}".format(min_pressure["pressure"], min_pressure["timestamp"]))
    print("Avg: {:.2f} hPa".format(avg_pressure))

    print("\n--- Humidity ---")
    print("Max: {:.2f} % at {}".format(max_humidity["humidity"], max_humidity["timestamp"]))
    print("Min: {:.2f} % at {}".format(min_humidity["humidity"], min_humidity["timestamp"]))
    print("Avg: {:.2f} %".format(avg_humidity))

    print("\nTotal readings:", n)
    print("=============================\n")


# =========================================
# MAIN PROGRAM
# =========================================
def main():
    print("Starting sensor logging project")
    wlan = connect_wifi()
    sensor = setup_sensor()
    
    readings = []

    for i in range(TOTAL_READINGS):
        current_time = time.localtime()
        timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            current_time[0], current_time[1], current_time[2],
            current_time[3], current_time[4], current_time[5]
        )

        temp_c, pressure_hpa, humidity_pct = get_sensor_data(sensor)

        print("Reading {}: {} | Temp: {:.2f} C | Pressure: {:.2f} hPa | Humidity: {:.2f} % | {}".format(
            i + 1, timestamp, temp_c, pressure_hpa, humidity_pct, LOCATION
        ))
        
        readings.append({
            "timestamp": timestamp,
            "temp": temp_c,
            "pressure": pressure_hpa,
            "humidity": humidity_pct,
            "Location": LOCATION
        })

        wlan = send_to_google(temp_c, pressure_hpa, humidity_pct, LOCATION, wlan)

        time.sleep(DELAY_SECONDS)
        
    print_summary(readings)

main()
