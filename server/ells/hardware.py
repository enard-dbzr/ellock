import serial
from time import sleep
from serial.tools.list_ports import comports
import cv2
import io

device = None
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)


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


def get_image():
    cap.read()
    success, img = cap.read()
    cv2.imwrite("test.jpg", img)
    success, buffer = cv2.imencode(".jpg", img)
    return io.BytesIO(buffer)
