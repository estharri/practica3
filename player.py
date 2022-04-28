from multiprocessing.connection import Client
import traceback
import pygame
import sys, os
import time

TMAX = 50 # tiempo maximo del juego
WHITE = (255, 255, 255)
BLACK = (0,0,0)

X = 0
Y = 1
SIZE = (1280, 720) 

FPS = 60 #frames por segundo


class Nave():
    
    def __init__(self, number):        
        self.index = number #numero de nave
        self.pos = [None, None] #coord x y

    def get_pos(self):
        return self.pos

    def get_number(self):
        return self.index

    def set_pos(self, pos):
        self.pos = pos

    def __str__(self):
        return f"P<{self.index, self.pos}>"


class Proyectil():
    
    def __init__(self):        
        self.pos= [None, None]

    def get_pos(self):
        return self.pos

    def set_pos(self, pos):
        self.pos = pos

    def __str__(self):
        return f"B<{self.pos}>"
    
class Game():
    
    def __init__(self, n_naves,n_proyectiles):
        self.naves = [Nave(i) for i in range(n_naves)] 
        self.proyectiles = [Proyectil() for i in range(n_proyectiles)]
        self.score = [0]*n_naves
        self.time = time.time()
        self.running = True

    def get_nave_iesima(self, i): #0 al n_naves-1
        return self.naves[i]

    def set_pos_nave_iesima(self,i, pos):
        self.naves[i].set_pos(pos)

    def get_proyectil_iesimo(self,i): 
        return self.proyectiles[i]
  
    def set_pos_proyectil_iesimo(self,i,pos):
        self.proyectiles[i].set_pos(pos)
  
    def get_score(self):
        return self.score

    def set_score(self, score):
        self.score = score
        
    def update(self, gameinfo):
       n_naves = len(self.naves)
       n_proyectiles = len(self.proyectiles)
       for i  in range (n_naves):
           self.set_pos_nave_iesima(i, gameinfo['pos_naves'][i])
       for i in range (n_proyectiles):
           self.set_pos_proyectil_iesimo(i,gameinfo['pos_proyectiles'][i])
       self.set_score(gameinfo['score'])
       self.running = gameinfo['is_running']

    def is_running(self):
        return self.running

    def finish(self):
        self.running = False


class Nave_Diseño(pygame.sprite.Sprite):
    def __init__(self,nave):
        super().__init__()
        self.nave = nave
        self.image = pygame.image.load('nave.png')
        self.image = pygame.transform.scale(self.image,(90,90))
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.update()
        
    def update(self):        
        pos = self.nave.get_pos()
        self.rect.centerx, self.rect.centery = pos  
        
    def draw(self, screen):
        screen.window.blit(self.image, self.rect)
   
    def __str__(self):
        return f"S<{self.mon}>"

class Proyectil_Diseño(pygame.sprite.Sprite):
    def __init__(self, proy):
        super().__init__()
        self.proyectil = proy
        self.image= pygame.image.load('proyectil.png')
        self.image = pygame.transform.scale(self.image,(50,50))
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.update()

    def update(self):
        pos = self.proyectil.get_pos()
        self.rect.centerx, self.rect.centery = pos

       
    def __str__(self):
        return f"P<{self.ban.pos}>"


class Display():
    
    def __init__(self, game, n_naves,n_proyectiles):      
        self.game = game
        self.score = game.get_score()
        self.naves_diseño = [Nave_Diseño(self.game.get_nave_iesima(i)) for i in range(n_naves)]
        self.proyectiles_diseño = [Proyectil_Diseño(self.game.get_proyectil_iesimo(i)) for i in range(n_proyectiles)]
        self.all_sprites = pygame.sprite.Group()
        self.naves_group = pygame.sprite.Group()
        self.proyectiles_group = pygame.sprite.Group()
        for nave  in self.naves_diseño:
            self.all_sprites.add(nave)
            self.naves_group.add(nave)
        for proyectil in self.proyectiles_diseño:
            self.all_sprites.add(proyectil)
            self.proyectiles_group.add(proyectil)
        self.screen = pygame.display.set_mode(SIZE)
        self.clock =  pygame.time.Clock()  #FPS
        self.background = pygame.image.load('fondo.jpg') 
        self.background = pygame.transform.scale(self.background,(1280,720))
        pygame.mixer.init()
        self.sound=pygame.mixer.music.load('temazo.mp3')
        self.sound=pygame.mixer.music.set_volume(0.3)
        pygame.init()
        pygame.mixer.music.play(loops=-1)

    
    def analyze_events(self):
        events = []
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    events.append("quit")
                elif event.key == pygame.K_UP:
                    events.append("up")
                elif event.key == pygame.K_DOWN:
                    events.append("down")
            elif event.type == pygame.QUIT:
                events.append("quit")
        for i in range(len(self.proyectiles_diseño)):
            if pygame.sprite.spritecollideany(self.proyectiles_diseño[i], self.naves_diseño):
                events.append("collide")
        return events
    

    def refresh(self):
        self.all_sprites.update()
        self.screen.blit(self.background, (0, 0))
        score = self.game.get_score()
        n_naves = len(self.game.naves)
        font = pygame.font.Font(None, 30)
        for i in range(n_naves):
        	text = font.render(f"Player {i+1}: {score[i]}", 1, WHITE)
        	self.screen.blit(text, (SIZE[X]-150, i*35))
        self.all_sprites.draw(self.screen)
        pygame.display.flip()

    def tick(self):
        self.clock.tick(FPS)

    @staticmethod
    def quit():
        pygame.quit()
        
        

def main(ip_address,port):
    print('¿Cuantos jugadores hay?')
    n_naves = int(input())
    n_proyectiles = 5
    try:
        with Client((ip_address, 6000), authkey=b'secret password') as conn:
            game = Game(n_naves, n_proyectiles)
            i,gameinfo = conn.recv()
            print(f"I am player {i+1}")
            game.update(gameinfo)
            display = Display(game,n_naves,n_proyectiles)
            while game.is_running():
                events = display.analyze_events()
                for ev in events:
                    conn.send(ev)
                    if ev == 'quit':
                        score =game.get_score
                        mejor = 0
                        for i in range(int(n_naves)):
                            if (score[i] < score[mejor]):
                                mejor=i
                        mejor+=1
                        print('GANADOR: Player ', mejor)
                        game.finish() #diferente
                conn.send("next")
                gameinfo = conn.recv()
                game.update(gameinfo)
                display.refresh()
                display.tick()
    except:
        traceback.print_exc()
    finally:
        pygame.quit()


if __name__=='__main__':
    ip_address = "127.0.0.1"
    if len(sys.argv)>2:
        ip_address = sys.argv[1]
        port=sys.argv[2]

    main(ip_address,port)  