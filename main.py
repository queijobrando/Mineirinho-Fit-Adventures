import random
import pygame
import sys
import math
from pygame import Surface
from pathlib import Path

pygame.init()
pygame.mixer.init()
pygame.font.init()

FONTS = {
    "sm": pygame.font.SysFont("Arial", 26, bold=True),
    "md": pygame.font.SysFont("Arial", 36, bold=True),
    "lg": pygame.font.SysFont("Arial", 70, bold=True),
    "xl": pygame.font.SysFont("Arial", 140, bold=True),
}

DEBUG = False

DISTANCIA_MINIMA = 190

WIDTH = 1100
HEIGHT = 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mineirinho Fit Adventures")
clock = pygame.time.Clock()

ASSETS_DIR = Path("assets")
SOUND_DIR = ASSETS_DIR / "sounds"
UI_DIR = ASSETS_DIR / "ui"
PLAYER_DIR = ASSETS_DIR / "player"
FOOD_DIR = ASSETS_DIR / "food"

# ============================================================
# SOM — CARREGAMENTO SEGURO
# ============================================================

def load_sound(path, volume=0.5):
    try:
        snd = pygame.mixer.Sound(str(path))
        snd.set_volume(volume)
        return snd
    except Exception as e:
        # falha não crítica
        print(f"[ERRO] Falha ao carregar som {path} ({e})")
        return None

# Sons do jogo
jump_sound = load_sound(SOUND_DIR / "jump.wav", 0.5)
good_sound = load_sound(SOUND_DIR / "good.wav", 0.6)
bad_sound = load_sound(SOUND_DIR / "bad.wav", 0.7)
lose_life_sound = load_sound(SOUND_DIR / "lose_life.wav", 0.7)
gameover_sound = load_sound(SOUND_DIR / "gameover.wav", 0.8)
victory_sound = load_sound(SOUND_DIR / "victory.wav", 0.8)

# ============================================================
# FUNÇÃO DE CARREGAMENTO SEGURO DE IMAGENS
# ============================================================

def load_image(path, scale=None, size=None):
    try:
        img = pygame.image.load(str(path)).convert_alpha()

        if scale is not None:
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            img = pygame.transform.scale(img, (w, h))
            return img

        if size is not None:
            img = pygame.transform.scale(img, size)
            return img

        return img

    except Exception as e:
        print(f"[ERRO] Não foi possível carregar '{path}'. Usando fallback. ({e})")
        # fallback: surface com cor visível
        fallback_size = size if (isinstance(size, tuple)) else (50, 50)
        surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
        surf.fill((200, 50, 50, 255))
        return surf

# ============================================================
# IMAGENS DO JOGO
# ============================================================

player_imgs = [
    load_image(PLAYER_DIR / "Boneco A1.png", scale=1),
    load_image(PLAYER_DIR / "Boneco A2.png", scale=1),
]

COMIDAS_BOAS = [
    load_image(FOOD_DIR / "Banana.png", scale=0.7),
    load_image(FOOD_DIR / "Alface.png", scale=0.6),
    load_image(FOOD_DIR / "Maca.png", scale=0.8),
]

COMIDAS_RUINS = [
    load_image(FOOD_DIR / "Hamburguer.png", scale=0.8),
    load_image(FOOD_DIR / "Sorvete.png", scale=0.7),
    load_image(FOOD_DIR / "Refrigerante.png", scale=0.7),
]

background_img = load_image(UI_DIR / "background.jpg", size=(WIDTH, HEIGHT))
gameover_img = load_image(UI_DIR / "benicio.png", size=(420, 320))

_chao_temp = load_image(UI_DIR / "chao.png")
chao_img = load_image(UI_DIR / "chao.png", size=(_chao_temp.get_width(), 70))

CHAO_HEIGHT = chao_img.get_height()
GROUND_BOTTOM = HEIGHT - CHAO_HEIGHT

ALTURA_ALTA = GROUND_BOTTOM - 160
ALTURA_BAIXA = GROUND_BOTTOM - 10

# ============================================================
# IMAGENS UI (HUD)
# ============================================================

# hearts
heart_full_img = load_image(UI_DIR / "heart_full.png", size=(48, 48))
heart_empty_img = load_image(UI_DIR / "heart_empty.png", size=(48, 48))

