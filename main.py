import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
RANKING_FILE = DATA_DIR / "ranking.json"

WHITE = (245, 245, 245)
GRAY = (120, 120, 120)
DARK = (8, 10, 22)
PANEL = (14, 18, 38)
GREEN = (50, 220, 100)
RED = (240, 70, 70)
YELLOW = (255, 220, 80)
CYAN = (80, 210, 255)
PURPLE = (180, 90, 255)
ORANGE = (255, 150, 70)
BLUE = (95, 145, 255)
PINK = (255, 90, 190)

PLAYER_MAX_HP = 100
RANKING_LIMIT = 10


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def load_ranking():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not RANKING_FILE.exists():
        return []
    try:
        with RANKING_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_ranking(ranking):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with RANKING_FILE.open("w", encoding="utf-8") as f:
        json.dump(ranking[:RANKING_LIMIT], f, ensure_ascii=False, indent=2)


def add_score_to_ranking(name, score, elapsed):
    ranking = load_ranking()
    ranking.append({"name": name, "score": int(score), "time": round(elapsed, 2)})
    ranking.sort(key=lambda item: (-item["score"], item["time"], item["name"]))
    save_ranking(ranking)
    return ranking[:RANKING_LIMIT]


def make_placeholder(size, color, kind="rect", label=""):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    w, h = size
    if kind == "player":
        points = [(w // 2, 0), (int(w * 0.08), h), (w // 2, int(h * 0.75)), (int(w * 0.92), h)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.circle(surface, WHITE, (w // 2, int(h * 0.52)), max(2, w // 10))
    elif kind == "enemy":
        pygame.draw.ellipse(surface, color, (0, int(h * 0.18), w, int(h * 0.62)))
        pygame.draw.rect(surface, color, (int(w * 0.16), int(h * 0.58), int(w * 0.68), int(h * 0.25)))
        pygame.draw.circle(surface, DARK, (int(w * 0.34), int(h * 0.45)), max(2, w // 12))
        pygame.draw.circle(surface, DARK, (int(w * 0.66), int(h * 0.45)), max(2, w // 12))
    elif kind == "boss":
        pygame.draw.ellipse(surface, color, (0, int(h * 0.10), w, int(h * 0.60)))
        pygame.draw.rect(surface, color, (int(w * 0.06), int(h * 0.43), int(w * 0.88), int(h * 0.42)))
        pygame.draw.circle(surface, WHITE, (int(w * 0.35), int(h * 0.42)), max(4, w // 16))
        pygame.draw.circle(surface, WHITE, (int(w * 0.65), int(h * 0.42)), max(4, w // 16))
    elif kind == "bullet":
        pygame.draw.ellipse(surface, color, surface.get_rect())
        pygame.draw.rect(surface, color, (int(w * 0.2), 0, max(2, int(w * 0.6)), h), border_radius=max(2, w // 2))
    elif kind == "laser":
        pygame.draw.rect(surface, color, surface.get_rect(), border_radius=max(4, w // 5))
        pygame.draw.rect(surface, WHITE, (w // 3, 0, max(2, w // 3), h), border_radius=max(3, w // 8))
    elif kind == "explosion":
        for i in range(12):
            angle = i * math.tau / 12
            end = (w // 2 + int(math.cos(angle) * w * 0.45), h // 2 + int(math.sin(angle) * h * 0.45))
            pygame.draw.line(surface, color, (w // 2, h // 2), end, max(2, w // 16))
        pygame.draw.circle(surface, YELLOW, (w // 2, h // 2), min(w, h) // 4)
    else:
        pygame.draw.rect(surface, color, surface.get_rect(), border_radius=max(4, min(w, h) // 6))
    if label:
        try:
            font = pygame.font.Font(None, max(12, min(size) // 2))
            txt = font.render(label, True, WHITE)
            surface.blit(txt, txt.get_rect(center=(w // 2, h // 2)))
        except pygame.error:
            pass
    return surface


def load_png_or_placeholder(path, size, color, kind, label=""):
    if path.exists():
        try:
            img = pygame.image.load(str(path)).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except pygame.error:
            pass
    return make_placeholder(size, color, kind, label)


def load_first_existing(paths, size, color, kind, label=""):
    for path in paths:
        if path.exists():
            return load_png_or_placeholder(path, size, color, kind, label)
    return make_placeholder(size, color, kind, label)


def load_background_or_none(path, size):
    if not path.exists():
        return None
    try:
        img = pygame.image.load(str(path)).convert_alpha()
        target_w, target_h = size
        img_w, img_h = img.get_size()
        if img_w <= 0 or img_h <= 0:
            return None
        scale = max(target_w / img_w, target_h / img_h)
        scaled_size = (max(1, int(img_w * scale)), max(1, int(img_h * scale)))
        img = pygame.transform.smoothscale(img, scaled_size)
        crop_x = max(0, (scaled_size[0] - target_w) // 2)
        crop_y = max(0, (scaled_size[1] - target_h) // 2)
        return img.subsurface(pygame.Rect(crop_x, crop_y, target_w, target_h)).copy()
    except pygame.error:
        return None


@dataclass
class Layout:
    width: int
    height: int
    scale: float
    play_rect: pygame.Rect
    player_size: tuple
    enemy_size: tuple
    boss_size: tuple
    player_bullet_size: tuple
    enemy_bullet_size: tuple
    counter_size: tuple

    @classmethod
    def from_screen(cls, width, height):
        # Base retrato 720x1280. Em monitores horizontais, o jogo fica em uma area vertical central.
        target_ratio = 9 / 16
        if width / height > target_ratio:
            play_h = height
            play_w = int(height * target_ratio)
            play_x = (width - play_w) // 2
            play_y = 0
        else:
            play_w = width
            play_h = int(width / target_ratio)
            play_x = 0
            play_y = (height - play_h) // 2
        scale = min(play_w / 720, play_h / 1280)
        scale = clamp(scale, 0.55, 2.6)
        return cls(
            width=width,
            height=height,
            scale=scale,
            play_rect=pygame.Rect(play_x, play_y, play_w, play_h),
            player_size=(int(123 * scale), int(117 * scale)),
            enemy_size=(int(76 * scale), int(56 * scale)),
            boss_size=(int(380 * scale), int(225 * scale)),
            player_bullet_size=(max(22, int(32 * scale)), max(34, int(52 * scale))),
            enemy_bullet_size=(max(24, int(36 * scale)), max(30, int(46 * scale))),
            counter_size=(max(48, int(74 * scale)), max(40, int(58 * scale))),
        )

    def px(self, x):
        return self.play_rect.left + int(x * self.play_rect.width)

    def py(self, y):
        return self.play_rect.top + int(y * self.play_rect.height)


class Assets:
    def __init__(self, layout):
        self.reload(layout)

    def reload(self, layout):
        self.background = load_background_or_none(
            ASSETS_DIR / "hud" / "background.png",
            layout.play_rect.size,
        )
        colors = [BLUE, CYAN, GREEN, YELLOW, ORANGE, PINK, PURPLE]
        self.player_sprites = []
        for i in range(5):
            numbered = i + 1
            preferred = ASSETS_DIR / "player" / f"nave_{numbered}.png"
            legacy = ASSETS_DIR / "player" / f"nave{numbered}.png"
            alternate = ASSETS_DIR / "player" / f"nave{i}.png"
            self.player_sprites.append(load_first_existing([preferred, legacy, alternate], layout.player_size, colors[i], "player", str(numbered)))

        self.counter_sprites = [
            load_png_or_placeholder(ASSETS_DIR / "hud" / f"cont_{i}.png", layout.counter_size, PANEL, "rect", str(i))
            for i in range(0, 7)
        ]

        enemy_colors = [GREEN, CYAN, ORANGE, PINK, PURPLE]
        self.enemy_sprites = [
            load_png_or_placeholder(ASSETS_DIR / "enemies" / f"inimigo{i}.png", layout.enemy_size, enemy_colors[(i - 1) % len(enemy_colors)], "enemy", str(i))
            for i in range(1, 5)
        ]
        # Existe apenas um sprite de tiro para inimigos; o chefe usa o mesmo tiro.
        self.enemy_bullet_sprites = [
            load_png_or_placeholder(ASSETS_DIR / "bullets" / "tiro_inimigo1.png", layout.enemy_bullet_size, RED, "bullet", "E")
        ]
        self.player_bullet_sprites = [
            load_png_or_placeholder(ASSETS_DIR / "bullets" / f"tiro_nave{i}.png", layout.player_bullet_size, CYAN if i == 1 else YELLOW, "bullet", str(i))
            for i in range(1, 3)
        ]
        boss_colors = [PURPLE, ORANGE, PINK, RED]
        self.boss_sprites = [
            load_png_or_placeholder(ASSETS_DIR / "boss" / f"chefe_{i}.png", layout.boss_size, boss_colors[i - 1], "boss", str(i))
            for i in range(1, 5)
        ]
        self.explosion = load_png_or_placeholder(
            ASSETS_DIR / "effects" / "explosion.png",
            (int(82 * layout.scale), int(82 * layout.scale)),
            ORANGE,
            "explosion",
        )
        self.laser = load_png_or_placeholder(
            ASSETS_DIR / "bullets" / "laser.png",
            (max(28, int(42 * layout.scale)), layout.play_rect.height),
            RED,
            "laser",
        )
        countdown_size = (int(260 * layout.scale), int(260 * layout.scale))
        self.countdown_sprites = [
            load_png_or_placeholder(ASSETS_DIR / "hud" / f"start_{i}.png", countdown_size, CYAN, "rect", str(i))
            for i in range(1, 5)
        ]


class Player:
    def __init__(self, layout, assets):
        self.layout = layout
        self.assets = assets
        self.ammo = 6
        self.max_ammo = 6
        self.sprite_index = 2
        self.image = assets.player_sprites[self.sprite_index]
        self.rect = self.image.get_rect(midbottom=(layout.play_rect.centerx, layout.py(0.93)))
        self.vel_x = 0.0
        self.hp = PLAYER_MAX_HP
        self.shoot_timer = 0.0
        self.reload_state = "ready"
        self.reload_timer = 0.0
        self.reload_delay = 0.48
        self.reload_step_timer = 0.0
        self.reload_step_delay = 0.16
        self.post_reload_delay = 0.42
        self.invuln = 0.0

    def update_sprite(self):
        max_speed = max(1, 760 * self.layout.scale)
        normalized = clamp(self.vel_x / max_speed, -1, 1)
        self.sprite_index = int(round((normalized + 1) * 2))
        self.sprite_index = clamp(self.sprite_index, 0, 4)
        center = self.rect.center
        bottom = self.rect.bottom
        self.image = self.assets.player_sprites[self.sprite_index]
        self.rect = self.image.get_rect(center=center)
        self.rect.bottom = bottom

    def update(self, dt, keys):
        accel = 2850 * self.layout.scale
        friction = 7.0
        max_speed = 760 * self.layout.scale
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1

        if direction:
            self.vel_x += direction * accel * dt
        else:
            self.vel_x -= self.vel_x * min(1, friction * dt)

        self.vel_x = clamp(self.vel_x, -max_speed, max_speed)
        self.rect.x += int(self.vel_x * dt)
        # Borda infinita apenas para o player: ao sair por um lado, reaparece no outro.
        if self.rect.right < self.layout.play_rect.left:
            self.rect.left = self.layout.play_rect.right
        elif self.rect.left > self.layout.play_rect.right:
            self.rect.right = self.layout.play_rect.left
        self.shoot_timer = max(0, self.shoot_timer - dt)
        self.invuln = max(0, self.invuln - dt)
        self.update_reload(dt)
        self.update_sprite()

    def update_reload(self, dt):
        # O jogador descarrega todos os 6 tiros antes de recarregar.
        # Durante a recarga nao atira; so volta apos completar 6 e aguardar um breve tempo.
        if self.reload_state == "ready":
            return

        self.reload_timer += dt
        if self.reload_state == "reloading":
            if self.reload_timer < self.reload_delay:
                return
            self.reload_step_timer += dt
            while self.reload_step_timer >= self.reload_step_delay and self.ammo < self.max_ammo:
                self.reload_step_timer -= self.reload_step_delay
                self.ammo += 1
            if self.ammo >= self.max_ammo:
                self.reload_state = "post_reload"
                self.reload_timer = 0.0
                self.reload_step_timer = 0.0
            return

        if self.reload_state == "post_reload" and self.reload_timer >= self.post_reload_delay:
            self.reload_state = "ready"
            self.reload_timer = 0.0

    def can_shoot(self):
        return self.reload_state == "ready" and self.shoot_timer <= 0 and self.ammo > 0

    def consume_shot(self):
        self.ammo = max(0, self.ammo - 1)
        self.shoot_timer = 0.22
        if self.ammo <= 0:
            self.reload_state = "reloading"
            self.reload_timer = 0.0
            self.reload_step_timer = 0.0
        self.update_sprite()

    def damage(self, amount):
        if self.invuln <= 0:
            self.hp = max(0, self.hp - amount)
            self.invuln = 0.45

    def draw(self, screen):
        if self.invuln > 0 and int(self.invuln * 20) % 2 == 0:
            return
        screen.blit(self.image, self.rect)


class Bullet:
    def __init__(self, x, y, vx, vy, damage, owner, image):
        self.image = image
        self.rect = image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.owner = owner

    def update(self, dt):
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)

    def offscreen(self, layout):
        margin = 100
        return (
            self.rect.bottom < layout.play_rect.top - margin
            or self.rect.top > layout.play_rect.bottom + margin
            or self.rect.right < layout.play_rect.left - margin
            or self.rect.left > layout.play_rect.right + margin
        )

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Laser:
    def __init__(self, x, y, width, height, damage, duration, image, tick_interval=0.12):
        self.rect = pygame.Rect(x, y, width, height)
        self.damage = damage
        self.duration = duration
        self.life = duration
        self.tick_timer = 0.0
        self.tick_interval = tick_interval
        self.image = image

    def update(self, dt):
        self.life -= dt
        self.tick_timer = max(0, self.tick_timer - dt)

    @property
    def alive(self):
        return self.life > 0

    def can_damage(self):
        return self.tick_timer <= 0

    def reset_tick(self):
        self.tick_timer = self.tick_interval

    def draw(self, screen):
        alpha = int(190 + 55 * math.sin(pygame.time.get_ticks() * 0.03))
        img = pygame.transform.smoothscale(self.image, self.rect.size)
        img.set_alpha(alpha)
        screen.blit(img, self.rect)


class Enemy:
    def __init__(self, x, y, image, hp=1):
        self.image = image
        self.x = float(x)
        self.y = float(y)
        self.rect = image.get_rect(topleft=(int(self.x), int(self.y)))
        self.hp = hp
        self.alive = True

    def sync_rect(self):
        self.rect.topleft = (int(self.x), int(self.y))

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.sync_rect()

    def damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Boss:
    def __init__(self, layout, assets):
        self.layout = layout
        self.assets = assets
        self.sprite_mode = 0
        self.image = assets.boss_sprites[0]
        self.rect = self.image.get_rect(midtop=(layout.play_rect.centerx, layout.py(0.17)))
        self.max_hp = 55
        self.hp = self.max_hp
        self.vel_x = 150 * layout.scale
        self.alive = True
        self.sequence_timer = 1.0
        self.sequence_active = False
        self.sequence_phase = "idle"
        self.phase_timer = 0.0
        self.laser_interval = 3
        self.sequence_count = 0
        self.laser_x = 0

    def set_sprite(self, mode):
        self.sprite_mode = mode
        center = self.rect.center
        top = self.rect.top
        self.image = self.assets.boss_sprites[mode]
        self.rect = self.image.get_rect(center=center)
        self.rect.top = top

    def update(self, dt, player, enemy_bullets, lasers):
        self.rect.x += int(self.vel_x * dt)
        left_limit = self.layout.play_rect.left + int(25 * self.layout.scale)
        right_limit = self.layout.play_rect.right - int(25 * self.layout.scale)
        if self.rect.left <= left_limit or self.rect.right >= right_limit:
            self.vel_x *= -1
            self.rect.y += int(9 * self.layout.scale)
            self.rect.left = max(left_limit, self.rect.left)
            self.rect.right = min(right_limit, self.rect.right)

        if not self.sequence_active:
            self.sequence_timer -= dt
            self.set_sprite(0)
            if self.sequence_timer <= 0:
                self.start_attack_sequence(player)
            return

        self.phase_timer -= dt
        if self.phase_timer > 0:
            return

        self.advance_attack_sequence(player, enemy_bullets, lasers)

    def start_attack_sequence(self, player):
        self.sequence_active = True
        self.sequence_phase = "warn_left"
        self.phase_timer = 0.45
        self.laser_x = player.rect.centerx
        self.set_sprite(1)

    def advance_attack_sequence(self, player, enemy_bullets, lasers):
        if self.sequence_phase == "warn_left":
            self.fire_edge_shot("left", player, enemy_bullets)
            self.sequence_phase = "warn_right"
            self.phase_timer = 0.45
            self.set_sprite(2)
            return

        if self.sequence_phase == "warn_right":
            self.fire_edge_shot("right", player, enemy_bullets)
            self.sequence_count += 1
            if self.sequence_count % self.laser_interval == 0:
                self.sequence_phase = "laser_warn"
                self.phase_timer = 0.55
                self.laser_x = player.rect.centerx
                self.set_sprite(3)
            else:
                self.sequence_phase = "recover"
                self.phase_timer = 0.52
                self.set_sprite(0)
            return

        if self.sequence_phase == "laser_warn":
            self.fire_laser(lasers)
            self.sequence_phase = "recover"
            self.phase_timer = 0.42
            self.set_sprite(0)
            return

        self.sequence_active = False
        self.sequence_phase = "idle"
        self.sequence_timer = 0.82 + random.random() * 0.35
        self.set_sprite(0)

    def fire_edge_shot(self, side, player, enemy_bullets):
        origin_x = self.rect.left + int(12 * self.layout.scale) if side == "left" else self.rect.right - int(12 * self.layout.scale)
        origin_y = self.rect.centery + int(20 * self.layout.scale)
        dx = player.rect.centerx - origin_x
        dy = player.rect.centery - origin_y
        length = max(1, math.hypot(dx, dy))
        speed = 430 * self.layout.scale
        image = random.choice(self.assets.enemy_bullet_sprites)
        enemy_bullets.append(Bullet(origin_x, origin_y, dx / length * speed, dy / length * speed, 14, "enemy", image))

    def fire_laser(self, lasers):
        laser_w = max(28, int(38 * self.layout.scale))
        x = int(clamp(self.laser_x - laser_w // 2, self.layout.play_rect.left, self.layout.play_rect.right - laser_w))
        y = self.rect.bottom
        lasers.append(Laser(x, y, laser_w, self.layout.play_rect.bottom - y, 18, 0.95, self.assets.laser))

    def damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        if self.sequence_active and self.sequence_phase == "laser_warn":
            laser_w = max(28, int(38 * self.layout.scale))
            x = int(clamp(self.laser_x - laser_w // 2, self.layout.play_rect.left, self.layout.play_rect.right - laser_w))
            warning = pygame.Surface((laser_w, self.layout.play_rect.bottom - self.rect.bottom), pygame.SRCALPHA)
            warning.fill((255, 60, 60, 80))
            screen.blit(warning, (x, self.rect.bottom))


class Explosion:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = image.get_rect(center=(x, y))
        self.life = 0.32
        self.max_life = self.life

    def update(self, dt):
        self.life -= dt

    def draw(self, screen):
        if self.life <= 0:
            return
        alpha = int(255 * self.life / self.max_life)
        img = self.image.copy()
        img.set_alpha(alpha)
        screen.blit(img, self.rect)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Space Invaders Vertical - Pygame")
        self.fullscreen = True
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.layout = Layout.from_screen(*self.screen.get_size())
        self.assets = Assets(self.layout)
        self.configure_fonts()
        self.state = "name"
        self.player_name = ""
        self.ranking = load_ranking()
        self.reset_game()

    def configure_fonts(self):
        self.font_big = pygame.font.Font(None, int(58 * self.layout.scale))
        self.font_med = pygame.font.Font(None, int(34 * self.layout.scale))
        self.font_small = pygame.font.Font(None, int(24 * self.layout.scale))
        self.font_tiny = pygame.font.Font(None, int(20 * self.layout.scale))

    def reset_game(self):
        self.player = Player(self.layout, self.assets)
        self.player_bullets = []
        self.enemy_bullets = []
        self.lasers = []
        self.enemies = []
        self.explosions = []
        self.boss = None
        self.enemy_direction = 1
        self.enemy_speed = 118 * self.layout.scale
        self.enemy_drop_timer = 0.0
        self.enemy_shot_timer = random.uniform(0.35, 0.75)
        self.player_shot_sequence = 0
        self.spawn_wave()
        self.score = 0
        self.start_ticks = pygame.time.get_ticks()
        self.finish_time = 0
        self.result_text = ""

    def resize_game(self, size, fullscreen=None):
        if fullscreen is not None:
            self.fullscreen = fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.layout = Layout.from_screen(*self.screen.get_size())
        self.assets.reload(self.layout)
        self.configure_fonts()
        self.reset_game()
        self.state = "name"

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.resize_game((720, 1280), fullscreen=False)
        else:
            self.resize_game((0, 0), fullscreen=True)

    def spawn_wave(self):
        self.enemies.clear()
        cols = 5
        rows = 3
        enemy_w, enemy_h = self.layout.enemy_size
        gap_x = int(34 * self.layout.scale)
        gap_y = int(30 * self.layout.scale)
        total_w = cols * enemy_w + (cols - 1) * gap_x
        start_x = self.layout.play_rect.centerx - total_w // 2
        start_y = self.layout.py(0.22)
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (enemy_w + gap_x)
                y = start_y + row * (enemy_h + gap_y)
                image = random.choice(self.assets.enemy_sprites)
                hp = 1 + row // 2
                self.enemies.append(Enemy(x, y, image, hp=hp))

    def elapsed(self):
        if self.state in ("win", "gameover"):
            return self.finish_time
        return (pygame.time.get_ticks() - self.start_ticks) / 1000

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                if self.state == "name":
                    self.handle_name_input(event)
                elif self.state in ("win", "gameover") and event.key == pygame.K_RETURN:
                    self.reset_game()
                    self.state = "name"
            if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.resize_game((event.w, event.h), fullscreen=False)

    def handle_name_input(self, event):
        if event.key == pygame.K_RETURN and self.player_name.strip():
            self.player_name = self.player_name.strip().upper()[:10]
            self.reset_game()
            self.state = "countdown"
            self.countdown_timer = 0.0
            self.countdown_index = 0  # start_1 = "3", index 0
        elif event.key == pygame.K_BACKSPACE:
            self.player_name = self.player_name[:-1]
        else:
            char = event.unicode.upper()
            if len(self.player_name) < 10 and (char.isalnum() or char in "_- "):
                self.player_name += char

    def update_countdown(self, dt):
        self.countdown_timer += dt
        # Cada sprite fica 0.85s na tela (3, 2, 1, GO!)
        self.countdown_index = int(self.countdown_timer / 0.85)
        if self.countdown_index >= 4:
            self.state = "playing"
            self.start_ticks = pygame.time.get_ticks()

    def draw_countdown(self):
        self.draw_playing()  # renderiza o jogo parado atrás
        # Overlay semitransparente
        overlay = pygame.Surface(self.layout.play_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, self.layout.play_rect.topleft)
        idx = min(self.countdown_index, 3)
        sprite = self.assets.countdown_sprites[idx]
        rect = sprite.get_rect(center=self.layout.play_rect.center)
        # Efeito de escala pulsante baseado no tempo dentro do frame atual
        t = (self.countdown_timer % 0.85) / 0.85  # 0..1
        pulse = 1.0 + 0.12 * (1.0 - t)
        w = int(sprite.get_width() * pulse)
        h = int(sprite.get_height() * pulse)
        scaled = pygame.transform.smoothscale(sprite, (w, h))
        r = scaled.get_rect(center=self.layout.play_rect.center)
        self.screen.blit(scaled, r)

    def update_playing(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)
        self.auto_player_fire()
        self.update_enemies(dt)
        self.update_boss(dt)
        self.update_bullets(dt)
        self.update_explosions(dt)
        self.check_collisions()
        self.check_end_conditions()

    def auto_player_fire(self):
        if self.player.can_shoot():
            image = self.assets.player_bullet_sprites[self.player_shot_sequence % 2]
            self.player_shot_sequence += 1
            speed = -840 * self.layout.scale
            self.player_bullets.append(Bullet(self.player.rect.centerx, self.player.rect.top - image.get_height() // 2, 0, speed, 1, "player", image))
            self.player.consume_shot()

    def update_enemies(self, dt):
        alive = [e for e in self.enemies if e.alive]
        if not alive:
            if self.boss is None:
                self.boss = Boss(self.layout, self.assets)
            return

        left_border = self.layout.play_rect.left + int(25 * self.layout.scale)
        right_border = self.layout.play_rect.right - int(25 * self.layout.scale)
        min_x = min(e.rect.left for e in alive)
        max_x = max(e.rect.right for e in alive)
        speed_bonus = min(2.2, self.elapsed() / 65)
        dx = self.enemy_direction * self.enemy_speed * (1 + speed_bonus) * dt
        dy = 0

        # Movimento classico: percorre horizontalmente ate a borda, desce um degrau,
        # inverte direcao e continua. Sem descida reta constante.
        if (self.enemy_direction > 0 and max_x + dx >= right_border) or (self.enemy_direction < 0 and min_x + dx <= left_border):
            dx = 0
            dy = int(28 * self.layout.scale)
            self.enemy_direction *= -1

        for enemy in alive:
            enemy.move(dx, dy)

        self.enemy_drop_timer += dt
        if self.enemy_drop_timer >= 4.2:
            self.enemy_drop_timer = 0
            for enemy in alive:
                enemy.move(0, int(12 * self.layout.scale))

        # Tiros da horda com temporizador explicito, mais confiavel que probabilidade por frame.
        self.enemy_shot_timer -= dt
        if self.enemy_shot_timer <= 0 and alive:
            self.enemy_shot_timer = random.uniform(0.42, 0.85)
            shooter = random.choice(alive)
            image = random.choice(self.assets.enemy_bullet_sprites)
            self.enemy_bullets.append(Bullet(shooter.rect.centerx, shooter.rect.bottom + image.get_height() // 2, 0, 330 * self.layout.scale, 10, "enemy", image))

    def update_boss(self, dt):
        if self.boss and self.boss.alive:
            self.boss.update(dt, self.player, self.enemy_bullets, self.lasers)

    def update_bullets(self, dt):
        for bullet in self.player_bullets + self.enemy_bullets:
            bullet.update(dt)
        for laser in self.lasers:
            laser.update(dt)
        self.player_bullets = [b for b in self.player_bullets if not b.offscreen(self.layout)]
        self.enemy_bullets = [b for b in self.enemy_bullets if not b.offscreen(self.layout)]
        self.lasers = [laser for laser in self.lasers if laser.alive]

    def update_explosions(self, dt):
        for explosion in self.explosions:
            explosion.update(dt)
        self.explosions = [ex for ex in self.explosions if ex.life > 0]

    def check_collisions(self):
        for bullet in list(self.player_bullets):
            hit = False
            for enemy in self.enemies:
                if enemy.alive and bullet.rect.colliderect(enemy.rect):
                    enemy.damage(bullet.damage)
                    hit = True
                    if not enemy.alive:
                        self.score += 100
                        self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery, self.assets.explosion))
                    break
            if not hit and self.boss and self.boss.alive and bullet.rect.colliderect(self.boss.rect):
                self.boss.damage(bullet.damage)
                hit = True
                self.score += 5
                if not self.boss.alive:
                    self.score += 1700
                    self.explosions.append(Explosion(self.boss.rect.centerx, self.boss.rect.centery, self.assets.explosion))
            if hit and bullet in self.player_bullets:
                self.player_bullets.remove(bullet)

        for bullet in list(self.enemy_bullets):
            if bullet.rect.colliderect(self.player.rect):
                self.player.damage(bullet.damage)
                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)

        for laser in self.lasers:
            if laser.rect.colliderect(self.player.rect) and laser.can_damage():
                self.player.damage(laser.damage)
                laser.reset_tick()

        for enemy in self.enemies:
            if enemy.alive and enemy.rect.colliderect(self.player.rect):
                self.player.damage(25)
                enemy.alive = False

    def check_end_conditions(self):
        if self.player.hp <= 0:
            self.finish_time = self.elapsed()
            self.result_text = "Derrota!"
            self.ranking = add_score_to_ranking(self.player_name or "PLAYER", self.score, self.finish_time)
            self.state = "gameover"
            return

        for enemy in self.enemies:
            if enemy.alive and enemy.rect.bottom >= self.player.rect.top:
                self.player.damage(PLAYER_MAX_HP)
                return

        if self.boss and not self.boss.alive:
            self.finish_time = self.elapsed()
            self.result_text = "Vitória!"
            self.ranking = add_score_to_ranking(self.player_name or "PLAYER", self.score, self.finish_time)
            self.state = "win"

    def draw_text_center(self, text, font, color, y):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(self.layout.width // 2, y))
        self.screen.blit(surface, rect)

    def draw_text_play_center(self, text, font, color, y):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(self.layout.play_rect.centerx, y))
        self.screen.blit(surface, rect)

    def draw_background(self):
        self.screen.fill((3, 4, 10))
        if self.assets.background:
            self.screen.blit(self.assets.background, self.layout.play_rect)
        else:
            pygame.draw.rect(self.screen, DARK, self.layout.play_rect)
            star_rng = random.Random(42)
            for _ in range(135):
                x = star_rng.randrange(self.layout.play_rect.left, self.layout.play_rect.right)
                y = star_rng.randrange(self.layout.play_rect.top, self.layout.play_rect.bottom)
                radius = star_rng.choice([1, 1, 2])
                pygame.draw.circle(self.screen, (70, 80, 120), (x, y), radius)
        vignette = pygame.Surface(self.layout.play_rect.size, pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 34))
        pygame.draw.rect(vignette, (255, 255, 255, 18), vignette.get_rect(), width=max(2, int(3 * self.layout.scale)))
        self.screen.blit(vignette, self.layout.play_rect)
        # Guias discretas nas laterais quando a tela fisica for horizontal.
        if self.layout.play_rect.left > 0:
            pygame.draw.rect(self.screen, (6, 8, 18), (0, 0, self.layout.play_rect.left, self.layout.height))
            pygame.draw.rect(self.screen, (6, 8, 18), (self.layout.play_rect.right, 0, self.layout.width - self.layout.play_rect.right, self.layout.height))

    def draw_cartoon_bar(self, rect, value, max_value, fill_color, label, label_color=WHITE, back_color=(39, 39, 55)):
        rect = pygame.Rect(rect)
        percent = 0 if max_value <= 0 else clamp(value / max_value, 0, 1)
        radius = max(7, rect.height // 2)
        outline = max(3, int(4 * self.layout.scale))
        shadow = rect.move(0, max(3, int(5 * self.layout.scale)))
        pygame.draw.rect(self.screen, (0, 0, 0, 105), shadow, border_radius=radius)
        pygame.draw.rect(self.screen, (24, 18, 34), rect, border_radius=radius)
        pygame.draw.rect(self.screen, WHITE, rect, width=outline, border_radius=radius)
        inner = rect.inflate(-outline * 2, -outline * 2)
        pygame.draw.rect(self.screen, back_color, inner, border_radius=max(5, inner.height // 2))
        fill_w = int(inner.width * percent)
        if fill_w > 0:
            fill_rect = pygame.Rect(inner.left, inner.top, fill_w, inner.height)
            pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=max(5, inner.height // 2))
            shine_h = max(2, inner.height // 3)
            shine = pygame.Surface((fill_w, shine_h), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 78))
            self.screen.blit(shine, (inner.left, inner.top + max(1, inner.height // 8)))
            pygame.draw.circle(self.screen, (255, 255, 255, 95), (inner.left + max(5, inner.height // 2), inner.centery), max(3, inner.height // 4))
        for step in range(1, 10):
            x = inner.left + inner.width * step // 10
            pygame.draw.line(self.screen, (255, 255, 255, 45), (x, inner.top + 3), (x, inner.bottom - 3), max(1, int(2 * self.layout.scale)))
        pygame.draw.rect(self.screen, (16, 12, 24), rect, width=max(2, int(2 * self.layout.scale)), border_radius=radius)
        text = self.font_tiny.render(label, True, label_color)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_hud(self):
        margin = int(18 * self.layout.scale)
        hud_y = self.layout.play_rect.top + int(14 * self.layout.scale)
        left_x = self.layout.play_rect.left + margin
        right_x = self.layout.play_rect.right - margin

        # Balao superior esquerdo: vida + contador visual de tiros restantes.
        panel_w = int(self.layout.play_rect.width * 0.44)
        panel_h = int(78 * self.layout.scale)
        panel = pygame.Rect(left_x, hud_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, (12, 16, 34), panel, border_radius=int(14 * self.layout.scale))
        pygame.draw.rect(self.screen, (42, 56, 95), panel, width=2, border_radius=int(14 * self.layout.scale))

        counter_img = self.assets.counter_sprites[clamp(self.player.ammo, 0, 6)]
        counter_rect = counter_img.get_rect(midleft=(panel.left + int(10 * self.layout.scale), panel.centery))
        self.screen.blit(counter_img, counter_rect)

        bar_x = counter_rect.right + int(12 * self.layout.scale)
        bar_w = max(60, panel.right - bar_x - int(10 * self.layout.scale))
        bar_h = int(16 * self.layout.scale)
        bar_y = panel.top + int(18 * self.layout.scale)
        hp_color = GREEN if self.player.hp > 35 else RED
        self.draw_cartoon_bar(
            pygame.Rect(bar_x, bar_y, bar_w, bar_h + int(7 * self.layout.scale)),
            self.player.hp,
            PLAYER_MAX_HP,
            hp_color,
            f"VIDA {self.player.hp}/{PLAYER_MAX_HP}",
        )

        # Pontos e tempo ficam no canto superior direito, fora do balao de vida/municao.
        score_txt = self.font_small.render(f"Pontos: {self.score}", True, WHITE)
        time_txt = self.font_small.render(f"Tempo: {self.elapsed():.1f}s", True, WHITE)
        self.screen.blit(score_txt, score_txt.get_rect(topright=(right_x, hud_y + int(4 * self.layout.scale))))
        self.screen.blit(time_txt, time_txt.get_rect(topright=(right_x, hud_y + int(31 * self.layout.scale))))

        if self.boss and self.boss.alive:
            bw = int(self.layout.play_rect.width * 0.72)
            bh = int(15 * self.layout.scale)
            bx = self.layout.play_rect.centerx - bw // 2
            by = self.layout.play_rect.top + int(145 * self.layout.scale)
            name_label = self.font_small.render("Dado Corrompido", True, WHITE)
            self.screen.blit(name_label, name_label.get_rect(center=(self.layout.play_rect.centerx, by - int(20 * self.layout.scale))))
            self.draw_cartoon_bar(
                pygame.Rect(bx, by, bw, bh + int(8 * self.layout.scale)),
                self.boss.hp,
                self.boss.max_hp,
                PURPLE,
                "CHEFE FINAL",
                label_color=(255, 235, 255),
                back_color=(52, 34, 66),
            )

    def draw_name_screen(self):
        self.draw_background()
        self.draw_text_play_center("SPACE INVADERS", self.font_big, CYAN, self.layout.py(0.13))
        self.draw_text_play_center("Digite seu nome", self.font_med, WHITE, self.layout.py(0.25))
        self.draw_text_play_center("ENTER para comecar", self.font_small, GRAY, self.layout.py(0.29))
        box_w = int(self.layout.play_rect.width * 0.72)
        box_h = int(62 * self.layout.scale)
        box = pygame.Rect(self.layout.play_rect.centerx - box_w // 2, self.layout.py(0.34), box_w, box_h)
        pygame.draw.rect(self.screen, PANEL, box, border_radius=12)
        pygame.draw.rect(self.screen, CYAN, box, width=3, border_radius=12)
        name = self.player_name if self.player_name else "_"
        txt = self.font_med.render(name, True, WHITE)
        self.screen.blit(txt, txt.get_rect(center=box.center))
        self.draw_ranking(self.layout.py(0.47))

    def draw_ranking(self, start_y):
        self.draw_text_play_center("RANKING", self.font_med, YELLOW, start_y)
        ranking = load_ranking()[:RANKING_LIMIT]
        if not ranking:
            self.draw_text_play_center("Sem pontuacoes ainda", self.font_small, GRAY, start_y + int(40 * self.layout.scale))
            return
        y = start_y + int(40 * self.layout.scale)
        panel_w = int(self.layout.play_rect.width * 0.86)
        panel_x = self.layout.play_rect.centerx - panel_w // 2
        for idx, item in enumerate(ranking, start=1):
            line = f"{idx:02d}. {item['name']:<10} {item['score']:>6} pts {item['time']:>6.2f}s"
            if idx == 1:
                # 1º lugar: fonte maior, cor dourada/especial
                font = pygame.font.Font(None, int(26 * self.layout.scale))
                color = YELLOW
                row_h = int(32 * self.layout.scale)
                row = pygame.Rect(panel_x, y - int(14 * self.layout.scale), panel_w, row_h)
                pygame.draw.rect(self.screen, (45, 38, 8), row, border_radius=6)
                pygame.draw.rect(self.screen, YELLOW, row, width=2, border_radius=6)
            elif idx == 2:
                font = pygame.font.Font(None, int(22 * self.layout.scale))
                color = CYAN
                row_h = int(28 * self.layout.scale)
                row = pygame.Rect(panel_x, y - int(12 * self.layout.scale), panel_w, row_h)
                pygame.draw.rect(self.screen, (8, 30, 45), row, border_radius=5)
            elif idx == 3:
                font = pygame.font.Font(None, int(22 * self.layout.scale))
                color = ORANGE
                row_h = int(28 * self.layout.scale)
                row = pygame.Rect(panel_x, y - int(12 * self.layout.scale), panel_w, row_h)
                pygame.draw.rect(self.screen, (35, 18, 5), row, border_radius=5)
            else:
                font = self.font_tiny
                color = WHITE
                row = pygame.Rect(panel_x, y - int(12 * self.layout.scale), panel_w, int(25 * self.layout.scale))
                if idx % 2 == 1:
                    pygame.draw.rect(self.screen, (18, 23, 45), row, border_radius=5)
            surf = font.render(line, True, color)
            self.screen.blit(surf, surf.get_rect(center=(self.layout.play_rect.centerx, y)))
            if idx == 1:
                y += int(36 * self.layout.scale)
            elif idx in (2, 3):
                y += int(30 * self.layout.scale)
            else:
                y += int(28 * self.layout.scale)

    def draw_playing(self):
        self.draw_background()
        for enemy in self.enemies:
            if enemy.alive:
                enemy.draw(self.screen)
        if self.boss and self.boss.alive:
            self.boss.draw(self.screen)
        for bullet in self.player_bullets + self.enemy_bullets:
            bullet.draw(self.screen)
        for laser in self.lasers:
            laser.draw(self.screen)
        for explosion in self.explosions:
            explosion.draw(self.screen)
        self.player.draw(self.screen)
        self.draw_hud()

    def draw_end_screen(self):
        self.draw_playing()
        overlay = pygame.Surface((self.layout.width, self.layout.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 178))
        self.screen.blit(overlay, (0, 0))
        title = self.result_text
        self.draw_text_play_center(title, self.font_big, YELLOW if self.state == "win" else RED, self.layout.py(0.17))
        self.draw_text_play_center(f"Pontos: {self.score}", self.font_med, WHITE, self.layout.py(0.25))
        self.draw_text_play_center(f"Tempo: {self.finish_time:.2f}s", self.font_small, CYAN, self.layout.py(0.30))
        self.draw_ranking(self.layout.py(0.40))
        self.draw_text_play_center("ENTER para jogar novamente", self.font_small, CYAN, self.layout.py(0.91))
        self.draw_text_play_center("ESC para sair", self.font_tiny, GRAY, self.layout.py(0.945))

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000
            self.handle_events()
            if self.state == "playing":
                self.update_playing(dt)
                self.draw_playing()
            elif self.state == "countdown":
                self.update_countdown(dt)
                self.draw_countdown()
            elif self.state == "name":
                self.draw_name_screen()
            else:
                self.draw_end_screen()
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
