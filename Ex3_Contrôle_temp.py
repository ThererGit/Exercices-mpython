##V 2.0 Project 2: Display Rotary Angle Sensor Reading with LCD

from lcd1602 import LCD1602
from machine import I2C, Pin, ADC
from utime import sleep


def main():
    ROTARY_ANGLE_SENSOR = ADC(0)
    i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
    d = LCD1602(i2c, 2, 16)

    d.display()  # allume l'écran

    while True:
        sleep(1)
        d.clear()  
        d.setCursor(0,0)
        d.print('Test Potentiometre')
        d.setCursor(0, 1)
        d.print(str(ROTARY_ANGLE_SENSOR.read_u16()))
        sleep(0.2)


###Exécution
main()