# score icon
score_icon_img = load_image(UI_DIR / "score_icon.png", size=(40, 40))

# time bar images (bar_bg, bar_fill)
bar_bg_img = load_image(UI_DIR / "bar_bg.png", size=(480, 28))
bar_fill_img = load_image(UI_DIR / "bar_fill.png", size=(480, 28))

# If user didn't provide bar images, create fallback sizes
if bar_bg_img.get_width() == 50 and bar_bg_img.get_height() == 50 and (UI_DIR / "bar_bg.png").exists() is False:
    # fallback to a wide bar
    bar_bg_img = pygame.Surface((480, 28), pygame.SRCALPHA)
    pygame.draw.rect(bar_bg_img, (40, 40, 40), bar_bg_img.get_rect(), border_radius=14)
if bar_fill_img.get_width() == 50 and bar_fill_img.get_height() == 50 and (UI_DIR / "bar_fill.png").exists() is False:
    bar_fill_img = pygame.Surface((480, 28), pygame.SRCALPHA)
    pygame.draw.rect(bar_fill_img, (80, 200, 80), bar_fill_img.get_rect(), border_radius=14)

BAR_WIDTH = bar_bg_img.get_width()
BAR_HEIGHT = bar_bg_img.get_height()

# ============================================================
# CLASSES
# ============================================================

