import pygame
import random
import sys
import math

pygame.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'dark_gray': (40, 40, 40),
    'gray': (128, 128, 128),
    'light_gray': (200, 200, 200),
    'brown': (139, 69, 19),
    'dark_brown': (101, 67, 33),
    'green': (34, 139, 34),
    'dark_green': (0, 100, 0),
    'blue': (70, 130, 180),
    'red': (220, 20, 60),
    'yellow': (255, 215, 0),
    'purple': (128, 0, 128),
    'floor': (160, 120, 80),
    'wall': (100, 80, 60),
    'wall_top': (120, 100, 80),
    'player': (0, 255, 100),
    'enemy': (255, 50, 50),
    'item': (255, 215, 0)
}

TILE_WIDTH = 64
TILE_HEIGHT = 32
MAP_WIDTH = 40
MAP_HEIGHT = 40

TILE_FLOOR = 0
TILE_WALL = 1


class Room:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.centerX = x + width // 2
        self.centerY = y + height // 2


class BSPMapGenerator:
    def __init__(self, width, height, min_room_size=6):
        self.width = width
        self.height = height
        self.min_room_size = min_room_size
        self.rooms = []
        self.map = [[TILE_WALL for _ in range(width)] for _ in range(height)]

    def generate(self):
        self._split_space(1, 1, self.width - 2, self.height - 2)
        self._connect_rooms()
        return self.map, self.rooms

    def _split_space(self, x, y, width, height):
        if width < self.min_room_size * 2 + 1 or height < self.min_room_size * 2 + 1:
            rw = random.randint(self.min_room_size, min(width, 12))
            rh = random.randint(self.min_room_size, min(height, 10))
            rx = random.randint(x, x + width - rw)
            ry = random.randint(y, y + height - rh)
            room = Room(rx, ry, rw, rh)
            self.rooms.append(room)
            self._create_room(room)
            return
        if random.random() < 0.5 and width >= self.min_room_size * 2 + 1:
            sx = random.randint(x + self.min_room_size, x + width - self.min_room_size)
            self._split_space(x, y, sx - x, height)
            self._split_space(sx, y, x + width - sx, height)
        elif height >= self.min_room_size * 2 + 1:
            sy = random.randint(y + self.min_room_size, y + height - self.min_room_size)
            self._split_space(x, y, width, sy - y)
            self._split_space(x, sy, width, y + height - sy)
        else:
            rw = random.randint(self.min_room_size, min(width, 12))
            rh = random.randint(self.min_room_size, min(height, 10))
            rx = random.randint(x, x + width - rw)
            ry = random.randint(y, y + height - rh)
            room = Room(rx, ry, rw, rh)
            self.rooms.append(room)
            self._create_room(room)

    def _create_room(self, room):
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.map[y][x] = TILE_FLOOR

    def _connect_rooms(self):
        for i in range(len(self.rooms) - 1):
            r1, r2 = self.rooms[i], self.rooms[i + 1]
            self._create_corridor(r1.centerX, r1.centerY, r2.centerX, r2.centerY)

    def _create_corridor(self, x1, y1, x2, y2):
        if random.random() < 0.5:
            self._create_h_corridor(x1, x2, y1)
            self._create_v_corridor(y1, y2, x2)
        else:
            self._create_v_corridor(y1, y2, x1)
            self._create_h_corridor(x1, x2, y2)

    def _create_h_corridor(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.map[y][x] = TILE_FLOOR

    def _create_v_corridor(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.map[y][x] = TILE_FLOOR


class IsometricRenderer:
    def __init__(self, map_data, rooms):
        self.map_data = map_data
        self.rooms = rooms
        self.camera_x = 0
        self.camera_y = 0
        self.tile_height_offset = 16
        self.floor_colors = {}
        self._precompute_floor_colors()

    def _precompute_floor_colors(self):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    base = COLORS['floor']
                    for room in self.rooms:
                        if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
                            random.seed(x * 1000 + y)
                            v = random.randint(-10, 10)
                            self.floor_colors[(x, y)] = (
                                max(0, min(255, base[0] + v)),
                                max(0, min(255, base[1] + v)),
                                max(0, min(255, base[2] + v))
                            )
                            random.seed()
                            break
                    else:
                        self.floor_colors[(x, y)] = base

    def update_camera(self, player_x, player_y):
        psx = (player_x - player_y) * (TILE_WIDTH // 2)
        psy = (player_x + player_y) * (TILE_HEIGHT // 2)
        tcx = psx - SCREEN_WIDTH // 2
        tcy = psy - SCREEN_HEIGHT // 2

        corners = [
            self._world_to_screen_raw(0, 0),
            self._world_to_screen_raw(MAP_WIDTH, 0),
            self._world_to_screen_raw(0, MAP_HEIGHT),
            self._world_to_screen_raw(MAP_WIDTH, MAP_HEIGHT)
        ]
        min_x = min(c[0] for c in corners)
        max_x = max(c[0] for c in corners)
        min_y = min(c[1] for c in corners)
        max_y = max(c[1] for c in corners)

        margin = 50
        if max_x - min_x + margin * 2 <= SCREEN_WIDTH:
            tcx = (max_x - min_x - SCREEN_WIDTH) // 2 + min_x
        else:
            tcx = max(min_x - margin, min(tcx, max_x - SCREEN_WIDTH + margin))
        if max_y - min_y + margin * 2 <= SCREEN_HEIGHT:
            tcy = (max_y - min_y - SCREEN_HEIGHT) // 2 + min_y
        else:
            tcy = max(min_y - margin, min(tcy, max_y - SCREEN_HEIGHT + margin))

        self.camera_x += (tcx - self.camera_x) * 0.15
        self.camera_y += (tcy - self.camera_y) * 0.15

    def _world_to_screen_raw(self, wx, wy):
        return (wx - wy) * (TILE_WIDTH // 2), (wx + wy) * (TILE_HEIGHT // 2)

    def world_to_screen(self, wx, wy):
        sx, sy = self._world_to_screen_raw(wx, wy)
        return sx - self.camera_x, sy - self.camera_y

    def render(self, surface, player_x, player_y):
        self.update_camera(player_x, player_y)
        surface.fill(COLORS['black'])

        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    self._draw_floor(surface, x, y)
                elif self._should_draw_wall(x, y):
                    self._draw_wall(surface, x, y)

        self._draw_player(surface, player_x, player_y)
        self._draw_ui(surface, player_x, player_y)

    def _should_draw_wall(self, x, y):
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if self.map_data[ny][nx] != TILE_WALL:
                    return True
        return False

    def _draw_floor(self, surface, x, y):
        sx, sy = self.world_to_screen(x, y)
        pts = [
            (sx, sy - TILE_HEIGHT // 2),
            (sx + TILE_WIDTH // 2, sy),
            (sx, sy + TILE_HEIGHT // 2),
            (sx - TILE_WIDTH // 2, sy)
        ]
        pygame.draw.polygon(surface, self.floor_colors.get((x, y), COLORS['floor']), pts)
        pygame.draw.polygon(surface, COLORS['dark_gray'], pts, 1)

    def _draw_wall(self, surface, x, y):
        sx, sy = self.world_to_screen(x, y)
        ho = self.tile_height_offset
        top = [(sx, sy - TILE_HEIGHT // 2 - ho), (sx + TILE_WIDTH // 2, sy - ho),
               (sx, sy + TILE_HEIGHT // 2 - ho), (sx - TILE_WIDTH // 2, sy - ho)]
        pygame.draw.polygon(surface, COLORS['wall_top'], top)
        pygame.draw.polygon(surface, COLORS['dark_gray'], top, 1)
        front = [(sx - TILE_WIDTH // 2, sy - ho), (sx, sy + TILE_HEIGHT // 2 - ho),
                 (sx, sy + TILE_HEIGHT // 2), (sx - TILE_WIDTH // 2, sy)]
        pygame.draw.polygon(surface, COLORS['wall'], front)
        pygame.draw.polygon(surface, COLORS['dark_gray'], front, 1)
        right = [(sx + TILE_WIDTH // 2, sy - ho), (sx, sy + TILE_HEIGHT // 2 - ho),
                 (sx, sy + TILE_HEIGHT // 2), (sx + TILE_WIDTH // 2, sy)]
        pygame.draw.polygon(surface, COLORS['dark_brown'], right)
        pygame.draw.polygon(surface, COLORS['dark_gray'], right, 1)

    def _draw_player(self, surface, x, y):
        sx, sy = int(self.world_to_screen(x, y)[0]), int(self.world_to_screen(x, y)[1])
        pts = [(sx, sy - TILE_HEIGHT // 2 - 8), (sx + 12, sy - 4),
               (sx, sy + TILE_HEIGHT // 2 - 8), (sx - 12, sy - 4)]
        pygame.draw.polygon(surface, COLORS['player'], pts)
        pygame.draw.polygon(surface, COLORS['white'], pts, 2)
        pygame.draw.circle(surface, COLORS['white'], (sx - 4, sy - 12), 3)
        pygame.draw.circle(surface, COLORS['white'], (sx + 4, sy - 12), 3)
        pygame.draw.circle(surface, COLORS['black'], (sx - 4, sy - 12), 1)
        pygame.draw.circle(surface, COLORS['black'], (sx + 4, sy - 12), 1)

    def _draw_ui(self, surface, player_x, player_y):
        ui = pygame.Surface((200, 150))
        ui.fill(COLORS['dark_gray'])
        ui.set_alpha(200)
        surface.blit(ui, (10, 10))
        font = pygame.font.Font(None, 24)
        surface.blit(font.render("2.5D Roguelike", True, COLORS['white']), (20, 20))
        surface.blit(font.render(f"位置: ({int(player_x)}, {int(player_y)})", True, COLORS['light_gray']), (20, 50))
        for i, txt in enumerate(["WASD/方向键: 移动", "R: 重新生成地图", "ESC: 暂停"]):
            surface.blit(font.render(txt, True, COLORS['yellow']), (20, 80 + i * 20))
        self._draw_minimap(surface, player_x, player_y)

    def _draw_minimap(self, surface, player_x, player_y):
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
        pygame.draw.circle(mm, COLORS['player'], (int(player_x * sc), int(player_y * sc)), 3)
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
        self._last_focus_time = 0
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
        if 0 <= ix < MAP_WIDTH and 0 <= iy < MAP_HEIGHT:
            return self.map_data[iy][ix] != TILE_WALL
        return False

    def _read_keys(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1.0
        if dx != 0 and dy != 0:
            dy = 0
        return dx, dy

    def start_move(self, dx, dy):
        nx, ny = self.target_x + dx, self.target_y + dy
        if self.is_valid_cell(nx, ny):
            self.target_x = nx
            self.target_y = ny
            self.is_moving = True

    def update(self, dt):
        if self.is_moving:
            dx = self.target_x - self.player_x
            dy = self.target_y - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.05:
                self.player_x = self.target_x
                self.player_y = self.target_y
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
        pygame.key.stop_text_input()
        pygame.key.start_text_input()
        pygame.event.clear()

    def _reinit_window(self):
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.DOUBLEBUF | pygame.HWSURFACE
        )
        pygame.display.set_caption("2.5D Roguelike - 随机地图生成")
        self._reset_keyboard()
        self._last_focus_time = pygame.time.get_ticks()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.WINDOWFOCUSLOST:
                self.paused = True
                self._render_pause()
            if event.type == pygame.WINDOWFOCUSGAINED:
                self._reinit_window()
                self._render_pause()
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    now = pygame.time.get_ticks()
                    if now - self._last_focus_time > 300:
                        self.paused = not self.paused
                        if self.paused:
                            self._render_pause()
                    continue
            if not self.paused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.generate_new_map()

    def _render_pause(self):
        self.renderer.render(self.screen, self.player_x, self.player_y)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        font_large = pygame.font.Font(None, 72)
        font_small = pygame.font.Font(None, 36)
        title = font_large.render("PAUSED", True, COLORS['white'])
        hint = font_small.render("Press ESC to resume", True, COLORS['light_gray'])
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
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
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
