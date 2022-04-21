from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, Value, Lock
import traceback
import sys
import random
import time

SIZE = (750, 625)

EJE = 500#pos x del eje donde se mueven las naves
X=0
Y=1

TMAX = 100000000000000000000000000000000000000000000000

PASO = 25 #la cantidad q se desplaza una nave arriba o abajo

#si fueran 2
class Nave():
    
    def __init__(self,number):
        self.pos =[EJE, SIZE[Y]//2] #colocamos las naves en la posicion del medio del eje
        self.index = number #para identificar a las naves??? Que cada una lleve su numero
        
    def get_pos(self):
        return self.pos
    
    def moveUp(self): # he cambiado up y down, creo q estaba al revés
        self.pos[Y] += PASO
        if self.pos[Y] > SIZE[Y]: 
            self.pos[Y] = SIZE[Y] #OTRA OPCION: que salga por el otro lado self.pos[Y] = 0

    def moveDown(self):
        self.pos[Y] -= PASO
        if self.pos[Y] < 0:
            self.pos[Y] = 0 #OTRA OPCION: que salga por el otro lado self.pos[Y] = SIZE[Y]

    def __str__(self):
        return str(self.pos)

class Proyectil():
    
    def __init__(self):
        self.pos=[random.randint(-300,-1), random.randint(0, SIZE[Y]) ]
        self.velocity = random.randint(2,8) # es una cantidad que se sumara en horizontal, no un vector
    
    def get_pos(self):
        return self.pos         
        
    def update(self):
        self.pos[X] += self.velocity  #solo se mueve en horizontal
        if self.pos[X] > SIZE[X]:
            self.restart()
        
    def restart(self): #establecer una velocidad y una posicion a la izqda pa cuando un poyectil llegue al final
        self.pos=[0, random.randint(0, SIZE[Y]) ]
        self.velocity = random.randint(3,10)

    #def collide_nave(self): # esto significa colisionar????
        #self.dies()
     
    def __str__(self):
        return f"B<{self.pos}>"

class Game():
     
    def __init__(self, manager,n_naves,n_proyectiles):
        self.naves = manager.list( [Nave(i) for i in range(n_naves)] )
        # creo que le estamos pasando la misma velocidad a todos los proyectiles, pq primero evalúa el parámetro
        self.proyectiles = manager.list( [Proyectil() for i in range(n_proyectiles)] )#calculamos random la velocidad)
        self.score = manager.list( [0]*n_naves )
        self.time = time.time()
        self.running = Value('i', 1) # 1 running, 0 not running
        self.mutex = Lock()
            
    def get_nave_iesima(self, i):
        return self.naves[i]

    def get_proyectil_iesimo(self,i):
        return self.proyectiles[i] # no entiendo pq coger el 0
    
    def get_score(self):
        return list(self.score)

    def is_running(self):
        return self.running.value == 1

    def stop(self):
        if time.time() - self.time > TMAX:#cuando el tiempo haya finalizado:  #mejor dicho, if todas las naves mueren?
            self.running.value = 0
                    
    def finish(self):
        self.running.value = 0
        
    def moveUp(self, numero):
        self.mutex.acquire()
        p = self.naves[numero]
        p.moveUp()
        self.naves[numero] = p
        self.mutex.release()

    def moveDown(self, numero):
        self.mutex.acquire()
        p = self.naves[numero]
        p.moveDown()
        self.naves[numero] = p
        self.mutex.release()
        
    def proyectil_collide(self, i): # un proyectil se choca con la nave i
        self.mutex.acquire()
        score = self.score[i]
        score += 1
        self.score[i] = score
        self.mutex.release()
    
    def get_info(self,n_naves):
        info = {
            'pos_naves': [nave.get_pos() for nave in self.naves],
            'pos_proyectiles': [proyectil.get_pos() for proyectil in self.proyectiles],
            'score': list(self.score),
            'is_running': self.running.value == 1
        }
        return info
    
    def move_proyectil(self):
        self.mutex.acquire()
        n_proyectiles = len(self.proyectiles)
        for i in range(n_proyectiles):
            proyectil = self.proyectiles[i] 
            proyectil.update() # se mueve a la drcha o se resetea si se pasa
            self.proyectiles[i] = proyectil
        self.mutex.release()

    def __str__(self):# FALTA
        return f"{self.get_info()}"

#APARTIR DE AQUI YA NO ENTIENDO NADA
def player(i, conn, game):
    try:
        print(f"{game.get_info()}")
        conn.send( (i, game.get_info()) )
        while game.is_running():
            command = ""
            while command != "next":
                command = conn.recv()
                if command == "up":
                    game.moveUp(i)
                elif command == "down":
                    game.moveDown(i)
                elif command == "collide":
                    game.proyectil_collide(i)
                elif command == "quit":
                    game.finish()
            conn.send(game.get_info())
    except:
        traceback.print_exc()
        conn.close()
    finally:
        print(f"Game ended {game}")

def main(ip_address):
    manager = Manager()
    n_naves = 3
    n_proyectiles = 5
    try:
        with Listener((ip_address, 6000),
                      authkey=b'secret password') as listener:
            n_player = 0
            players = [None, None]
            game = Game(manager,n_naves,n_proyectiles)
            while True:
                print(f"accepting connection {n_player}")
                conn = listener.accept()
                players[n_player] = Process(target=player,
                                            args=(n_player, conn, game))
                n_player += 1
                if n_player == n_naves:
                    for i in range(n_naves):
                        players[i].start()
                    game = Game(manager,n_naves,n_proyectiles)
    except Exception as e:
        traceback.print_exc()

if __name__=='__main__':
    ip_address = "127.0.0.1"
    if len(sys.argv)>1:
        ip_address = sys.argv[1]

    main(ip_address)
