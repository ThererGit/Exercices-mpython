from ws2812 import WS2812
from machine import ADC, Pin
from utime import sleep
import utime
import urandom  # pour générer des couleurs aléatoires

led = WS2812(18,1)
SOUND_SENSOR = ADC(1)

BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

prece=75 			#niveau sonor de comparaison de départ
valeurs_son = [1]
val_close = [1]
moyenne=0
bpm=0
interval=0

#je veux un niveau sonore excluant les valeurs anormales. Soit le bruit : niv > 50 et la variation trop soudaine. 
# Telle que niv1 *1,5 = niv2 = PICS et que niv2 ne dépasse pas (1,8*niv1)(pics trop important).

dernierBat = 0
while True:
    
    son = SOUND_SENSOR.read_u16()//256
    #print(son)
    
    if son > 50:
        valeurs_son.append(son)      #son ok, je l'ajoute à la liste 
        if len(valeurs_son)>50:      #verifie si la liste n'est pas trop longue (max 50 echantillons pour faire la moy)
                valeurs_son.pop(0)
        moyenne_lon= sum(valeurs_son)/len(valeurs_son)
        
        val_close.append(son)
        if len(val_close)>5:      #verifie si la liste n'est pas trop longue (max 5 echantillons pour faire la moy)
                val_close.pop(0)
        moyenne_cou= sum(val_close)/len(val_close)
    
        variance = sum((x - moyenne_cou) ** 2 for x in val_close) / len(val_close)
        mnt = utime.ticks_ms()
        print("ici")
        print(mnt - dernierBat)
#         print(mnt, dernierBat)
#         print(moyenne_cou,moyenne_lon)
    
        if moyenne_cou>moyenne_lon*1.2 and variance>50:    #Prends les valeurs plausibles pour de niveau sonore d'un batement
            print ("coucou")
            if dernierBat is not None:  # éviter le tout premier "beat"
                interval_ms = utime.ticks_diff(mnt, dernierBat)
                if 300 < interval_ms < 2000:  # 30 à 200 BPM
                    bpm = 60000 / interval_ms
                    print(bpm)
                    print(" Beat détecté! interval:", interval_ms, "ms  → BPM:", bpm)
                    
                    tampon_bpm.append(bpm)
                    if len(tampon_bpm) > ECHANTILLONS_BPM_MAX:
                        tampon_bpm.pop(0)

                    bpm_filtre = sum(tampon_bpm) / len(tampon_bpm)
                    tampon_bpm_minute.append(bpm_filtre)
                    print(f"BPM filtré: {bpm_filtre:.1f}")
                    
                    led.pixels_fill(color)
                    led.pixels_show()
                    
            else:
                print("Premier beat détecté, démarrage du chrono...")

                #	 mise à jour du dernier beat
                dernierBat = mnt
                
                
    sleep(0.005)

#moyenne= sum(valeurs_son)/len(valeurs_son)
#print(moyenne)
#print(son)
    
    
#     if son>moyenne*1.2:
#         print("BEATS")
#         mnt = utime.ticks_ms()
#         interval = utime.ticks_diff(mnt, der)
#         if 300 < interval < 1950:
#             bpm = 60000/interval
#             der=mnt
#             print("PICS DETECTE")
    #compaMoy=moyenne
    
    
#je veux detecter les pics sonores, si la moyenne est trop importante % à la précédente alors = BEATS
    
   

# end1 = utime.ticks_ms()
# duree1 = utime.ticks_diff(end1, start1)
# print("la durée de la boucle est :",duree1)



