import network
import socket
import time
from machine import Pin, I2C
import bme280

# testing
#led = Pin("LED", Pin.OUT)
#led.off()

# =========================================
# USER SETTINGS
# =========================================
WIFI_SSID = "MyPixel"
WIFI_PASSWORD = "eagle123456"

# =========================================
# CONNECT TO WIFI
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
# SETUP SENSOR
# =========================================
def setup_sensor():
    i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
    sensor = bme280.BME280(i2c=i2c)
    print("BME280 sensor ready")
    return sensor

# =========================================
# CREATE WEB PAGE
# =========================================
def create_webpage(temp, hum, pres):
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Pico W BME280 Sensor</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f2f2f2;
            margin-top: 40px;
        }}
        .card {{
            display: inline-block;
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #333;
        }}
        p {{
            font-size: 20px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>BME280 Sensor Readings</h1>
        <p><strong>Temperature:</strong> {temp}</p>
        <p><strong>Humidity:</strong> {hum}</p>
        <p><strong>Pressure:</strong> {pres}</p>
    </div>
</body>
</html>"""
    return html

# =========================================
# MAIN PROGRAM
# =========================================
def main():
    wlan = connect_wifi()
    sensor = setup_sensor()

    address = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(address)
    server.listen(1)

    print("Web server running at http://{}".format(wlan.ifconfig()[0]))

    while True:
        client, client_address = server.accept()
        print("Client connected from", client_address)

        temperature, pressure, humidity = sensor.values
        webpage = create_webpage(temperature, humidity, pressure)

        response_headers = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
        client.send(response_headers)
        client.sendall(webpage)
        client.close()

main()
