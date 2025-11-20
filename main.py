import random
import pygame
import sys
import math
from pathlib import Path

pygame.init()
pygame.font.init()


WIDTH = 1100        # Aumentei amplamente a largura
HEIGHT = 700       # Aumentei a altura
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jogo da Comida Saudável")
clock = pygame.time.Clock()

ASSETS_DIR = Path("assets")

# ---- IMAGENS -----
player_img = pygame.image.load(ASSETS_DIR / "Boneco A1.png").convert_alpha()
comida_saude_img = pygame.image.load(ASSETS_DIR / "Banana.png").convert_alpha()
comida_ruim_img = pygame.image.load(ASSETS_DIR / "Hamburguer.png").convert_alpha()

background_img_raw = pygame.image.load(ASSETS_DIR / "background.jpg").convert()
background_img = pygame.transform.scale(background_img_raw, (WIDTH, HEIGHT))

# GAME OVER
gameover_img_raw = pygame.image.load(ASSETS_DIR / "benicio.png").convert_alpha()
gameover_img = pygame.transform.smoothscale(gameover_img_raw, (420, 320))

# CHÃO
chao_img_raw = pygame.image.load(ASSETS_DIR / "chao.png").convert_alpha()
chao_img = pygame.transform.scale(chao_img_raw, (chao_img_raw.get_width(), 70))  # Reduz altura se precisar

CHAO_HEIGHT = chao_img.get_height()
GROUND_BOTTOM = HEIGHT - CHAO_HEIGHT   #  CHÃO SEMPRE ALINHADO


# ============================================================
# CLASSES
# ============================================================

class Chao:
    """Chão infinito rolando igual ao Dino."""
    def __init__(self):
        self.image = chao_img
        self.width = self.image.get_width()

        # As duas peças do chão
        self.x1 = 0
        self.x2 = self.width

        self.y = HEIGHT - CHAO_HEIGHT
        self.speed = 6

    def update(self, speed_multiplier):
        vel = int(self.speed * speed_multiplier)

        self.x1 -= vel
        self.x2 -= vel

        # 🔥 CORREÇÃO DO BUG DO CHÃO SOBREPOSTO
        if self.x1 <= -self.width:
            self.x1 = self.x2 + self.width

        if self.x2 <= -self.width:
            self.x2 = self.x1 + self.width

    def draw(self, surface):
        surface.blit(self.image, (self.x1, self.y))
        surface.blit(self.image, (self.x2, self.y))


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()

        # 🔥 Ajustar jogador ao chão
        self.rect.bottomleft = (150, GROUND_BOTTOM)

        self.update_hitbox()

        self.vel_y = 0
        self.jump_force = -20   # pulo mais forte para tela maior
        self.gravity = 1
        self.no_chao = True

    def update_hitbox(self):
        self.hitbox = self.rect.inflate(-40, -20)

    def jump(self):
        if self.no_chao:
            self.vel_y = self.jump_force
            self.no_chao = False

    def update(self, dt):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        if self.rect.bottom >= GROUND_BOTTOM:
            self.rect.bottom = GROUND_BOTTOM
            self.no_chao = True
            self.vel_y = 0

        self.update_hitbox()


class Comida(pygame.sprite.Sprite):
    def __init__(self, tipo, spawn_x):
        super().__init__()
        self.tipo = tipo
        self.image = comida_saude_img if tipo == "boa" else comida_ruim_img
        self.rect = self.image.get_rect()

        # 🔥 Nunca spawnar no chão errado
        if tipo == "boa":
            self.rect.bottom = GROUND_BOTTOM - 40
        else:
            self.rect.bottom = GROUND_BOTTOM

        self.rect.x = spawn_x

        self.base_speed = random.randint(6, 9)
        self.speed = self.base_speed

        self.update_hitbox()

    def update_hitbox(self):
        self.hitbox = self.rect.inflate(-20, -10)

    def update(self, dt, speed_multiplier):
        self.speed = int(self.base_speed * speed_multiplier)
        self.rect.x -= self.speed
        self.update_hitbox()

        if self.rect.right < -50:
            self.kill()


# ============================================================
# FUNÇÕES
# ============================================================

def draw_text(surface, text, size, x, y, center=False, color=(0, 0, 0)):
    font = pygame.font.SysFont("Arial", size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
    surface.blit(surf, rect)


def countdown_screen(seconds=3):
    for i in range(seconds, -1, -1):
        screen.blit(background_img, (0, 0))
        draw_text(screen, "Preparar...", 36, WIDTH//2, HEIGHT//5, center=True)

        text = str(i) if i > 0 else "VAI!"
        size = 140 if i > 0 else 90
        color = (0, 0, 0) if i > 0 else (0, 200, 0)

        draw_text(screen, text, size, WIDTH//2, HEIGHT//2, center=True, color=color)
        pygame.display.update()
        pygame.time.delay(700)


def game_over_screen(score):
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:
                    return True
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    return False

        screen.blit(background_img, (0, 0))

        rect = gameover_img.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
        screen.blit(gameover_img, rect)

        draw_text(screen, "GAME OVER", 70, WIDTH//2, HEIGHT//2 + 120, center=True, color=(220, 30, 30))
        draw_text(screen, f"Pontos: {score}", 36, WIDTH//2, HEIGHT//2 + 170, center=True)
        draw_text(screen, "R = Reiniciar  |  ESC = Sair", 26, WIDTH//2, HEIGHT - 40, center=True)

        pygame.display.update()
        clock.tick(30)


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def main():
    while True:
        player_group = pygame.sprite.GroupSingle()
        comida_group = pygame.sprite.Group()

        player = Player()
        player_group.add(player)

        chao = Chao()

        score = 0
        vidas = 3

        spawn_timer = 0
        spawn_interval = 1000

        game_start = pygame.time.get_ticks()

        countdown_screen(3)
        running = True

        while running:
            dt = clock.tick(60)
            spawn_timer += dt
            elapsed = (pygame.time.get_ticks() - game_start) / 1000

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                    player.jump()

            # Dificuldade progressiva
            spawn_interval = max(380, 1000 - int(elapsed * 30))
            speed_multiplier = 1.0 + elapsed / 40

            # SPAWN
            if spawn_timer >= spawn_interval:
                spawn_timer = 0
                spawn_x = WIDTH + random.randint(80, 250)
                tipo = "boa" if random.random() < 0.55 else "ruim"
                comida_group.add(Comida(tipo, spawn_x))

            # UPDATE
            player_group.update(dt)
            for c in comida_group:
                c.update(dt, speed_multiplier)

            chao.update(speed_multiplier)

            # COLISÕES
            for comida in comida_group:
                if player.hitbox.colliderect(comida.hitbox):
                    comida.kill()
                    if comida.tipo == "boa":
                        score += 10
                    else:
                        vidas -= 1
                        if vidas <= 0:
                            if game_over_screen(score):
                                running = False
                            else:
                                pygame.quit()
                                sys.exit()

            screen.blit(background_img, (0, 0))
            chao.draw(screen)
            player_group.draw(screen)
            comida_group.draw(screen)

            draw_text(screen, f"Pontos: {score}", 30, 30, 20)
            draw_text(screen, f"Vidas: {vidas}", 30, 30, 60)

            pygame.display.update()


if __name__ == "__main__":
    main()