class Chao:
    def __init__(self):
        self.image = chao_img
        self.width = self.image.get_width()
        self.y = HEIGHT - CHAO_HEIGHT
        self.speed = 6

        self.n_blocos = (WIDTH // self.width) + 3
        self.blocos = []
        x = 0
        for _ in range(self.n_blocos):
            self.blocos.append(x)
            x += self.width

    def update(self, speed_multiplier):
        vel = int(self.speed * speed_multiplier)
        for i in range(len(self.blocos)):
            self.blocos[i] -= vel

        for i in range(len(self.blocos)):
            if self.blocos[i] <= -self.width:
                max_x = max(self.blocos)
                self.blocos[i] = max_x + self.width

    def draw(self, surface):
        for x in self.blocos:
            surface.blit(self.image, (x, self.y))

class Player(pygame.sprite.Sprite):
    def __init__(self, images):
        super().__init__()
        self.images = images
        self.current_frame = 0
        self.frame_time = 120
        self.last_update = pygame.time.get_ticks()

        self.image = self.images[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (150, GROUND_BOTTOM)

        self.update_hitbox()

        self.vel_y = 0
        self.jump_force = -20
        self.gravity = 1
        self.no_chao = True

    def update_hitbox(self):
        self.hitbox = self.rect.inflate(0, 0)

    def animate(self):
        now = pygame.time.get_ticks()
        if now - self.last_update >= self.frame_time:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.images)
            self.image = self.images[self.current_frame]

    def jump(self):
        if self.no_chao:
            self.vel_y = self.jump_force
            self.no_chao = False
            if jump_sound:
                jump_sound.play()

    def update(self, dt):
        self.animate()

        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        if self.rect.bottom >= GROUND_BOTTOM:
            self.rect.bottom = GROUND_BOTTOM
            self.no_chao = True
            self.vel_y = 0

        self.update_hitbox()

class Comida(pygame.sprite.Sprite):
    def __init__(self, tipo, spawn_x, altura):
        super().__init__()
        self.tipo = tipo

        if tipo == "boa":
            self.image = random.choice(COMIDAS_BOAS)
        else:
            self.image = random.choice(COMIDAS_RUINS)

        self.rect = self.image.get_rect()
        self.rect.bottom = altura
        self.rect.x = spawn_x

        self.speed = 1
        self.update_hitbox()

    def update_hitbox(self):
        self.hitbox = self.rect.inflate(0, 0)

    def update(self, dt, speed_multiplier):
        vel = int(6 * speed_multiplier)
        self.rect.x -= vel
        self.update_hitbox()

        if self.rect.right < -50:
            self.kill()

# ============================================================
# UI (HUD) helper drawing
# ============================================================

def draw_text(surface, text, font_key, x, y, center=False, color=(0, 0, 0)):
    font = FONTS[font_key]
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
    surface.blit(surf, rect)

def debug_rect(surface, rect, color=(0, 255, 0), width=1):
    pygame.draw.rect(surface, color, rect, width)

def draw_hud(surface, score, vidas, elapsed_seconds, total_time):
    padding = 12
    # --- HEARTS (top-left) ---
    heart_x = padding
    heart_y = padding
    max_hearts = 3  # desenho, mas você usa 'vidas' reais
    # draw only up to 3 hearts visually, matching gameplay vidas (you can change)
    shown_hearts = min(max_hearts, 3)
    for i in range(shown_hearts):
        img = heart_full_img if i < vidas else heart_empty_img
        surface.blit(img, (heart_x, heart_y))
        heart_x += img.get_width() + 6

    # --- SCORE (top-center-ish) ---
    # Place near top-left but after hearts; we will place it a bit to the right
    score_icon_w = score_icon_img.get_width()
    score_icon_h = score_icon_img.get_height()
    score_x = padding + 48 * shown_hearts + 40
    score_y = padding + (48 - score_icon_h) // 2
    surface.blit(score_icon_img, (score_x, score_y))

    draw_text(surface, f"{score}", "md",
            score_x + score_icon_w + 8,
            score_y + (score_icon_h // 2) - 17)

    # --- TIME BAR (rodapé, centralizada) ---
    # Bar position
    padding = 20
    bar_x = WIDTH - BAR_WIDTH - 55
    bar_y = padding

    # draw bg
    surface.blit(bar_bg_img, (bar_x, bar_y))

    # compute fill percentage
    remaining = max(total_time - elapsed_seconds, 0)
    pct = elapsed_seconds / total_time if total_time > 0 else 0.0
    pct = max(0.0, min(1.0, pct))

    # draw fill using scaled image (keep proportion)
    fill_w = int(BAR_WIDTH * pct)
    if fill_w > 0:
        # crop bar_fill_img horizontally to fill_w
        # if fill image width matches BAR_WIDTH, scale/crop to fill_w
        if bar_fill_img.get_width() != BAR_WIDTH:
            # scale fill to BAR_WIDTH first (preserve height)
            scaled_fill = pygame.transform.scale(bar_fill_img, (BAR_WIDTH, BAR_HEIGHT))
        else:
            scaled_fill = bar_fill_img
        fill_surf = scaled_fill.subsurface((0, 0, fill_w, BAR_HEIGHT)).copy()
        surface.blit(fill_surf, (bar_x, bar_y))

    # optional: numeric timer on top-right of bar
    timer_text = f"{int(elapsed_seconds)}s"
    draw_text(surface, timer_text, "sm", bar_x + BAR_WIDTH + 8, bar_y + BAR_HEIGHT // 2 - 8)

# ============================================================
# TELA DE CONTAGEM / GAME OVER / VITÓRIA (mantive a lógica)
# ============================================================

def countdown_screen(seconds=3):
    for i in range(seconds, -1, -1):
        screen.blit(background_img, (0, 0))
        draw_text(screen, "Preparar...", "md", WIDTH//2, HEIGHT//5, center=True)

        text = str(i) if i > 0 else "VAI!"
        color = (0, 0, 0) if i > 0 else (0, 200, 0)
        font_key = "xl" if i > 0 else "lg"

        draw_text(screen, text, font_key, WIDTH//2, HEIGHT//2, center=True, color=color)
        pygame.display.update()
        pygame.time.delay(700)

def game_over_screen(score):
    if gameover_sound:
        gameover_sound.play()

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

        draw_text(screen, "GAME OVER", "lg", WIDTH//2, HEIGHT//2 + 120, center=True, color=(220, 30, 30))
        draw_text(screen, f"Pontos: {score}", "md", WIDTH//2, HEIGHT//2 + 170, center=True)
        draw_text(screen, "R = Reiniciar  |  ESC = Sair", "sm", WIDTH//2, HEIGHT - 40, center=True)

        pygame.display.update()
        clock.tick(30)

def victory_screen(score):
    if victory_sound:
        victory_sound.play()

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
        rect = gameover_img.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
        screen.blit(gameover_img, rect)

        draw_text(screen, "PARABÉNS!", "lg", WIDTH//2, HEIGHT//2 + 80, center=True, color=(30, 130, 30))
        draw_text(screen, "Você sobreviveu 60 segundos!", "md", WIDTH//2, HEIGHT//2 + 140, center=True)
        draw_text(screen, f"Pontos: {score}", "md", WIDTH//2, HEIGHT//2 + 180, center=True)
        draw_text(screen, "R = Reiniciar  |  ESC = Sair", "sm", WIDTH//2, HEIGHT - 40, center=True)

        pygame.display.update()
        clock.tick(30)

# ============================================================
# LOOP PRINCIPAL
# ============================================================

def main():
    TEMPO_TOTAL = 60

    while True:
        player_group = pygame.sprite.GroupSingle()
        comida_group = pygame.sprite.Group()

        player = Player(player_imgs)
        player_group.add(player)
        chao = Chao()

        score = 0
        vidas = 3

        spawn_timer = 0
        game_start = pygame.time.get_ticks()

        countdown_screen(3)
        running = True

        while running:
            dt = clock.tick(60)
            spawn_timer += dt
            elapsed_seconds = (pygame.time.get_ticks() - game_start) / 1000.0

            progress = min(elapsed_seconds / TEMPO_TOTAL, 1.0)
            speed_multiplier = 1 + (progress ** 1.7)

            spawn_interval_dynamic = max(1200 - int(progress * 900), 350)
            chance_ruim_dynamic = min(25 + progress * 90, 85)

            if elapsed_seconds >= TEMPO_TOTAL:
                if victory_screen(score):
                    running = False
                else:
                    pygame.quit()
                    sys.exit()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_SPACE, pygame.K_UP):
                        player.jump()

            # ========= SPAWN =========
            spawn_check_interval = int(spawn_interval_dynamic + random.randint(-80, 80))
            if spawn_timer >= spawn_check_interval:

                spawn_allowed = True
                if len(comida_group) > 0:
                    ultimo = max(comida_group.sprites(), key=lambda s: s.rect.x)
                    if ultimo.rect.x > WIDTH - DISTANCIA_MINIMA:
                        spawn_allowed = False

                if spawn_allowed:
                    spawn_timer = 0
                    spawn_x = WIDTH + random.randint(80, 250)

                    if random.randint(1, 100) <= chance_ruim_dynamic:
                        tipo = "ruim"
                    else:
                        tipo = "boa"

                    altura = random.choice([ALTURA_ALTA, ALTURA_BAIXA])
                    comida_group.add(Comida(tipo, spawn_x, altura))
                else:
                    spawn_timer -= 200
                    if spawn_timer < 0:
                        spawn_timer = 0

            # ========= UPDATE =========
            player_group.update(dt)
            for c in comida_group:
                c.update(dt, speed_multiplier)

            chao.update(speed_multiplier)

            # ========= COLISÃO =========
            for comida in comida_group:
                if player.hitbox.colliderect(comida.hitbox):
                    comida.kill()

                    if comida.tipo == "boa":
                        score += 10
                        if good_sound:
                            good_sound.play()
                    else:
                        vidas -= 1
                        if bad_sound:
                            bad_sound.play()
                        if lose_life_sound:
                            lose_life_sound.play()

                        if vidas <= 0:
                            if game_over_screen(score):
                                running = False
                            else:
                                pygame.quit()
                                sys.exit()

            # ========= DESENHO =========
            screen.blit(background_img, (0, 0))
            chao.draw(screen)
            player_group.draw(screen)
            comida_group.draw(screen)

            if DEBUG:
                debug_rect(screen, player.hitbox, (0, 255, 0))
                for comida in comida_group:
                    debug_rect(screen, comida.hitbox, (255, 0, 0))

            # HUD
            draw_hud(screen, score, vidas, elapsed_seconds, TEMPO_TOTAL)

            # fallback textual HUD (kept for compatibility)
            # draw_text(screen, f"Pontos: {score}", "sm", 30, 20)
            # draw_text(screen, f"Vidas: {vidas}", "sm", 30, 60)
            # draw_text(screen, f"Tempo: {int(elapsed_seconds)}s", "sm", WIDTH - 160, 20)

            pygame.display.update()

if __name__ == "__main__":
    main()
