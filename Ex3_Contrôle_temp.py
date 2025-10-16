##V 3.0 Exercie 3: SYSTÈME DE CONTRÔLE DE TEMPÉRATURE

from lcd1602 import LCD1602
from machine import I2C, Pin, ADC, PWM
from utime import sleep
from dht11 import *  


# --- Helpers ---
def adc_to_setpoint(adc_val):
    """Mappe ADC 0..65535 -> 15..35 °C."""
    return 15.0 + 20.0 * (adc_val / 65535.0)

## Fonction pour faire sonner le buzzer 
def alarm(buzzer, ambient, set_temp):
    """Buzzer ON si Ambient > Set + 3°C, sinon OFF."""
    try:
        if ambient is not None and (ambient > set_temp + 3.0):
            buzzer.freq(2000)       # ~2 kHz
            buzzer.duty_u16(2000)   # volume modéré
        else:
            buzzer.duty_u16(0)      # OFF
    except:
        # sécurité en cas d'erreur PWM
        buzzer.deinit()
        buzzer = PWM(Pin(16))

# --- Programme principal ---
def main():
    # Entrées / sorties
    ROTARY_ANGLE_SENSOR = ADC(0)                 # Potentiomètre
    i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)  # écran lcd
    d = LCD1602(i2c, 2, 16)                      # Taille de mon LCD 16x2
    dht2 = DHT(18)                                # DHT sur GP18
    buzzer = PWM(Pin(16))                         # Buzzer PWM sur GP16

    d.display()  # allume l'écran

    while True:
        # 1) Consigne depuis potentiomètre
        adc_val = ROTARY_ANGLE_SENSOR.read_u16()
        set_temp = adc_to_setpoint(adc_val)  # 15..35 °C

        # 2) Lecture capteur (≈ 1 Hz)
        # La librairie dht 11 renvoie le couple (temp, humid) via readTempHumid()
        temp, humid = dht2.readTempHumid()
        ambient_str = "--- "
        if temp is not None:
            try:
                ambient_str = "{:>4.1f}C".format(float(temp))
            except:
                pass

        # 3) Affichage LCD
        d.clear()
        d.setCursor(0, 0)
        d.print("Set:     " + "{:>4.1f}C".format(set_temp))
        d.setCursor(0, 1)
        d.print("Ambient: " + ambient_str)

        # 4) Alerte buzzer
        alarm(buzzer, temp, set_temp)

        # 5) Période ~1 s
        sleep(1)

# Exécution
main()
