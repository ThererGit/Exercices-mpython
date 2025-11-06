from machine import Pin, PWM, ADC
from time import sleep

# === Initialisation ===
LED_PWM = PWM(Pin(16))          # LED en PWM
LED_PWM.freq(1000)

ROTARY_ANGLE_SENSOR = ADC(0)    # Potentiomètre
buzzer = PWM(Pin(27))           # Buzzer
BUTTON = Pin(18, Pin.IN)        # Bouton poussoir

#new


# === Définition des notes ===
def DO(time, vol): buzzer.freq(1046); buzzer.duty_u16(int(vol)); sleep(time)
def RE(time, vol): buzzer.freq(1175); buzzer.duty_u16(int(vol)); sleep(time)
def MI(time, vol): buzzer.freq(1318); buzzer.duty_u16(int(vol)); sleep(time)
def FA(time, vol): buzzer.freq(1397); buzzer.duty_u16(int(vol)); sleep(time)
def SO(time, vol): buzzer.freq(1568); buzzer.duty_u16(int(vol)); sleep(time)
def LA(time, vol): buzzer.freq(1760); buzzer.duty_u16(int(vol)); sleep(time)
def SI(time, vol): buzzer.freq(1967); buzzer.duty_u16(int(vol)); sleep(time)
def NO(time): buzzer.duty_u16(0); sleep(time)

# === Mélodie 1 : victoire Mario ===
def mario_victory(vol=3000):
    tempo = 0.15
    MI(tempo, vol); SO(tempo, vol); MI(tempo, vol)
    LA(tempo, vol); SI(tempo, vol); LA(tempo/2, vol); SI(tempo/2, vol)
    SO(tempo, vol); MI(tempo, vol); LA(tempo, vol)
    SO(tempo, vol); DO(tempo*2, vol)
    NO(0.1)
    DO(tempo, vol); RE(tempo, vol); MI(tempo*2, vol)
    NO(0.2)
    MI(tempo, vol); RE(tempo, vol); MI(tempo, vol); DO(tempo*2, vol)
    NO(0.5)
    buzzer.duty_u16(0)

# === Mélodie 2 : perso ===
def melodie_perso(vol=3000):
    for note in [MI, SO, DO, SO, MI]:
        vol = ROTARY_ANGLE_SENSOR.read_u16()
        LED_PWM.duty_u16(vol)
        note(0.25, vol)
        LED_PWM.duty_u16(0)
        NO(0.05)
        
melodie_active=0
dernier_etat = 0    # pour détecter le changement d’état du bouton

while True:
    vol = ROTARY_ANGLE_SENSOR.read_u16()

    # --- Détection de l'appui sur le bouton ---
    etat = BUTTON.value()
    if etat == 1 and dernier_etat == 0:
        # Changement de mélodie au front montant
        melodie_active = 1 - melodie_active
        print("Mélodie changée :", "Mario" if melodie_active else "Perso")
        sleep(0.3)  # anti-rebond
    dernier_etat = etat

    # --- Lecture du volume et affichage sur la LED ---
    LED_PWM.duty_u16(vol)

    # --- Lecture de la mélodie active ---
    if melodie_active == 1:
        mario_victory(vol)
    else:
        melodie_perso(vol)



