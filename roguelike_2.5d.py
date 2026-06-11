import pygame
import random
import sys
import math
import ctypes

pygame.init()

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

TILE_WIDTH = 16
TILE_HEIGHT = 8
MAP_WIDTH = 400
MAP_HEIGHT = 400
TILE_FLOOR = 0
TILE_WALL = 1

user32 = ctypes.windll.user32


def is_window_foreground():
    try:
        hwnd = pygame.display.get_wm_info()['window']
        return user32.GetForegroundWindow() == hwnd
    except Exception:
        return True


class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.width, self.height = x, y, w, h
        self.centerX = x + w // 2
        self.centerY = y + h // 2


class BSPMapGenerator:
    def __init__(self, w, h, min_size=60):
        self.w, self.h, self.min_size = w, h, min_size
        self.rooms = []
        self.map = [[TILE_WALL] * w for _ in range(h)]

    def generate(self):
        self._split(1, 1, self.w - 2, self.h - 2)
        self._connect()
        return self.map, self.rooms

    def _split(self, x, y, w, h):
        if w < self.min_size * 2 + 1 or h < self.min_size * 2 + 1:
            rw = random.randint(self.min_size, min(w, 120))
            rh = random.randint(self.min_size, min(h, 100))
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
            rw = random.randint(self.min_size, min(w, 120))
            rh = random.randint(self.min_size, min(h, 100))
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


