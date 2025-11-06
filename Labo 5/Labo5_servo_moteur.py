# main.py — Pico W (MicroPython) – bouton réactif
import time
import network
import ntptime
import urequests
from machine import Pin, RTC
from utime import sleep
from servo import SERVO  # ta classe telle quelle

# === Wi-Fi ===
WIFI_SSID = "iPhone de William"
WIFI_PASSWORD = "poiuytreza"

# === IO ===
LED = Pin("LED", Pin.OUT)

# --- Câblage bouton ---
# Si bouton entre GP16 et GND  -> actif à 0 (recommandé) :
BUTTON_ACTIVE_LOW = True
if BUTTON_ACTIVE_LOW:
    BUTTON = Pin(16, Pin.IN, Pin.PULL_UP)   # appui = 0
    IRQ_EDGE = Pin.IRQ_FALLING
else:
    BUTTON = Pin(16, Pin.IN, Pin.PULL_DOWN) # appui = 1
    IRQ_EDGE = Pin.IRQ_RISING

SERVO_PIN = 20
RTC_ = RTC()

# Fréquence de mise à jour périodique (secondes)
SAFE_UPDATE_S = 600  # 10 min
TICK = 20           # ms – pas de sommeil court

# --- Fuseaux horaires cyclés par le bouton ---
TIMEZONES = [
    ("UTC",   0),
    ("UTC+1", +1*3600),
    ("UTC+3", +3*3600),
    ("UTC-2", -2*3600),
]

# État global (modifié par l'IRQ)
tz_index = 0
tz_name, tz_offset_sel = TIMEZONES[tz_index]
tz_changed = False
_last_press_ms = 0
DEBOUNCE_MS = 250

def on_button_irq(pin):
    """IRQ bouton : anti-rebond + cycle fuseau + flag immédiat."""
    global _last_press_ms, tz_index, tz_name, tz_offset_sel, tz_changed
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_press_ms) < DEBOUNCE_MS:
        return
    _last_press_ms = now

    # (optionnel) double-vérif état logique, utile contre faux déclenchements
    val = pin.value()
    if BUTTON_ACTIVE_LOW and val != 0:
        return
    if (not BUTTON_ACTIVE_LOW) and val != 1:
        return

    tz_index = (tz_index + 1) % len(TIMEZONES)
    tz_name, tz_offset_sel = TIMEZONES[tz_index]
    tz_changed = True
    LED.toggle()

BUTTON.irq(trigger=IRQ_EDGE, handler=on_button_irq)

# ---------------- Wi-Fi ----------------
def connect_wifi(ssid, password, timeout_s=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        wlan.config(hostname="pico-w")
    except Exception:
        pass
    if not wlan.isconnected():
        print("Connexion Wi-Fi…")
        wlan.connect(ssid, password)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            LED.toggle()
            sleep(0.25)
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_s * 1000:
                LED.off()
                raise RuntimeError("Échec Wi-Fi (timeout)")
        LED.off()
    print("Wi-Fi OK:", wlan.ifconfig()[0])
    return wlan

# --------------- Temps ---------------
def set_rtc_from_epoch(epoch_secs):
    Y, M, D, h, m, s, wday, yday = time.gmtime(epoch_secs)
    RTC_.datetime((Y, M, D, wday, h, m, s, 0))  # RTC en UTC

def sync_time_ntp(retries=4):
    ntptime.host = "pool.ntp.org"
    delay = 0.5
    for i in range(retries):
        try:
            print("Sync NTP… (try", i+1, ")")
            ntptime.settime()  # met la RTC en UTC
            print("NTP OK (UTC):", time.gmtime())
            return True
        except Exception as e:
            print("NTP échec:", e)
            time.sleep(delay)
            delay = min(5, delay * 2)
    return False

def sync_time_http():
    try:
        r = urequests.get("http://worldtimeapi.org/api/ip", timeout=10)
        data = r.json()
        r.close()
        set_rtc_from_epoch(int(data["unixtime"]))
        print("HTTP time OK (UTC).")
        return True
    except Exception as e:
        print("HTTP time KO:", e)
        return False

def localtime_with_offset(offset_sec):
    return time.gmtime(time.time() + offset_sec)

# ------------- Mapping heure -> angle -------------
def time_to_servo_angle(tm):
    hour = tm[3] % 12
    minute = tm[4]
    angle = 15.0 * (hour + minute / 60.0)  # 12h -> 0..180° (15°/h)
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    return angle

def show_time_and_set_servo(servo, tz_name, tz_offset):
    tm_local = localtime_with_offset(tz_offset)
    angle = time_to_servo_angle(tm_local)
    servo.turn(angle)
    print("[{}] {:02d}:{:02d}:{:02d} -> angle {:.1f}°"
          .format(tz_name, tm_local[3], tm_local[4], tm_local[5], angle))
    return angle

# ----------------- MAIN -----------------
def main():
    global tz_changed

    # 1) Wi-Fi + temps
    connect_wifi(WIFI_SSID, WIFI_PASSWORD)
    if not sync_time_ntp():
        sync_time_http()

    # 2) Servo
    servo = SERVO(Pin(SERVO_PIN))
    print("Fuseau initial:", tz_name)

    # Affichage + position initiale
    last_angle = show_time_and_set_servo(servo, tz_name, tz_offset_sel)

    # 3) Boucle non bloquante
    next_update_ms = time.ticks_add(time.ticks_ms(), int(SAFE_UPDATE_S*1000))
    while True:
        now = time.ticks_ms()

        # a) Appui bouton -> réaction immédiate
        if tz_changed:
            tz_changed = False
            last_angle = show_time_and_set_servo(servo, tz_name, tz_offset_sel)

            # re-planifie la mise à jour périodique
            next_update_ms = time.ticks_add(now, int(SAFE_UPDATE_S*1000))

        # b) Mise à jour périodique quand l’échéance arrive
        if time.ticks_diff(now, next_update_ms) >= 0:
            tm_local = localtime_with_offset(tz_offset_sel)
            angle = time_to_servo_angle(tm_local)
            if abs(angle - last_angle) >= 0.5:
                servo.turn(angle)
                last_angle = angle
                print("[{}] {:02d}:{:02d}:{:02d} -> angle {:.1f}°"
                      .format(tz_name, tm_local[3], tm_local[4], tm_local[5], angle))
            next_update_ms = time.ticks_add(now, int(SAFE_UPDATE_S*1000))

        # c) Petit sommeil coopératif
        sleep(TICK/1000)

if __name__ == "__main__":
    main()
