import pygame
import random
import sys
import math
import ctypes

pygame.init()

# 禁用IME输入法，防止切屏后IME拦截键盘事件
try:
    pygame.key.stop_text_input()
except Exception:
    pass

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

COLORS = {
    'black': (0, 0, 0), 'white': (255, 255, 255),
    'dark_gray': (40, 40, 40), 'gray': (128, 128, 128),
    'light_gray': (200, 200, 200), 'brown': (139, 69, 19),
    'dark_brown': (101, 67, 33), 'green': (34, 139, 34),
    'dark_green': (0, 100, 0), 'blue': (70, 130, 180),
    'red': (220, 20, 60), 'yellow': (255, 215, 0),
    'purple': (128, 0, 128), 'floor': (160, 120, 80),
    'wall': (100, 80, 60), 'wall_top': (120, 100, 80),
    'player': (0, 255, 100), 'enemy': (255, 50, 50),
    'item': (255, 215, 0)
}

TILE_WIDTH = 64
TILE_HEIGHT = 32
MAP_WIDTH = 40
MAP_HEIGHT = 40
TILE_FLOOR = 0
TILE_WALL = 1

user32 = ctypes.windll.user32


def is_window_foreground():
    hwnd = pygame.display.get_wm_info()['window']
    return user32.GetForegroundWindow() == hwnd


class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.width, self.height = x, y, w, h
        self.centerX = x + w // 2
        self.centerY = y + h // 2


class BSPMapGenerator:
    def __init__(self, w, h, min_size=6):
        self.w, self.h, self.min_size = w, h, min_size
        self.rooms = []
        self.map = [[TILE_WALL] * w for _ in range(h)]

    def generate(self):
        self._split(1, 1, self.w - 2, self.h - 2)
        self._connect()
        return self.map, self.rooms

    def _split(self, x, y, w, h):
        if w < self.min_size * 2 + 1 or h < self.min_size * 2 + 1:
            rw = random.randint(self.min_size, min(w, 12))
            rh = random.randint(self.min_size, min(h, 10))
            r = Room(random.randint(x, x + w - rw), random.randint(y, y + h - rh), rw, rh)
            self.rooms.append(r)
            for ry in range(r.y, r.y + r.height):
                for rx in range(r.x, r.x + r.width):
                    if 0 <= rx < self.w and 0 <= ry < self.h:
                        self.map[ry][rx] = TILE_FLOOR
            return
        if random.random() < 0.5 and w >= self.min_size * 2 + 1:
            sx = random.randint(x + self.min_size, x + w - self.min_size)
            self._split(x, y, sx - x, h)
            self._split(sx, y, x + w - sx, h)
        elif h >= self.min_size * 2 + 1:
            sy = random.randint(y + self.min_size, y + h - self.min_size)
            self._split(x, y, w, sy - y)
            self._split(x, sy, w, y + h - sy)
        else:
            rw = random.randint(self.min_size, min(w, 12))
            rh = random.randint(self.min_size, min(h, 10))
            r = Room(random.randint(x, x + w - rw), random.randint(y, y + h - rh), rw, rh)
            self.rooms.append(r)
            for ry in range(r.y, r.y + r.height):
                for rx in range(r.x, r.x + r.width):
                    if 0 <= rx < self.w and 0 <= ry < self.h:
                        self.map[ry][rx] = TILE_FLOOR

    def _connect(self):
        for i in range(len(self.rooms) - 1):
            r1, r2 = self.rooms[i], self.rooms[i + 1]
            x1, y1, x2, y2 = r1.centerX, r1.centerY, r2.centerX, r2.centerY
            if random.random() < 0.5:
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    if 0 <= x < self.w and 0 <= y1 < self.h:
                        self.map[y1][x] = TILE_FLOOR
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    if 0 <= x2 < self.w and 0 <= y < self.h:
                        self.map[y][x2] = TILE_FLOOR
            else:
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    if 0 <= x1 < self.w and 0 <= y < self.h:
                        self.map[y][x1] = TILE_FLOOR
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    if 0 <= x < self.w and 0 <= y2 < self.h:
                        self.map[y2][x] = TILE_FLOOR


