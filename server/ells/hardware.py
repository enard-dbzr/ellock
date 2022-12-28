import serial
from time import sleep
from serial.tools.list_ports import comports

device = None

def detect_device():
    global device
    ser = serial.Serial(baudrate=115200, timeout=0.5)
    while True:
        for port in comports():
            try:
                ser.port = port.device
                ser.open()
                sleep(2)
                ser.write(b"elldetect\n")
                if ser.readline().startswith(b"found"):
                    device = ser
                    print("Device found")
                    return ser
                ser.close()
            except serial.serialutil.SerialException:
                pass


def open():
    device.write(b"open\n")
    return True
