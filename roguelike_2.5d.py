import pygame
import random
import sys
from collections import deque

# 初始化Pygame
pygame.init()

# 屏幕设置
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2.5D Roguelike - 随机地图生成")

# 颜色定义
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

# 等距视角参数
TILE_WIDTH = 64
TILE_HEIGHT = 32
MAP_WIDTH = 40
MAP_HEIGHT = 40

# 地图元素类型
TILE_FLOOR = 0
TILE_WALL = 1
TILE_DOOR = 2
TILE_STAIRS = 3

class Room:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.centerX = x + width // 2
        self.centerY = y + height // 2
    
    def intersects(self, other):
        return (self.x <= other.x + other.width and
                self.x + self.width >= other.x and
                self.y <= other.y + other.height and
                self.y + self.height >= other.y)

class BSPMapGenerator:
    def __init__(self, width, height, min_room_size=6):
        self.width = width
        self.height = height
        self.min_room_size = min_room_size
        self.rooms = []
        self.map = [[TILE_WALL for _ in range(width)] for _ in range(height)]
    
    def generate(self):
        # 使用BSP算法生成地图
        self._split_space(1, 1, self.width - 2, self.height - 2)
        self._connect_rooms()
        self._add_details()
        return self.map, self.rooms
    
    def _split_space(self, x, y, width, height):
        if width < self.min_room_size * 2 + 1 or height < self.min_room_size * 2 + 1:
            # 空间太小，创建房间
            room_width = random.randint(self.min_room_size, min(width, 12))
            room_height = random.randint(self.min_room_size, min(height, 10))
            room_x = random.randint(x, x + width - room_width)
            room_y = random.randint(y, y + height - room_height)
            
            room = Room(room_x, room_y, room_width, room_height)
            self.rooms.append(room)
            self._create_room(room)
            return
        
        # 决定是水平分割还是垂直分割
        if random.random() < 0.5 and width >= self.min_room_size * 2 + 1:
            # 垂直分割
            split_x = random.randint(x + self.min_room_size, x + width - self.min_room_size)
            self._split_space(x, y, split_x - x, height)
            self._split_space(split_x, y, x + width - split_x, height)
        elif height >= self.min_room_size * 2 + 1:
            # 水平分割
            split_y = random.randint(y + self.min_room_size, y + height - self.min_room_size)
            self._split_space(x, y, width, split_y - y)
            self._split_space(x, split_y, width, y + height - split_y)
        else:
            # 无法分割，创建房间
            room_width = random.randint(self.min_room_size, min(width, 12))
            room_height = random.randint(self.min_room_size, min(height, 10))
            room_x = random.randint(x, x + width - room_width)
            room_y = random.randint(y, y + height - room_height)
            
            room = Room(room_x, room_y, room_width, room_height)
            self.rooms.append(room)
            self._create_room(room)
    
    def _create_room(self, room):
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.map[y][x] = TILE_FLOOR
    
    def _connect_rooms(self):
        # 连接所有房间
        for i in range(len(self.rooms) - 1):
            room1 = self.rooms[i]
            room2 = self.rooms[i + 1]
            self._create_corridor(room1.centerX, room1.centerY, room2.centerX, room2.centerY)
    
    def _create_corridor(self, x1, y1, x2, y2):
        # 创建L形走廊
        if random.random() < 0.5:
            # 先水平后垂直
            self._create_h_corridor(x1, x2, y1)
            self._create_v_corridor(y1, y2, x2)
        else:
            # 先垂直后水平
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
    
    def _add_details(self):
        # 添加一些随机细节
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y][x] == TILE_FLOOR:
                    # 随机添加一些装饰
                    if random.random() < 0.05:
                        # 可以在这里添加地板装饰
                        pass