class IsometricRenderer:
    def __init__(self, map_data, rooms):
        self.map_data = map_data
        self.rooms = rooms
        self.cam_x, self.cam_y = 0, 0
        self.tho = 16
        self.floor_colors = {}
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    base = COLORS['floor']
                    for r in self.rooms:
                        if r.x <= x < r.x + r.width and r.y <= y < r.y + r.height:
                            random.seed(x * 1000 + y)
                            v = random.randint(-10, 10)
                            self.floor_colors[(x, y)] = (
                                max(0, min(255, base[0] + v)),
                                max(0, min(255, base[1] + v)),
                                max(0, min(255, base[2] + v)))
                            random.seed()
                            break
                    else:
                        self.floor_colors[(x, y)] = base

    def _w2s_raw(self, wx, wy):
        return (wx - wy) * (TILE_WIDTH // 2), (wx + wy) * (TILE_HEIGHT // 2)

    def _w2s(self, wx, wy):
        sx, sy = self._w2s_raw(wx, wy)
        return sx - self.cam_x, sy - self.cam_y

    def update_camera(self, px, py):
        psx, psy = self._w2s_raw(px, py)
        tcx, tcy = psx - SCREEN_WIDTH // 2, psy - SCREEN_HEIGHT // 2
        corners = [self._w2s_raw(0, 0), self._w2s_raw(MAP_WIDTH, 0),
                    self._w2s_raw(0, MAP_HEIGHT), self._w2s_raw(MAP_WIDTH, MAP_HEIGHT)]
        min_x = min(c[0] for c in corners)
        max_x = max(c[0] for c in corners)
        min_y = min(c[1] for c in corners)
        max_y = max(c[1] for c in corners)
        m = 50
        if max_x - min_x + m * 2 <= SCREEN_WIDTH:
            tcx = (max_x - min_x - SCREEN_WIDTH) // 2 + min_x
        else:
            tcx = max(min_x - m, min(tcx, max_x - SCREEN_WIDTH + m))
        if max_y - min_y + m * 2 <= SCREEN_HEIGHT:
            tcy = (max_y - min_y - SCREEN_HEIGHT) // 2 + min_y
        else:
            tcy = max(min_y - m, min(tcy, max_y - SCREEN_HEIGHT + m))
        self.cam_x += (tcx - self.cam_x) * 0.15
        self.cam_y += (tcy - self.cam_y) * 0.15

    def render(self, surface, px, py):
        self.update_camera(px, py)
        surface.fill(COLORS['black'])
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    self._draw_floor(surface, x, y)
                elif self._wall_adj(x, y):
                    self._draw_wall(surface, x, y)
        self._draw_player(surface, px, py)

    def _wall_adj(self, x, y):
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if self.map_data[ny][nx] != TILE_WALL:
                    return True
        return False

    def _draw_floor(self, surface, x, y):
        sx, sy = self._w2s(x, y)
        pts = [(sx, sy - TILE_HEIGHT // 2), (sx + TILE_WIDTH // 2, sy),
               (sx, sy + TILE_HEIGHT // 2), (sx - TILE_WIDTH // 2, sy)]
        pygame.draw.polygon(surface, self.floor_colors.get((x, y), COLORS['floor']), pts)
        pygame.draw.polygon(surface, COLORS['dark_gray'], pts, 1)

    def _draw_wall(self, surface, x, y):
        sx, sy = self._w2s(x, y)
        h = self.tho
        pygame.draw.polygon(surface, COLORS['wall_top'],
                            [(sx, sy - TILE_HEIGHT // 2 - h), (sx + TILE_WIDTH // 2, sy - h),
                             (sx, sy + TILE_HEIGHT // 2 - h), (sx - TILE_WIDTH // 2, sy - h)])
        pygame.draw.polygon(surface, COLORS['wall'],
                            [(sx - TILE_WIDTH // 2, sy - h), (sx, sy + TILE_HEIGHT // 2 - h),
                             (sx, sy + TILE_HEIGHT // 2), (sx - TILE_WIDTH // 2, sy)])
        pygame.draw.polygon(surface, COLORS['dark_brown'],
                            [(sx + TILE_WIDTH // 2, sy - h), (sx, sy + TILE_HEIGHT // 2 - h),
                             (sx, sy + TILE_HEIGHT // 2), (sx + TILE_WIDTH // 2, sy)])

    def _draw_player(self, surface, x, y):
        sx, sy = int(self._w2s(x, y)[0]), int(self._w2s(x, y)[1])
        pts = [(sx, sy - TILE_HEIGHT // 2 - 8), (sx + 12, sy - 4),
               (sx, sy + TILE_HEIGHT // 2 - 8), (sx - 12, sy - 4)]
        pygame.draw.polygon(surface, COLORS['player'], pts)
        pygame.draw.polygon(surface, COLORS['white'], pts, 2)
        pygame.draw.circle(surface, COLORS['white'], (sx - 4, sy - 12), 3)
        pygame.draw.circle(surface, COLORS['white'], (sx + 4, sy - 12), 3)
        pygame.draw.circle(surface, COLORS['black'], (sx - 4, sy - 12), 1)
        pygame.draw.circle(surface, COLORS['black'], (sx + 4, sy - 12), 1)

    def draw_ui(self, surface, px, py):
        ui = pygame.Surface((200, 150))
        ui.fill(COLORS['dark_gray'])
        ui.set_alpha(200)
        surface.blit(ui, (10, 10))
        f = pygame.font.Font(None, 24)
        surface.blit(f.render("2.5D Roguelike", True, COLORS['white']), (20, 20))
        surface.blit(f.render(f"位置: ({int(px)}, {int(py)})", True, COLORS['light_gray']), (20, 50))
        for i, t in enumerate(["WASD/方向键: 移动", "R: 重新生成地图", "ESC: 暂停"]):
            surface.blit(f.render(t, True, COLORS['yellow']), (20, 80 + i * 20))
        ms = 120
        mm = pygame.Surface((ms, ms))
        mm.fill(COLORS['black'])
        mm.set_alpha(180)
        sc = ms / max(MAP_WIDTH, MAP_HEIGHT)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    c = COLORS['green'] if any(
                        r.x <= x < r.x + r.width and r.y <= y < r.y + r.height for r in self.rooms
                    ) else COLORS['floor']
                    pygame.draw.rect(mm, c, (int(x * sc), int(y * sc), max(1, int(sc)), max(1, int(sc))))
        pygame.draw.circle(mm, COLORS['player'], (int(px * sc), int(py * sc)), 3)
        surface.blit(mm, (SCREEN_WIDTH - ms - 10, 10))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2.5D Roguelike - 随机地图生成")
        self.map_data = None
        self.rooms = None
        self.player_x = 0.0
        self.player_y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.move_speed = 6.0
        self.is_moving = False
        self.renderer = None
        self.paused = False
        self.running = True
        self._focus_lost = False
        self.generate_new_map()

    def generate_new_map(self):
        gen = BSPMapGenerator(MAP_WIDTH, MAP_HEIGHT)
        self.map_data, self.rooms = gen.generate()
        if self.rooms:
            self.player_x = float(self.rooms[0].centerX)
            self.player_y = float(self.rooms[0].centerY)
            self.target_x = self.player_x
            self.target_y = self.player_y
        self.is_moving = False
        self.renderer = IsometricRenderer(self.map_data, self.rooms)

    def is_valid_cell(self, cx, cy):
        ix, iy = int(cx), int(cy)
        return 0 <= ix < MAP_WIDTH and 0 <= iy < MAP_HEIGHT and self.map_data[iy][ix] != TILE_WALL

    def _read_keys(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1.0
        if dx != 0 and dy != 0: dy = 0
        return dx, dy

    def start_move(self, dx, dy):
        nx, ny = self.target_x + dx, self.target_y + dy
        if self.is_valid_cell(nx, ny):
            self.target_x, self.target_y = nx, ny
            self.is_moving = True

    def update(self, dt):
        if self.is_moving:
            dx = self.target_x - self.player_x
            dy = self.target_y - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.05:
                self.player_x, self.player_y = self.target_x, self.target_y
                self.is_moving = False
            else:
                mv = min(self.move_speed * dt, dist)
                self.player_x += (dx / dist) * mv
                self.player_y += (dy / dist) * mv
            kdx, kdy = self._read_keys()
            if (kdx != 0 or kdy != 0) and dist > 0:
                dot = (dx * kdx + dy * kdy) / dist
                if dot < 0 and dist > 0.5:
                    self.start_move(kdx, kdy)
        else:
            dx, dy = self._read_keys()
            if dx != 0 or dy != 0:
                self.start_move(dx, dy)

    def _reset_keyboard(self):
        pygame.event.clear()
        pygame.event.pump()
        pygame.event.clear()
        pygame.key.stop_text_input()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.WINDOWFOCUSLOST:
                self.paused = True
                self._focus_lost = True
                self._draw_pause()
            if event.type == pygame.WINDOWFOCUSGAINED:
                self._focus_lost = False
                self._reset_keyboard()
                self.screen = pygame.display.set_mode(
                    (SCREEN_WIDTH, SCREEN_HEIGHT),
                    pygame.DOUBLEBUF | pygame.HWSURFACE
                )
                pygame.display.set_caption("2.5D Roguelike - 随机地图生成")
                self._draw_pause()
                continue
            if not is_window_foreground():
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._focus_lost:
                        self._focus_lost = False
                        continue
                    self.paused = not self.paused
                    if self.paused:
                        self._draw_pause()
                    continue
                if not self.paused and event.key == pygame.K_r:
                    self.generate_new_map()

    def _draw_pause(self):
        self.renderer.render(self.screen, self.player_x, self.player_y)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        f1 = pygame.font.Font(None, 72)
        f2 = pygame.font.Font(None, 36)
        t1 = f1.render("PAUSED", True, COLORS['white'])
        t2 = f2.render("Press ESC to resume", True, COLORS['light_gray'])
        self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            self.handle_events()
            if self.paused:
                pygame.time.wait(50)
                continue
            self.update(dt)
            self.renderer.render(self.screen, self.player_x, self.player_y)
            self.renderer.draw_ui(self.screen, self.player_x, self.player_y)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
