## V 1. 0   Project 1: Display Hello, world! with LCD



from lcd1602 import LCD1602
from machine import I2C,Pin
from utime import sleep

i2c=I2C(1,scl=Pin(7), sda=Pin(6), freq=400000)
d=LCD1602(i2c,2,16)

d.display() #allume l'écran
sleep(1)
d.clear()
d.print('Bonjour')

sleep(1)
d.setCursor(0,1)
d.print('Monde')