class IsometricRenderer:
    def __init__(self, map_data, rooms):
        self.map_data = map_data
        self.rooms = rooms
        self.camera_x = 0
        self.camera_y = 0
        self.tile_height_offset = 16  # 墙壁高度
        self.floor_colors = {}  # 预计算的地板颜色
        self._precompute_floor_colors()
    
    def _precompute_floor_colors(self):
        # 预计算每个地板砖的颜色，避免闪烁
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    base_color = COLORS['floor']
                    for room in self.rooms:
                        if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
                            # 使用确定性的随机种子
                            random.seed(x * 1000 + y)
                            color_variation = random.randint(-10, 10)
                            self.floor_colors[(x, y)] = (
                                max(0, min(255, base_color[0] + color_variation)),
                                max(0, min(255, base_color[1] + color_variation)),
                                max(0, min(255, base_color[2] + color_variation))
                            )
                            random.seed()  # 重置随机种子
                            break
                    else:
                        self.floor_colors[(x, y)] = base_color
    
    def update_camera(self, player_x, player_y):
        # 计算玩家在世界坐标中的屏幕位置
        player_screen_x = (player_x - player_y) * (TILE_WIDTH // 2)
        player_screen_y = (player_x + player_y) * (TILE_HEIGHT // 2)
        
        # 目标摄像机位置：玩家在屏幕中央
        target_camera_x = player_screen_x - SCREEN_WIDTH // 2
        target_camera_y = player_screen_y - SCREEN_HEIGHT // 2
        
        # 计算地图边界（等距视角下的边界）
        # 地图四个角的世界坐标转换到屏幕坐标
        corners = [
            self.world_to_screen_raw(0, 0),
            self.world_to_screen_raw(MAP_WIDTH, 0),
            self.world_to_screen_raw(0, MAP_HEIGHT),
            self.world_to_screen_raw(MAP_WIDTH, MAP_HEIGHT)
        ]
        
        min_x = min(c[0] for c in corners)
        max_x = max(c[0] for c in corners)
        min_y = min(c[1] for c in corners)
        max_y = max(c[1] for c in corners)
        
        map_width_screen = max_x - min_x
        map_height_screen = max_y - min_y
        
        # 边界限制：确保地图边缘距离窗口边缘不超过50像素
        margin = 50
        
        # 如果地图比屏幕小，居中显示
        if map_width_screen + margin * 2 <= SCREEN_WIDTH:
            target_camera_x = (map_width_screen - SCREEN_WIDTH) // 2 + min_x
        else:
            # 限制摄像机，使地图边缘不超过margin像素
            target_camera_x = max(min_x - margin, min(target_camera_x, max_x - SCREEN_WIDTH + margin))
        
        if map_height_screen + margin * 2 <= SCREEN_HEIGHT:
            target_camera_y = (map_height_screen - SCREEN_HEIGHT) // 2 + min_y
        else:
            target_camera_y = max(min_y - margin, min(target_camera_y, max_y - SCREEN_HEIGHT + margin))
        
        # 平滑跟随
        self.camera_x += (target_camera_x - self.camera_x) * 0.15
        self.camera_y += (target_camera_y - self.camera_y) * 0.15
    
    def world_to_screen_raw(self, world_x, world_y):
        # 世界坐标转屏幕坐标（不应用摄像机偏移）
        screen_x = (world_x - world_y) * (TILE_WIDTH // 2)
        screen_y = (world_x + world_y) * (TILE_HEIGHT // 2)
        return screen_x, screen_y
    
    def world_to_screen(self, world_x, world_y):
        # 世界坐标转屏幕坐标（等距视角）
        screen_x = (world_x - world_y) * (TILE_WIDTH // 2)
        screen_y = (world_x + world_y) * (TILE_HEIGHT // 2)
        return screen_x - self.camera_x, screen_y - self.camera_y
    
    def screen_to_world(self, screen_x, screen_y):
        # 屏幕坐标转世界坐标
        screen_x += self.camera_x
        screen_y += self.camera_y
        world_x = (screen_x / (TILE_WIDTH // 2) + screen_y / (TILE_HEIGHT // 2)) / 2
        world_y = (screen_y / (TILE_HEIGHT // 2) - screen_x / (TILE_WIDTH // 2)) / 2
        return int(world_x), int(world_y)
    
    def render(self, surface, player_x, player_y):
        # 更新摄像机位置
        self.update_camera(player_x, player_y)
        
        surface.fill(COLORS['black'])
        
        # 渲染地图
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    self._draw_floor_tile(surface, x, y)
                
                if self.map_data[y][x] == TILE_WALL:
                    # 检查是否需要绘制墙壁（只绘制有地板相邻的墙壁）
                    if self._should_draw_wall(x, y):
                        self._draw_wall_tile(surface, x, y)
        
        # 渲染玩家
        self._draw_player(surface, player_x, player_y)
        
        # 渲染UI
        self._draw_ui(surface, player_x, player_y)
    
    def _should_draw_wall(self, x, y):
        # 检查周围是否有地板
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if self.map_data[ny][nx] != TILE_WALL:
                    return True
        return False
    
    def _draw_floor_tile(self, surface, x, y):
        screen_x, screen_y = self.world_to_screen(x, y)
        
        # 绘制菱形地板
        points = [
            (screen_x, screen_y - TILE_HEIGHT // 2),
            (screen_x + TILE_WIDTH // 2, screen_y),
            (screen_x, screen_y + TILE_HEIGHT // 2),
            (screen_x - TILE_WIDTH // 2, screen_y)
        ]
        
        # 使用预计算的颜色
        color = self.floor_colors.get((x, y), COLORS['floor'])
        
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, COLORS['dark_gray'], points, 1)
    
    def _draw_wall_tile(self, surface, x, y):
        screen_x, screen_y = self.world_to_screen(x, y)
        
        # 绘制墙壁顶部
        top_points = [
            (screen_x, screen_y - TILE_HEIGHT // 2 - self.tile_height_offset),
            (screen_x + TILE_WIDTH // 2, screen_y - self.tile_height_offset),
            (screen_x, screen_y + TILE_HEIGHT // 2 - self.tile_height_offset),
            (screen_x - TILE_WIDTH // 2, screen_y - self.tile_height_offset)
        ]
        pygame.draw.polygon(surface, COLORS['wall_top'], top_points)
        pygame.draw.polygon(surface, COLORS['dark_gray'], top_points, 1)
        
        # 绘制墙壁前面
        front_points = [
            (screen_x - TILE_WIDTH // 2, screen_y - self.tile_height_offset),
            (screen_x, screen_y + TILE_HEIGHT // 2 - self.tile_height_offset),
            (screen_x, screen_y + TILE_HEIGHT // 2),
            (screen_x - TILE_WIDTH // 2, screen_y)
        ]
        pygame.draw.polygon(surface, COLORS['wall'], front_points)
        pygame.draw.polygon(surface, COLORS['dark_gray'], front_points, 1)
        
        # 绘制墙壁右面
        right_points = [
            (screen_x + TILE_WIDTH // 2, screen_y - self.tile_height_offset),
            (screen_x, screen_y + TILE_HEIGHT // 2 - self.tile_height_offset),
            (screen_x, screen_y + TILE_HEIGHT // 2),
            (screen_x + TILE_WIDTH // 2, screen_y)
        ]
        pygame.draw.polygon(surface, COLORS['dark_brown'], right_points)
        pygame.draw.polygon(surface, COLORS['dark_gray'], right_points, 1)
    
    def _draw_player(self, surface, x, y):
        screen_x, screen_y = self.world_to_screen(x, y)
        screen_x = int(screen_x)
        screen_y = int(screen_y)
        
        # 绘制玩家（简单的菱形）
        points = [
            (screen_x, screen_y - TILE_HEIGHT // 2 - 8),
            (screen_x + 12, screen_y - 4),
            (screen_x, screen_y + TILE_HEIGHT // 2 - 8),
            (screen_x - 12, screen_y - 4)
        ]
        pygame.draw.polygon(surface, COLORS['player'], points)
        pygame.draw.polygon(surface, COLORS['white'], points, 2)
        
        # 绘制玩家眼睛
        pygame.draw.circle(surface, COLORS['white'], (screen_x - 4, screen_y - 12), 3)
        pygame.draw.circle(surface, COLORS['white'], (screen_x + 4, screen_y - 12), 3)
        pygame.draw.circle(surface, COLORS['black'], (screen_x - 4, screen_y - 12), 1)
        pygame.draw.circle(surface, COLORS['black'], (screen_x + 4, screen_y - 12), 1)
    
    def _draw_ui(self, surface, player_x, player_y):
        # 绘制UI面板
        ui_panel = pygame.Surface((200, 150))
        ui_panel.fill(COLORS['dark_gray'])
        ui_panel.set_alpha(200)
        surface.blit(ui_panel, (10, 10))
        
        # 绘制文字
        font = pygame.font.Font(None, 24)
        title_text = font.render("2.5D Roguelike", True, COLORS['white'])
        surface.blit(title_text, (20, 20))
        
        pos_text = font.render(f"位置: ({player_x}, {player_y})", True, COLORS['light_gray'])
        surface.blit(pos_text, (20, 50))
        
        controls = [
            "WASD/方向键: 移动",
            "R: 重新生成地图",
            "ESC: 退出"
        ]
        
        for i, control in enumerate(controls):
            control_text = font.render(control, True, COLORS['yellow'])
            surface.blit(control_text, (20, 80 + i * 20))
        
        # 绘制小地图
        self._draw_minimap(surface, player_x, player_y)
    
    def _draw_minimap(self, surface, player_x, player_y):
        minimap_size = 120
        minimap_surface = pygame.Surface((minimap_size, minimap_size))
        minimap_surface.fill(COLORS['black'])
        minimap_surface.set_alpha(180)
        
        scale = minimap_size / max(MAP_WIDTH, MAP_HEIGHT)
        
        # 绘制地图
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] != TILE_WALL:
                    color = COLORS['floor']
                    for room in self.rooms:
                        if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
                            color = COLORS['green']
                            break
                    
                    pygame.draw.rect(minimap_surface, color, 
                                   (int(x * scale), int(y * scale), max(1, int(scale)), max(1, int(scale))))
        
        # 绘制玩家
        pygame.draw.circle(minimap_surface, COLORS['player'], 
                          (int(player_x * scale), int(player_y * scale)), 3)
        
        surface.blit(minimap_surface, (SCREEN_WIDTH - minimap_size - 10, 10))

class Game:
    def __init__(self):
        self.map_data = None
        self.rooms = None
        self.player_x = 0.0
        self.player_y = 0.0
        self.move_speed = 3.0  # 移动速度（每秒格数）
        self.renderer = None
        self.keys_pressed = set()
        self.generate_new_map()
    
    def generate_new_map(self):
        # 生成新地图
        generator = BSPMapGenerator(MAP_WIDTH, MAP_HEIGHT)
        self.map_data, self.rooms = generator.generate()
        
        # 将玩家放在第一个房间
        if self.rooms:
            self.player_x = float(self.rooms[0].centerX)
            self.player_y = float(self.rooms[0].centerY)
        
        self.renderer = IsometricRenderer(self.map_data, self.rooms)
    
    def is_valid_position(self, x, y):
        # 检查位置是否有效（基于浮点坐标）
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
            return self.map_data[map_y][map_x] != TILE_WALL
        return False
    
    def update(self, dt):
        # 根据按键状态移动
        dx = 0.0
        dy = 0.0
        
        if pygame.K_w in self.keys_pressed or pygame.K_UP in self.keys_pressed:
            dy -= 1.0
        if pygame.K_s in self.keys_pressed or pygame.K_DOWN in self.keys_pressed:
            dy += 1.0
        if pygame.K_a in self.keys_pressed or pygame.K_LEFT in self.keys_pressed:
            dx -= 1.0
        if pygame.K_d in self.keys_pressed or pygame.K_RIGHT in self.keys_pressed:
            dx += 1.0
        
        # 归一化对角线移动
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        
        # 计算新位置
        new_x = self.player_x + dx * self.move_speed * dt
        new_y = self.player_y + dy * self.move_speed * dt
        
        # 分轴碰撞检测，允许滑动
        if self.is_valid_position(new_x, self.player_y):
            self.player_x = new_x
        if self.is_valid_position(self.player_x, new_y):
            self.player_y = new_y
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r:
                    self.generate_new_map()
                else:
                    self.keys_pressed.add(event.key)
            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)
        
        return True
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            dt = clock.tick(60) / 1000.0  # 秒为单位的时间差
            running = self.handle_input()
            self.update(dt)
            self.renderer.render(screen, self.player_x, self.player_y)
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()