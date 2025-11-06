# main.py — Pico W (MicroPython)
import time
import network
import ntptime
import urequests
from machine import Pin, RTC
from utime import sleep
from servo import SERVO  # <-- on importe servo pour le moteur

BUTTON=machine.Pin(16,machine.Pin.IN)


# === Wi-Fi ===
WIFI_SSID = "iPhone de William"
WIFI_PASSWORD = "poiuytreza"

RTC_ = RTC()
WORLD_TIME_URL = "http://worldtimeapi.org/api/timezone/Europe/Brussels"
SERVO_PIN = 20
SAFE_UPDATE_S = 600  # rafraîchissement de l'angle toute les 10 minutes pour que nombre de degrés suffisament grand

# ---------------- Wi-Fi ----------------
def connect_wifi(ssid, password, timeout_s=20):
    wlan = network.WLAN(network.STA_IF) #On se connecte à un réseau grace à la libraire network
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
    RTC_.datetime((Y, M, D, wday, h, m, s, 0))

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

def get_local_offset_sec():
    """Retourne l'offset local (CET/CEST) en secondes pour Bruxelles."""
    try:
        r = urequests.get(WORLD_TIME_URL, timeout=10)
        data = r.json()
        r.close()
        return int(data.get("raw_offset", 0)) + int(data.get("dst_offset", 0))
    except Exception as e:
        print("API offset KO:", e)
        return 3600  # défaut CET

def sync_time_http():
    """Fallback si NTP KO : règle la RTC en UTC via WorldTimeAPI."""
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
    """
    Mapping voulu: 12 -> 0°, 6 -> 90°
    180° couvrent 12 h => 15°/h. On ajoute la fraction des minutes.
    """
    hour = tm[3] % 12
    minute = tm[4]
    angle = 15.0 * (hour + minute / 60.0)  # 15° par heure
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    return angle

# ----------------- MAIN -----------------
def main():
    # 1) Wi-Fi
    connect_wifi(WIFI_SSID, WIFI_PASSWORD)

    # 2) Temps
    if not sync_time_ntp():
        sync_time_http()
    local_offset = get_local_offset_sec()  # CET/CEST pour Bruxelles

    # 3) Servo — utilise la classe SERVO(pin)
    servo = SERVO(Pin(SERVO_PIN))

    print("Contrôle du servo en fonction de l'heure locale (Europe/Brussels)…")
    last_angle = None
    while True:
        tm_local = localtime_with_offset(local_offset)
        angle = time_to_servo_angle(tm_local)
        

        # Envoie l'angle uniquement s'il a changé (évite du bruit)
        if last_angle is None or abs(angle - last_angle) >= 0.5:
            servo.turn(angle)
            last_angle = angle
            print("Heure {:02d}:{:02d}:{:02d} -> angle {:.1f}°"
                  .format(tm_local[3], tm_local[4], tm_local[5], angle))

        sleep(SAFE_UPDATE_S)

if __name__ == "__main__":
    main()
