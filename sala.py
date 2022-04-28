from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, Value, Lock
import traceback
import sys
import random
import time

SIZE = (1280, 720)
EJE = 850#pos x del eje donde se mueven las naves
X=0
Y=1

TMAX = 50

PASO = 25 #la cantidad q se desplaza una nave arriba o abajo

class Nave():
    
    def __init__(self,number):
        self.pos =[EJE, random.randint(0,SIZE[Y])] #colocamos las naves en la posicion del medio del eje
        self.index = number #para identificar a las naves??? Que cada una lleve su numero
        
    def get_pos(self):
        return self.pos
    
    def get_number(self):
        return self.index
    
    def moveUp(self): 
        self.pos[Y] -= PASO
        if self.pos[Y] < 0:
            self.pos[Y] = 0 #OTRA OPCION: que salga por el otro lado self.pos[Y] = SIZE[Y]


    def moveDown(self):
        self.pos[Y] += PASO
        if self.pos[Y] > SIZE[Y]: 
            self.pos[Y] = SIZE[Y] #OTRA OPCION: que salga por el otro lado self.pos[Y] = 0
            
    def __str__(self):
        return str(self.pos)

class Proyectil():
    
    def __init__(self):
        self.pos=[0, random.randint(0, SIZE[Y]) ]
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

    def choca_nave(self,numero):
        d_y = abs(self.pos[1]-numero.get_pos()[1])
        d_x = abs(self.pos[0]-numero.get_pos()[0])
        r1 = 50/2 #radio imagen 1
        r2 = 90/2 #radio imagen 2
        r = r1+r2
        if(d_x+100<2*r and d_y+100<2*r):
            return True
        else:
            return False
    
    def __str__(self):
        return f"B<{self.pos}>"

class Game():
     
    def __init__(self, manager,n_naves,n_proyectiles):
        self.n_naves = n_naves
        self.naves = manager.list( [Nave(i) for i in range(n_naves)] )
        self.proyectiles = manager.list( [Proyectil() for i in range(n_proyectiles)] )
        self.score = manager.list( [0]*n_naves )
        self.time = time.time()
        self.running = Value('i', 1) # 1 running, 0 not running
        self.mutex = Lock()
    def numero_naves(self):
        return self.n_naves
    
    def get_nave_iesima(self, i):
        return self.naves[i]

    def get_proyectil_iesimo(self,i):
        return self.proyectiles[i] 
    
    def get_score(self):
        return list(self.score)

    def is_running(self):
        return self.running.value == 1

    def stop(self):
        if time.time() - self.time > TMAX:#cuando el tiempo haya finalizado
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
        self.mutex.release()
    
    def get_info(self):
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
        n_naves = len(self.naves)
        for i in range(n_proyectiles):
            proyectil = self.proyectiles[i] 
            for j in range(n_naves):
                if(proyectil.choca_nave(self.naves[j])):
                    proyectil.restart()
                    self.score[j]+=1
                    break
            proyectil.update() # se mueve a la drcha o se resetea si se pasa
            self.proyectiles[i] = proyectil
        self.mutex.release()

    def __str__(self):# FALTA
        return f"{self.get_info()}"


def player(i, conn, game, n_naves):
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
            if i==0:
                game.move_proyectil()
                if game.stop():
                    return f"GAME OVER"
            conn.send(game.get_info())
    except:
        traceback.print_exc()
        conn.close()
    finally:
        score = game.get_score()
        root = tkinter.Tk()
        # create a font
        f = Font(family="times", size=50, weight=NORMAL)
        f = Font(font=("Courier", 20, "bold"))
        mejor = 0
        for i in range(int(n_naves)):
            if (score[i] < score[mejor]):
                mejor=i
        mejor+=1 
        w = tkinter.Label(root, text= "\n  SE ACABO EL JUEGO  \n  GANADOR: Player "+ str(mejor) + "\n    /\    \n   /  \   \n  /    \  \n  |    |  \n  |    |  \n  |O  O|  \n  |    |  \n  |    |  \n /|    |\ \n / |____| \ \n /__|    |__\ ", font=f)
        w.pack()
    
        w = tkinter.Button(root, text="Finalizar", command=root.destroy)
        w.pack()
    
        fb = Font(font=w["font"]).copy()
        fb.config(weight=BOLD)
    
        w.config(font=fb)
    
        tkinter.mainloop()
        print(f"Game ended {game}")

def main(ip_address,port):
    manager = Manager()
    print('¿Cuantos jugadores hay?')
    n_naves = int(input())
    n_proyectiles = 5
    try:
        with Listener((ip_address, 6000),
                      authkey=b'secret password') as listener:
            n_player = 0
            players = [None]*n_naves
            game = Game(manager,n_naves,n_proyectiles)
            while True:
                print(f"accepting connection {n_player}")
                conn = listener.accept()
                players[n_player] = Process(target=player,
                                            args=(n_player, conn, game, n_naves))
                n_player += 1
                if n_player == n_naves:
                    for i in range(n_naves):
                        players[i].start()
                    game = Game(manager,n_naves,n_proyectiles)
    except Exception as e:
        traceback.print_exc()

if __name__=='__main__':
    ip_address = "127.0.0.1"
    if len(sys.argv)>2:
        ip_address = sys.argv[1]
        port=sys.argv[2]

    main(ip_address,port)