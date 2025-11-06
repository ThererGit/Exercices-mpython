import machine
import utime #pour ajouter des délais

#Exercice 1 : CLIGNOTEMENT DE LED AVEC BOUTON POUSSOIR 


flag=0
state=0
ledtest=False
BUTTON=machine.Pin(16,machine.Pin.IN)
LED=machine.Pin(18,machine.Pin.OUT)
LED.value(0)
last_state=0
press_count=0
while True:
    
    val=BUTTON.value()
   
   #détection de l'appui:
   #flag sert de verrou anti-rebond logiciel (en gros, il empêche de compter plusieurs fois le même appui tant que tu n’as pas relâché le bouton).
    if val == 1 and flag == 0:
        flag = 1
        press_count += 1   # on compte l'appui 1 fois sur 2 (c'est notre deuxième bonus)
        
        if press_count == 2:  
            state += 1
            if state > 4:
                state = 1
            press_count = 0   # on remet à zéro
    
    if val == 0:
        flag = 0
    
    if last_state!=state:#ici c'est notre touche bonus on a décidé de mettre la led allumée 3 sec entre chaque changements de vitesse.
            LED.value(1)
            utime.sleep(3)
            LED.value(0)
            last_state=state       
    if state==1:
        LED.value(1)
        utime.sleep(0.5)
        LED.value(0)
    if state==2:
        LED.value(1)
        utime.sleep(0.1)
        LED.value(0)
        
    utime.sleep(0.1)
    
