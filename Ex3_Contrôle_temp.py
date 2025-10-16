##V 3.0 Exercie 3: SYSTÈME DE CONTRÔLE DE TEMPÉRATURE

from lcd1602 import LCD1602
from machine import I2C, Pin, ADC, PWM
from utime import sleep, sleep_ms
from dht11 import *   # classe DHT fournie (readTempHumid, etc.)

# --- Constantes de broches (modifiables) ---
LED_PIN   = 20     # LED externe
BUZZ_PIN  = 16     # Buzzer (PWM)
DHT_PIN   = 18     # DHT11
I2C_SDA   = 6
I2C_SCL   = 7

# définitions:
def adc_to_setpoint(adc_val):
    """Mappe ADC 0..65535 -> 15..35 °C."""
    return 15.0 + 20.0 * (adc_val / 65535.0)

def alarm_pwm(buzzer, ambient, set_temp):
    """Buzzer ON si Ambient > Set + 3°C, sinon OFF."""
    if ambient is not None and (ambient > set_temp + 3.0):
        buzzer.freq(2000)       # ~2 kHz
        buzzer.duty_u16(2000)   # volume modéré
    else:
        buzzer.duty_u16(0)      # OFF

def read_dht_with_retry(dht, last_t=None, last_h=None):
    """
    - 1 lecture
    - si (0,0) probable échec => 2 petites tentatives supplémentaires
    - si toujours invalide: on renvoie la dernière bonne (si dispo), sinon (None, None)
    """
    t, h = dht.readTempHumid()
    if (t is not None and h is not None) and not (t == 0 and h == 0):
        return t, h

    # 1er retry
    sleep_ms(200)
    t, h = dht.readTempHumid()
    if (t is not None and h is not None) and not (t == 0 and h == 0):
        return t, h

    # 2e retry
    sleep_ms(200)
    t, h = dht.readTempHumid()
    if (t is not None and h is not None) and not (t == 0 and h == 0):
        return t, h

    # Toujours pas de bonne mesure
    if last_t is not None and last_h is not None:
        return last_t, last_h
    return None, None

# --- Programme principal ---
def main():
    # E/S
    ROTARY_ANGLE_SENSOR = ADC(0)                           # Potentiomètre
    i2c = I2C(1, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400000)
    d = LCD1602(i2c, 2, 16)                                # LCD 16x2
    dht2 = DHT(DHT_PIN)                                    # DHT11
    buzzer = PWM(Pin(BUZZ_PIN))                            # Buzzer PWM
    led = Pin(LED_PIN, Pin.OUT, value=0)                   # LED

    d.display()  # allume l'écran
    sleep(2)     # sécurité pour le dht

    last_good_t = None
    last_good_h = None

    while True:
        # 1) Consigne depuis potentiomètre
        adc_val = ROTARY_ANGLE_SENSOR.read_u16()
        set_temp = adc_to_setpoint(adc_val)  # 15..35 °C

        # 2) Lecture DHT avec retry (sans toucher à ta lib)
        temp, humid = read_dht_with_retry(dht2, last_good_t, last_good_h)
        if temp is not None and humid is not None:
            last_good_t, last_good_h = temp, humid  # mémorise une mesure valide

        # 3) Affichage LCD
        d.clear()
        d.setCursor(0, 0)
        d.print("Set:" + "{:>4.1f}C".format(set_temp)) #print avec formatage 
        d.setCursor(0, 1)
        if temp is not None:
            d.print("Ambient: " + "{:>4.1f}C".format(float(temp)))
        else:
            d.print("Ambient: --- ")

        # 4) Contrôle LED + buzzer
        if temp is not None:
            if temp > set_temp + 3.0:
                # --- État ALARM ---
                for _ in range(4):  # 4 cycles de clignotement rapide (≈1 s total)
                    led.value(1)
                    d.setCursor(10, 0)
                    d.print(" ALARM")
                    alarm_pwm(buzzer, temp, set_temp)
                    sleep_ms(250)
                    led.value(0)
                    d.setCursor(10, 0)
                    d.print("      ")
                    alarm_pwm(buzzer, temp, set_temp)
                    sleep_ms(250)

            elif temp > set_temp:
                # --- État WARN ---
                for _ in range(2):  # 2 cycles de clignotement lent (≈2 s total)
                    led.value(1)
                    alarm_pwm(buzzer, temp, set_temp)  # OFF normalement
                    sleep(1)
                    led.value(0)
                    alarm_pwm(buzzer, temp, set_temp)
                    sleep(1)
            else:
                # --- État NORMAL ---
                led.value(0)
                d.setCursor(10, 0)
                d.print("      ")
                alarm_pwm(buzzer, temp, set_temp)
                sleep(1)
        else:
            # Si capteur non lu correctement
            led.value(0)
            alarm_pwm(buzzer, None, set_temp)
            sleep(1)

# Exécution
main()
