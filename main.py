import random
import pygame
import sys

pygame.display.init()
pygame.font.init()

# Tamanho da janela
WIDTH = 800
HEIGHT = 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jogo da Comida Saudável")

clock = pygame.time.Clock()

# Carregando imagens
player_img = pygame.image.load("assets/Boneco A1.png").convert_alpha()
comida_saude_img = pygame.image.load("assets/Banana.png").convert_alpha()
comida_ruim_img = pygame.image.load("assets/Hamburguer.png").convert_alpha()
background_img = pygame.image.load("assets/background.jpg").convert()
gameover_img = pygame.image.load("assets/benicio.png").convert_alpha()   # <--- NOVO

# Classes ------------------------------------------------------

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (100, HEIGHT - 30)

        self.vel_y = 0
        self.jump_force = -18
        self.gravity = 1
        self.no_chao = True

    def jump(self):
        if self.no_chao:
            self.vel_y = self.jump_force
            self.no_chao = False

    def update(self):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        if self.rect.bottom >= HEIGHT - 30:
            self.rect.bottom = HEIGHT - 30
            self.no_chao = True


class Comida(pygame.sprite.Sprite):
    def __init__(self, tipo):
        super().__init__()
        self.tipo = tipo
        
        # Imagem correta
        if tipo == "boa":
            self.image = comida_saude_img
        else:
            self.image = comida_ruim_img

        self.rect = self.image.get_rect()

        # -------------------------------------------------------
        # Agora nasce à DIREITA e anda para a esquerda
        # -------------------------------------------------------
        self.rect.x = WIDTH + 50
        self.rect.y = random.randint(HEIGHT - 120, HEIGHT - 50)

        self.speed = random.randint(5, 8)

    def update(self):
        # Anda para a ESQUERDA
        self.rect.x -= self.speed

        # Saiu da tela
        if self.rect.right < -50:
            self.kill()


# Função de tela de Game Over --------------------------------------

def game_over_screen():
    screen.blit(background_img, (0, 0))

    # Centraliza imagem de game over
    rect = gameover_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(gameover_img, rect)

    pygame.display.update()

    # Pausa até tecla pressionada
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                waiting = False


# Grupos
player_group = pygame.sprite.Group()
comida_group = pygame.sprite.Group()

player = Player()
player_group.add(player)

score = 0
vidas = 3
spawn_timer = 0

running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.jump()

    # Spawn comidas
    spawn_timer += 1
    if spawn_timer > 60:
        spawn_timer = 0
        tipo = "boa" if random.random() < 0.6 else "ruim"
        comida_group.add(Comida(tipo))

    # Update
    player_group.update()
    comida_group.update()

    # Colisão
    colisao = pygame.sprite.spritecollide(player, comida_group, True)
    for comida in colisao:
        if comida.tipo == "boa":
            score += 10
        else:
            vidas -= 1
            if vidas <= 0:
                game_over_screen()   # <--- chama tela de game over
                pygame.quit()
                sys.exit()

    # Desenho
    screen.blit(background_img, (0, 0))
    player_group.draw(screen)
    comida_group.draw(screen)

    # UI
    font = pygame.font.SysFont("Arial", 28)
    text_score = font.render(f"Pontos: {score}", True, (0, 0, 0))
    text_life = font.render(f"Vidas: {vidas}", True, (0, 0, 0))
    screen.blit(text_score, (20, 20))
    screen.blit(text_life, (20, 60))

    pygame.display.update()

pygame.quit()