class Renderer:
    def __init__(self, surface, map_data, rooms):
        self.surface = surface
        self.map_data = map_data
        self.rooms = rooms
        self.cam_x, self.cam_y = 0.0, 0.0
        self.target_cam_x, self.target_cam_y = 0.0, 0.0
        self.map_offset_x = 0
        self.map_offset_y = 0
        self.map_surface = None
        self.map_surf_w = 0
        self.map_surf_h = 0
        self._build_map_surface()

    def _w2s_raw(self, wx, wy):
        return (wx - wy) * (TILE_WIDTH // 2), (wx + wy) * (TILE_HEIGHT // 2)

    def _build_map_surface(self):
        corners = [self._w2s_raw(0, 0), self._w2s_raw(MAP_WIDTH, 0),
                    self._w2s_raw(0, MAP_HEIGHT), self._w2s_raw(MAP_WIDTH, MAP_HEIGHT)]
        min_x = min(c[0] for c in corners)
        min_y = min(c[1] for c in corners)
        max_x = max(c[0] for c in corners)
        max_y = max(c[1] for c in corners)
        self.map_offset_x = -min_x + TILE_WIDTH
        self.map_offset_y = -min_y + 4 + TILE_HEIGHT
        self.map_surf_w = max_x - min_x + TILE_WIDTH * 2
        self.map_surf_h = max_y - min_y + 8 + TILE_HEIGHT * 2
        self.map_surface = pygame.Surface((self.map_surf_w, self.map_surf_h))
        self.map_surface.fill(COLORS['black'])

        floor_colors = {}
        base = COLORS['floor']
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    for r in self.rooms:
                        if r.x <= x < r.x + r.width and r.y <= y < r.y + r.height:
                            random.seed(x * 1000 + y)
                            v = random.randint(-10, 10)
                            floor_colors[(x, y)] = (
                                max(0, min(255, base[0] + v)),
                                max(0, min(255, base[1] + v)),
                                max(0, min(255, base[2] + v)))
                            random.seed()
                            break
                    else:
                        floor_colors[(x, y)] = base

        def adj_wall(x, y):
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                    if self.map_data[ny][nx] != TILE_WALL:
                        return True
            return False

        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                sx = (x - y) * (TILE_WIDTH // 2) + self.map_offset_x
                sy = (x + y) * (TILE_HEIGHT // 2) + self.map_offset_y
                if self.map_data[y][x] != TILE_WALL:
                    color = floor_colors.get((x, y), base)
                    pts = [(sx, sy - TILE_HEIGHT // 2), (sx + TILE_WIDTH // 2, sy),
                           (sx, sy + TILE_HEIGHT // 2), (sx - TILE_WIDTH // 2, sy)]
                    pygame.draw.polygon(self.map_surface, color, pts)
                    pygame.draw.polygon(self.map_surface, COLORS['dark_gray'], pts, 1)
                elif adj_wall(x, y):
                    h = 4
                    pygame.draw.polygon(self.map_surface, COLORS['wall_top'],
                        [(sx, sy - TILE_HEIGHT // 2 - h), (sx + TILE_WIDTH // 2, sy - h),
                         (sx, sy + TILE_HEIGHT // 2 - h), (sx - TILE_WIDTH // 2, sy - h)])
                    pygame.draw.polygon(self.map_surface, COLORS['wall'],
                        [(sx - TILE_WIDTH // 2, sy - h), (sx, sy + TILE_HEIGHT // 2 - h),
                         (sx, sy + TILE_HEIGHT // 2), (sx - TILE_WIDTH // 2, sy)])
                    pygame.draw.polygon(self.map_surface, COLORS['dark_brown'],
                        [(sx + TILE_WIDTH // 2, sy - h), (sx, sy + TILE_HEIGHT // 2 - h),
                         (sx, sy + TILE_HEIGHT // 2), (sx + TILE_WIDTH // 2, sy)])

    def update_camera(self, px, py):
        psx, psy = self._w2s_raw(px, py)
        self.target_cam_x = psx - SCREEN_WIDTH // 2
        self.target_cam_y = psy - SCREEN_HEIGHT // 2
        corners = [self._w2s_raw(0, 0), self._w2s_raw(MAP_WIDTH, 0),
                    self._w2s_raw(0, MAP_HEIGHT), self._w2s_raw(MAP_WIDTH, MAP_HEIGHT)]
        min_x = min(c[0] for c in corners)
        max_x = max(c[0] for c in corners)
        min_y = min(c[1] for c in corners)
        max_y = max(c[1] for c in corners)
        m = 50
        if max_x - min_x + m * 2 <= SCREEN_WIDTH:
            self.target_cam_x = (max_x - min_x - SCREEN_WIDTH) // 2 + min_x
        else:
            self.target_cam_x = max(min_x - m, min(self.target_cam_x, max_x - SCREEN_WIDTH + m))
        if max_y - min_y + m * 2 <= SCREEN_HEIGHT:
            self.target_cam_y = (max_y - min_y - SCREEN_HEIGHT) // 2 + min_y
        else:
            self.target_cam_y = max(min_y - m, min(self.target_cam_y, max_y - SCREEN_HEIGHT + m))
        self.cam_x += (self.target_cam_x - self.cam_x) * 0.15
        self.cam_y += (self.target_cam_y - self.cam_y) * 0.15

    def render(self, px, py):
        self.update_camera(px, py)
        self.surface.fill(COLORS['black'])
        src_x = int(self.cam_x + self.map_offset_x - TILE_WIDTH) - 10
        src_y = int(self.cam_y + self.map_offset_y - 4 - TILE_HEIGHT) - 10
        src_x = max(0, min(src_x, self.map_surf_w - SCREEN_WIDTH))
        src_y = max(0, min(src_y, self.map_surf_h - SCREEN_HEIGHT))
        self.surface.blit(self.map_surface, (0, 0), (src_x, src_y, SCREEN_WIDTH, SCREEN_HEIGHT))
        # 玩家
        sx = int((px - py) * (TILE_WIDTH // 2) - self.cam_x)
        sy = int((px + py) * (TILE_HEIGHT // 2) - self.cam_y)
        pts = [(sx, sy - 9), (sx + 9, sy), (sx, sy + 9), (sx - 9, sy)]
        pygame.draw.polygon(self.surface, COLORS['player'], pts)
        pygame.draw.polygon(self.surface, COLORS['white'], pts, 2)

    def draw_ui(self, px, py):
        ui = pygame.Surface((200, 150))
        ui.fill(COLORS['dark_gray'])
        ui.set_alpha(200)
        self.surface.blit(ui, (10, 10))
        f = pygame.font.Font(None, 24)
        self.surface.blit(f.render("2.5D Roguelike", True, COLORS['white']), (20, 20))
        self.surface.blit(f.render(f"位置: ({int(px)}, {int(py)})", True, COLORS['light_gray']), (20, 50))
        for i, t in enumerate(["WASD/方向键: 移动", "R: 重新生成地图", "ESC: 暂停"]):
            self.surface.blit(f.render(t, True, COLORS['yellow']), (20, 80 + i * 20))
        # 小地图
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
        self.surface.blit(mm, (SCREEN_WIDTH - ms - 10, 10))


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
        self.renderer = Renderer(self.screen, self.map_data, self.rooms)

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
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        return dx, dy

    def start_move(self, dx, dy):
        if abs(dx) > 0.1 and abs(dy) > 0.1:
            step_x = 1.0 if dx > 0 else -1.0
            step_y = 1.0 if dy > 0 else -1.0
            if self.is_valid_cell(self.target_x + step_x, self.target_y + step_y):
                self.target_x += step_x
                self.target_y += step_y
                self.is_moving = True
            elif self.is_valid_cell(self.target_x + step_x, self.target_y):
                self.target_x += step_x
                self.is_moving = True
            elif self.is_valid_cell(self.target_x, self.target_y + step_y):
                self.target_y += step_y
                self.is_moving = True
        else:
            step_x = 1.0 if dx > 0.1 else (-1.0 if dx < -0.1 else 0.0)
            step_y = 1.0 if dy > 0.1 else (-1.0 if dy < -0.1 else 0.0)
            nx, ny = self.target_x + step_x, self.target_y + step_y
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
            if (kdx != 0 or kdy != 0) and dist > 0.3:
                dot = dx * kdx + dy * kdy
                if dot < 0:
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
        self.renderer.render(self.player_x, self.player_y)
        self.renderer.draw_ui(self.player_x, self.player_y)
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
            self.renderer.render(self.player_x, self.player_y)
            self.renderer.draw_ui(self.player_x, self.player_y)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
