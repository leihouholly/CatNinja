
# 为了避免打包出问题增加的部分 第二版
import sys
import os

# 必须放在最开头，且在所有其他导入之前
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# 禁止 Pygame 输出支持提示
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# 现在才导入其他模块
import pygame
import random
import math
import io   # 如果其他地方需要可以保留，但不要再重定向 stdout

# 你的其余代码保持不变...

"""
# 为了避免打包出问题增加的部分 第一版
import sys
import os

# 修复PyInstaller无控制台打包时的stdout为None问题
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# 下面才是你原来的代码，比如import pygame之类的
# 你的第4行代码现在就不会报错了
"""

import sys
import io

# 临时挂起
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pygame
import random
import math
import os

# 初始化 Pygame
pygame.init()
pygame.mixer.init()

# 屏幕设置
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fruit Ninja - Bounce Edition")
clock = pygame.time.Clock()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GOLD = (255, 215, 0)
COLORS = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE]

# 游戏区域 (上边界提高，为文字留出空间)
GAME_AREA_TOP = 150
GAME_AREA_BOTTOM = SCREEN_HEIGHT - 80

# 物理参数
GRAVITY = 0.3
BASE_FALL_SPEED = 2.0
BOUNCE_DAMP = 0.8
MAX_BOUNCES = 5
BASE_LIFESPAN_MS = 30000
MIN_LIFESPAN_MS = 5000
MAX_LIFESPAN_MS = 60000

# 得分影响寿命的累计计数
score_gain_count = 0
score_loss_count = 0
current_lifespan_ms = BASE_LIFESPAN_MS

# 全局速度因子
SPEED_FACTOR = 1.0

# 连击计数器
combo_counter = 0


# ==================== 资源加载 ====================
FRUIT_IMAGES_FOLDER = "fruits"
SPECIAL_FRUIT_FOLDER = os.path.join(FRUIT_IMAGES_FOLDER, "videos")
BACKGROUND_IMAGE_FOLDER = "background"
BUTTON_IMAGES_FOLDER = "buttons"

fruit_images = []
special_fruit_images = []
background_img = None
button_img_normal = None
button_img_hover = None


def load_image(path, scale_size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale_size:
            img = pygame.transform.scale(img, scale_size)
        return img
    except:
        return None


def load_resources():
    global fruit_images, special_fruit_images, background_img, button_img_normal, button_img_hover

    # 加载普通水果图片
    if os.path.exists(FRUIT_IMAGES_FOLDER):
        for file in os.listdir(FRUIT_IMAGES_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(FRUIT_IMAGES_FOLDER, file)
                if os.path.isdir(full_path):
                    continue
                img = load_image(full_path)
                if img:
                    fruit_images.append(img)
        print(f"Loaded {len(fruit_images)} fruit images")
    else:
        print(f"Folder '{FRUIT_IMAGES_FOLDER}' not found, using circles")

    # 加载特殊水果图片 (fruits/videos/ 下所有图片)
    if os.path.exists(SPECIAL_FRUIT_FOLDER):
        for file in os.listdir(SPECIAL_FRUIT_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = load_image(os.path.join(SPECIAL_FRUIT_FOLDER, file))
                if img:
                    special_fruit_images.append(img)
        if special_fruit_images:
            print(f"Loaded {len(special_fruit_images)} special fruit images from fruits/videos/")
        else:
            print("No valid images in fruits/videos/, using golden circle for special fruit")
    else:
        print(f"Folder '{SPECIAL_FRUIT_FOLDER}' not found, using golden circle for special fruit")

    # 加载背景（扫描文件夹，取第一个图片文件）
    if os.path.exists(BACKGROUND_IMAGE_FOLDER):
        bg_files = []
        for file in os.listdir(BACKGROUND_IMAGE_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                bg_files.append(file)
        if bg_files:
            bg_files.sort()
            first_bg = bg_files[0]
            bg_path = os.path.join(BACKGROUND_IMAGE_FOLDER, first_bg)
            background_img = load_image(bg_path)
            if background_img:
                background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print(f"Background image loaded: {first_bg}")
            else:
                print(f"Failed to load background image: {first_bg}")
        else:
            print(f"Folder '{BACKGROUND_IMAGE_FOLDER}' contains no valid images, using default background")
    else:
        print(f"Folder '{BACKGROUND_IMAGE_FOLDER}' not found, using default background")

    # 加载按钮图片
    if os.path.exists(BUTTON_IMAGES_FOLDER):
        for file in os.listdir(BUTTON_IMAGES_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                button_img_normal = load_image(os.path.join(BUTTON_IMAGES_FOLDER, file))
                if button_img_normal:
                    button_img_normal = pygame.transform.scale(button_img_normal, (100, 40))
                    print("Button image loaded")
                break
    else:
        print(f"Folder '{BUTTON_IMAGES_FOLDER}' not found, using default button")


# 字体 (安全加载)
try:
    font = pygame.font.SysFont("SimHei", 24)
    small_font = pygame.font.SysFont("SimHei", 18)
    combo_font = pygame.font.SysFont("SimHei", 22)
except:
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    combo_font = pygame.font.Font(None, 22)


# ========== 带阴影和边框的文字绘制函数 ==========
def draw_text_with_effect(surface, text, font, color, outline_color, shadow_color, x, y, shadow_offset=(2, 2)):
    shadow_surf = font.render(text, True, shadow_color)
    surface.blit(shadow_surf, (x + shadow_offset[0], y + shadow_offset[1]))
    text_surf = font.render(text, True, color)
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        outline_surf = font.render(text, True, outline_color)
        surface.blit(outline_surf, (x + dx, y + dy))
    surface.blit(text_surf, (x, y))


# ========== 速度滑块 ==========
class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min = min_val
        self.max = max_val
        self.val = initial_val
        self.handle_radius = h // 2
        self.handle_x = self.rect.x + int((initial_val - min_val) / (max_val - min_val) * w)
        self.dragging = False
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_handle(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_handle(event.pos[0])

    def update_handle(self, mouse_x):
        self.handle_x = max(self.rect.left, min(mouse_x, self.rect.right))
        ratio = (self.handle_x - self.rect.left) / self.rect.width
        self.val = self.min + ratio * (self.max - self.min)

    def draw(self, surface):
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=self.rect.height // 2)
        fill_rect = pygame.Rect(self.rect.left, self.rect.top, self.handle_x - self.rect.left, self.rect.height)
        pygame.draw.rect(surface, (0, 150, 200), fill_rect, border_radius=self.rect.height // 2)
        pygame.draw.circle(surface, WHITE, (self.handle_x, self.rect.centery), self.handle_radius)
        pygame.draw.circle(surface, BLACK, (self.handle_x, self.rect.centery), self.handle_radius, 2)
        label_text = f"{self.label}: {self.val:.1f}"
        draw_text_with_effect(surface, label_text, small_font, WHITE, BLACK, (80, 80, 80),
                              self.rect.left, self.rect.top - 20)


# ========== 水果类 ==========
class Fruit:
    def __init__(self, lifespan_ms, is_special=False):
        self.radius = random.randint(20, 40)
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = GAME_AREA_TOP - self.radius
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = BASE_FALL_SPEED * random.uniform(0.8, 1.2)
        self.sliced = False
        self.bounce_count = 0
        self.birth_time = pygame.time.get_ticks()
        self.lifespan_ms = lifespan_ms
        self.is_special = is_special
        self.score_multiplier = 3 if is_special else 1

        if self.is_special:
            self.fall_mode = True
            self.initial_radius = self.radius
            self.scale_factor = 1.0
            self.angle = 0
            self.fall_vy = random.uniform(2.5, 4.5)
            self.fall_vx = random.uniform(-1.0, 1.0)
            self.vx = self.fall_vx
            self.bounce_count = 0
            self.lifespan_ms = 9999999
        else:
            self.fall_mode = False

        if self.is_special and special_fruit_images:
            base_img = random.choice(special_fruit_images)
            self.image = pygame.transform.scale(base_img, (self.radius * 2, self.radius * 2))
            self.use_image = True
        elif fruit_images:
            self.image = random.choice(fruit_images)
            self.image = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
            self.use_image = True
        else:
            self.color = GOLD if self.is_special else random.choice(COLORS)
            self.use_image = False

    def update(self, speed_factor):
        if self.is_special and self.fall_mode:
            self.scale_factor = min(5.0, self.scale_factor + 0.022)
            self.radius = int(self.initial_radius * self.scale_factor)
            self.angle = (self.angle + 2) % 360
            self.x += self.vx * speed_factor
            self.y += self.fall_vy * speed_factor
            if (self.y + self.radius < GAME_AREA_TOP or
                self.y - self.radius > GAME_AREA_BOTTOM or
                self.x + self.radius < 0 or
                self.x - self.radius > SCREEN_WIDTH):
                return True
            return False

        self.vy += GRAVITY * speed_factor
        self.x += self.vx
        self.y += self.vy * speed_factor

        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = -self.vx * BOUNCE_DAMP
            self.bounce_count += 1
        if self.x + self.radius >= SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -self.vx * BOUNCE_DAMP
            self.bounce_count += 1
        if self.y - self.radius <= GAME_AREA_TOP:
            self.y = GAME_AREA_TOP + self.radius
            self.vy = -self.vy * BOUNCE_DAMP
            self.bounce_count += 1
        if self.y + self.radius >= GAME_AREA_BOTTOM:
            self.y = GAME_AREA_BOTTOM - self.radius
            self.vy = -self.vy * BOUNCE_DAMP
            self.bounce_count += 1

        if self.bounce_count >= MAX_BOUNCES:
            return True
        if pygame.time.get_ticks() - self.birth_time >= self.lifespan_ms:
            return True
        return False

    def draw(self, surface):
        if self.is_special and self.fall_mode:
            if self.use_image:
                scaled_img = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
                rotated_img = pygame.transform.rotate(scaled_img, self.angle)
                img_rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(rotated_img, img_rect)
            else:
                pygame.draw.circle(surface, GOLD, (int(self.x), int(self.y)), self.radius)
                highlight_radius = max(2, self.radius // 4)
                pygame.draw.circle(surface, WHITE, (int(self.x - self.radius // 4), int(self.y - self.radius // 4)),
                                   highlight_radius)
            star_text = "★3x★"
            draw_text_with_effect(surface, star_text, small_font, GOLD, BLACK, (80, 80, 80),
                                  self.x - self.radius, self.y + self.radius - 20)
            return

        if self.use_image:
            img_rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.image, img_rect)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            highlight_radius = max(2, self.radius // 4)
            pygame.draw.circle(surface, WHITE, (int(self.x - self.radius // 4), int(self.y - self.radius // 4)),
                               highlight_radius)

        bounce_text = f"Bounce:{self.bounce_count}/{MAX_BOUNCES}"
        draw_text_with_effect(surface, bounce_text, small_font, WHITE, BLACK, (80, 80, 80),
                              self.x - self.radius, self.y - self.radius - 10)

        if self.is_special:
            star_text = "★3x★"
            draw_text_with_effect(surface, star_text, small_font, GOLD, BLACK, (80, 80, 80),
                                  self.x - self.radius, self.y + self.radius - 20)

    def check_slice(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        cx, cy = self.x, self.y
        r = self.radius
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(cx - x1, cy - y1) <= r
        t = ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        nearest_x = x1 + t * dx
        nearest_y = y1 + t * dy
        dist = math.hypot(cx - nearest_x, cy - nearest_y)
        return dist <= r


# ========== 刀光效果 ==========
class SwipeTrail:
    def __init__(self):
        self.points = []
        self.max_len = 8
        self.life = 15

    def add_point(self, pos):
        self.points.append((pos[0], pos[1], self.life))
        if len(self.points) > self.max_len:
            self.points.pop(0)

    def update(self):
        for i in range(len(self.points)):
            x, y, life = self.points[i]
            life -= 1
            self.points[i] = (x, y, life)
        self.points = [p for p in self.points if p[2] > 0]

    def draw(self, surface):
        if len(self.points) < 2:
            return
        for i in range(len(self.points) - 1):
            x1, y1, life1 = self.points[i]
            x2, y2, life2 = self.points[i + 1]
            pygame.draw.line(surface, (200, 200, 200), (x1, y1), (x2, y2), max(2, int(5 * life1 / self.life)))


# ========== 按钮类 ==========
class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.use_image = button_img_normal is not None
        if self.use_image:
            self.img_normal = pygame.transform.scale(button_img_normal, (w, h))
            self.img_hover = self.img_normal.copy()
            self.img_hover.fill((50, 50, 50, 0), special_flags=pygame.BLEND_RGB_ADD)
        else:
            self.color = (50, 50, 150)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse_pos)
        if self.use_image:
            img = self.img_hover if hover else self.img_normal
            surface.blit(img, self.rect)
        else:
            color = (100, 100, 200) if hover else self.color
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
            draw_text_with_effect(surface, self.text, small_font, WHITE, BLACK, (80, 80, 80),
                                  self.rect.x + self.rect.width // 2 - small_font.size(self.text)[0] // 2,
                                  self.rect.y + self.rect.height // 2 - small_font.get_height() // 2)


# ==================== 音乐动态加载 ====================
MUSIC_FOLDER = "music"
music_files = []
current_music_index = 0
music_playing = True


def scan_music_files():
    supported_ext = ('.mp3', '.wav', '.ogg')
    files = []
    if os.path.exists(MUSIC_FOLDER):
        for file in os.listdir(MUSIC_FOLDER):
            if file.lower().endswith(supported_ext):
                files.append(file)
        files.sort()
    if files:
        print(f"Found {len(files)} music files: {files}")
    else:
        print(f"No music files found in '{MUSIC_FOLDER}' folder")
    return files


def load_music(index):
    global music_playing
    if not music_files:
        return False
    try:
        path = os.path.join(MUSIC_FOLDER, music_files[index])
        pygame.mixer.music.load(path)
        if music_playing:
            pygame.mixer.music.play(-1)
        print(f"Now playing: {music_files[index]}")
        return True
    except Exception as e:
        print(f"Cannot load music '{path}': {e}")
        return False


def switch_music():
    global current_music_index, music_playing
    if not music_files:
        return
    current_music_index = (current_music_index + 1) % len(music_files)
    if load_music(current_music_index):
        print(f"Switched to: {music_files[current_music_index]}")
    else:
        print("Music switch failed")


def init_music():
    global music_files, current_music_index
    music_files = scan_music_files()
    if music_files:
        current_music_index = 0
        load_music(0)
    else:
        print("No music available, will play silently")


# ========== 得分与寿命调整 ==========
def adjust_lifespan_by_score(gain, loss):
    global score_gain_count, score_loss_count, current_lifespan_ms
    if gain > 0:
        score_gain_count += gain
        if score_gain_count >= 10:
            times = score_gain_count // 10
            for _ in range(times):
                new_lifespan = current_lifespan_ms - 2000
                if new_lifespan >= MIN_LIFESPAN_MS:
                    current_lifespan_ms = new_lifespan
                else:
                    current_lifespan_ms = MIN_LIFESPAN_MS
            score_gain_count %= 10
    if loss > 0:
        score_loss_count += loss
        if score_loss_count >= 10:
            times = score_loss_count // 10
            for _ in range(times):
                new_lifespan = current_lifespan_ms + 2000
                if new_lifespan <= MAX_LIFESPAN_MS:
                    current_lifespan_ms = new_lifespan
                else:
                    current_lifespan_ms = MAX_LIFESPAN_MS
            score_loss_count %= 10


def spawn_special_fruit(fruits_list):
    for f in fruits_list:
        if f.is_special:
            return
    special = Fruit(current_lifespan_ms, is_special=True)
    fruits_list.append(special)
    print("Special fruit spawned! (Rotating & scaling, random image)")


# ========== 主游戏函数 ==========
def main():
    global SPEED_FACTOR, combo_counter, score, current_lifespan_ms
    global score_gain_count, score_loss_count, fruits

    load_resources()
    init_music()

    speed_slider = Slider(20, SCREEN_HEIGHT - 50, 200, 16, 0.5, 2.5, 1.0, "Speed")
    music_button = Button(SCREEN_WIDTH - 110, 10, 100, 40, "Next", switch_music)

    fruits = []
    swipe_trail = SwipeTrail()
    mouse_down = False
    last_mouse_pos = None
    score = 0
    running = True

    while running:
        # ---------- 绘制背景 ----------
        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill(BLACK)

        # ---------- 关键修改：去掉游戏区域的黑色矩形，让背景完全显示 ----------
        # 原代码中有：
        # game_rect = pygame.Rect(0, GAME_AREA_TOP, SCREEN_WIDTH, GAME_AREA_BOTTOM - GAME_AREA_TOP)
        # pygame.draw.rect(screen, (20, 20, 30), game_rect)
        # 现在已删除，游戏区域不再有半透明黑色背景

        # 保留游戏区域的边界线（底部线条）
        pygame.draw.line(screen, (100, 100, 100), (0, GAME_AREA_BOTTOM), (SCREEN_WIDTH, GAME_AREA_BOTTOM), 2)

        # ---------- 事件处理 ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            speed_slider.handle_event(event)
            music_button.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down = True
                last_mouse_pos = event.pos
                swipe_trail.points = []
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_down = False
                last_mouse_pos = None
            elif event.type == pygame.MOUSEMOTION and mouse_down:
                if last_mouse_pos:
                    swipe_trail.add_point(event.pos)
                    p1 = last_mouse_pos
                    p2 = event.pos
                    for fruit in fruits[:]:
                        if fruit.check_slice(p1, p2):
                            fruit.sliced = True
                            gain = fruit.score_multiplier
                            score += gain
                            adjust_lifespan_by_score(gain=gain, loss=0)

                            if fruit.is_special:
                                combo_counter = 0
                            else:
                                combo_counter += 1
                                if combo_counter >= 3:
                                    spawn_special_fruit(fruits)
                                    combo_counter = 0

                            fruits.remove(fruit)
                            break
                last_mouse_pos = event.pos

        # ---------- 更新 ----------
        SPEED_FACTOR = speed_slider.val
        swipe_trail.update()

        for fruit in fruits[:]:
            if fruit.update(SPEED_FACTOR):
                if not fruit.sliced:
                    score -= 1
                    adjust_lifespan_by_score(gain=0, loss=1)
                    combo_counter = 0
                fruits.remove(fruit)

        if len(fruits) == 0:
            fruits.append(Fruit(current_lifespan_ms, is_special=False))

        # ---------- 绘制水果、刀光等 ----------
        for fruit in fruits:
            fruit.draw(screen)

        swipe_trail.draw(screen)

        # ---------- UI 文字 ----------
        draw_text_with_effect(screen, "Fruit Ninja - Bounce Edition", font, WHITE, BLACK, (80, 80, 80),
                              SCREEN_WIDTH // 2 - font.size("Fruit Ninja - Bounce Edition")[0] // 2, 20)
        draw_text_with_effect(screen, f"Score: {score}", font, YELLOW, BLACK, (80, 80, 80), 20, 65)
        lifespan_sec = current_lifespan_ms // 1000
        draw_text_with_effect(screen, f"Fruit Lifespan: {lifespan_sec}s", small_font, WHITE, BLACK, (80, 80, 80), 20, 100)
        draw_text_with_effect(screen, f"Combo: {combo_counter}", combo_font, ORANGE, BLACK, (80, 80, 80), 20, 130)

        if fruits:
            fruit = fruits[0]
            elapsed = pygame.time.get_ticks() - fruit.birth_time
            remaining = max(0, fruit.lifespan_ms - elapsed) // 1000
            info_text = f"Bounce: {fruit.bounce_count}/{MAX_BOUNCES} Time left: {remaining}s"
            draw_text_with_effect(screen, info_text, small_font, WHITE, BLACK, (80, 80, 80),
                                  SCREEN_WIDTH // 2 - small_font.size(info_text)[0] // 2, GAME_AREA_TOP - 40)

        speed_slider.draw(screen)
        music_button.draw(screen)

        if music_files:
            current_track = music_files[current_music_index]
            draw_text_with_effect(screen, f"Music: {current_track}", small_font, WHITE, BLACK, (80, 80, 80),
                                  SCREEN_WIDTH - 220, 60)
        else:
            draw_text_with_effect(screen, "Music: None", small_font, WHITE, BLACK, (80, 80, 80),
                                  SCREEN_WIDTH - 220, 60)

        hint_text = "Hold and swipe to cut fruits"
        draw_text_with_effect(screen, hint_text, small_font, (200, 200, 200), BLACK, (80, 80, 80),
                              SCREEN_WIDTH // 2 - small_font.size(hint_text)[0] // 2, GAME_AREA_TOP - 20)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

"""

# $$ 透明、随机、转速适中、背景音可选完整版0505
# 注释看前一个版本
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pygame
import random
import math
import os

# 初始化 Pygame
pygame.init()
pygame.mixer.init()

# 屏幕设置
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fruit Ninja - Bounce Edition")
clock = pygame.time.Clock()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GOLD = (255, 215, 0)
COLORS = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE]

# 游戏区域 (上边界提高，为文字留出空间)
GAME_AREA_TOP = 150
GAME_AREA_BOTTOM = SCREEN_HEIGHT - 80

# 物理参数
GRAVITY = 0.3
BASE_FALL_SPEED = 2.0
BOUNCE_DAMP = 0.8
MAX_BOUNCES = 5
BASE_LIFESPAN_MS = 30000
MIN_LIFESPAN_MS = 5000
MAX_LIFESPAN_MS = 60000

# 得分影响寿命的累计计数
score_gain_count = 0
score_loss_count = 0
current_lifespan_ms = BASE_LIFESPAN_MS

# 全局速度因子
SPEED_FACTOR = 1.0

# 连击计数器
combo_counter = 0


# ==================== 资源加载 ====================
FRUIT_IMAGES_FOLDER = "fruits"
SPECIAL_FRUIT_FOLDER = os.path.join(FRUIT_IMAGES_FOLDER, "videos")
BACKGROUND_IMAGE_FOLDER = "background"
BUTTON_IMAGES_FOLDER = "buttons"

fruit_images = []
special_fruit_images = []
background_img = None
button_img_normal = None
button_img_hover = None


def load_image(path, scale_size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale_size:
            img = pygame.transform.scale(img, scale_size)
        return img
    except:
        return None


def load_resources():
    global fruit_images, special_fruit_images, background_img, button_img_normal, button_img_hover

    # 加载普通水果图片
    if os.path.exists(FRUIT_IMAGES_FOLDER):
        for file in os.listdir(FRUIT_IMAGES_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(FRUIT_IMAGES_FOLDER, file)
                if os.path.isdir(full_path):
                    continue
                img = load_image(full_path)
                if img:
                    fruit_images.append(img)
        print(f"Loaded {len(fruit_images)} fruit images")
    else:
        print(f"Folder '{FRUIT_IMAGES_FOLDER}' not found, using circles")

    # 加载特殊水果图片 (fruits/videos/ 下所有图片)
    if os.path.exists(SPECIAL_FRUIT_FOLDER):
        for file in os.listdir(SPECIAL_FRUIT_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = load_image(os.path.join(SPECIAL_FRUIT_FOLDER, file))
                if img:
                    special_fruit_images.append(img)
        if special_fruit_images:
            print(f"Loaded {len(special_fruit_images)} special fruit images from fruits/videos/")
        else:
            print("No valid images in fruits/videos/, using golden circle for special fruit")
    else:
        print(f"Folder '{SPECIAL_FRUIT_FOLDER}' not found, using golden circle for special fruit")

    # 加载背景（优先加载 background/2.jpg）
    if os.path.exists(BACKGROUND_IMAGE_FOLDER):
        bg_path_jpg = os.path.join(BACKGROUND_IMAGE_FOLDER, "2.jpg")
        if os.path.exists(bg_path_jpg):
            background_img = load_image(bg_path_jpg)
            if background_img:
                background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print("Background image loaded: 2.jpg")
        else:
            for file in os.listdir(BACKGROUND_IMAGE_FOLDER):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    background_img = load_image(os.path.join(BACKGROUND_IMAGE_FOLDER, file))
                    if background_img:
                        background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                        print(f"Background image loaded: {file}")
                        break
    else:
        print(f"Folder '{BACKGROUND_IMAGE_FOLDER}' not found, using default background")

    # 加载按钮图片
    if os.path.exists(BUTTON_IMAGES_FOLDER):
        for file in os.listdir(BUTTON_IMAGES_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                button_img_normal = load_image(os.path.join(BUTTON_IMAGES_FOLDER, file))
                if button_img_normal:
                    button_img_normal = pygame.transform.scale(button_img_normal, (100, 40))
                    print("Button image loaded")
                    break
    else:
        print(f"Folder '{BUTTON_IMAGES_FOLDER}' not found, using default button")


# 字体 (安全加载)
try:
    font = pygame.font.SysFont("SimHei", 24)
    small_font = pygame.font.SysFont("SimHei", 18)
    combo_font = pygame.font.SysFont("SimHei", 22)
except:
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    combo_font = pygame.font.Font(None, 22)


# ========== 带阴影和边框的文字绘制函数 ==========
def draw_text_with_effect(surface, text, font, color, outline_color, shadow_color, x, y, shadow_offset=(2, 2)):
    shadow_surf = font.render(text, True, shadow_color)
    surface.blit(shadow_surf, (x + shadow_offset[0], y + shadow_offset[1]))
    text_surf = font.render(text, True, color)
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        outline_surf = font.render(text, True, outline_color)
        surface.blit(outline_surf, (x + dx, y + dy))
    surface.blit(text_surf, (x, y))


# ========== 速度滑块 ==========
class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min = min_val
        self.max = max_val
        self.val = initial_val
        self.handle_radius = h // 2
        self.handle_x = self.rect.x + int((initial_val - min_val) / (max_val - min_val) * w)
        self.dragging = False
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_handle(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_handle(event.pos[0])

    def update_handle(self, mouse_x):
        self.handle_x = max(self.rect.left, min(mouse_x, self.rect.right))
        ratio = (self.handle_x - self.rect.left) / self.rect.width
        self.val = self.min + ratio * (self.max - self.min)

    def draw(self, surface):
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=self.rect.height // 2)
        fill_rect = pygame.Rect(self.rect.left, self.rect.top, self.handle_x - self.rect.left, self.rect.height)
        pygame.draw.rect(surface, (0, 150, 200), fill_rect, border_radius=self.rect.height // 2)
        pygame.draw.circle(surface, WHITE, (self.handle_x, self.rect.centery), self.handle_radius)
        pygame.draw.circle(surface, BLACK, (self.handle_x, self.rect.centery), self.handle_radius, 2)
        label_text = f"{self.label}: {self.val:.1f}"
        draw_text_with_effect(surface, label_text, small_font, WHITE, BLACK, (80, 80, 80),
                              self.rect.left, self.rect.top - 20)


# ========== 水果类 ==========
class Fruit:
    def __init__(self, lifespan_ms, is_special=False):
        self.radius = random.randint(20, 40)
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = GAME_AREA_TOP - self.radius
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = BASE_FALL_SPEED * random.uniform(0.8, 1.2)
        self.sliced = False
        self.bounce_count = 0
        self.birth_time = pygame.time.get_ticks()
        self.lifespan_ms = lifespan_ms
        self.is_special = is_special
        self.score_multiplier = 3 if is_special else 1

        if self.is_special:
            self.fall_mode = True
            self.initial_radius = self.radius
            self.scale_factor = 1.0
            self.angle = 0
            self.fall_vy = random.uniform(2.5, 4.5)
            self.fall_vx = random.uniform(-1.0, 1.0)
            self.vx = self.fall_vx
            self.bounce_count = 0
            self.lifespan_ms = 9999999
        else:
            self.fall_mode = False

        if self.is_special and special_fruit_images:
            base_img = random.choice(special_fruit_images)
            self.image = pygame.transform.scale(base_img, (self.radius * 2, self.radius * 2))
            self.use_image = True
        elif fruit_images:
            self.image = random.choice(fruit_images)
            self.image = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
            self.use_image = True
        else:
            self.color = GOLD if self.is_special else random.choice(COLORS)
            self.use_image = False

    def update(self, speed_factor):
        if self.is_special and self.fall_mode:
            self.scale_factor = min(5.0, self.scale_factor + 0.022)
            self.radius = int(self.initial_radius * self.scale_factor)
            self.angle = (self.angle + 2) % 360
            self.x += self.vx * speed_factor
            self.y += self.fall_vy * speed_factor
            if (self.y + self.radius < GAME_AREA_TOP or
                self.y - self.radius > GAME_AREA_BOTTOM or
                self.x + self.radius < 0 or
                self.x - self.radius > SCREEN_WIDTH):
                return True
            return False

        self.vy += GRAVITY * speed_factor
        self.x += self.vx
        self.y += self.vy * speed_factor

        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = -self.vx * BOUNCE_DAMP
            self.bounce_count += 1
        if self.x + self.radius >= SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -self.vx * BOUNCE_DAMP
            self.bounce_count += 1
        if self.y - self.radius <= GAME_AREA_TOP:
            self.y = GAME_AREA_TOP + self.radius
            self.vy = -self.vy * BOUNCE_DAMP
            self.bounce_count += 1
        if self.y + self.radius >= GAME_AREA_BOTTOM:
            self.y = GAME_AREA_BOTTOM - self.radius
            self.vy = -self.vy * BOUNCE_DAMP
            self.bounce_count += 1

        if self.bounce_count >= MAX_BOUNCES:
            return True
        if pygame.time.get_ticks() - self.birth_time >= self.lifespan_ms:
            return True
        return False

    def draw(self, surface):
        if self.is_special and self.fall_mode:
            if self.use_image:
                scaled_img = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
                rotated_img = pygame.transform.rotate(scaled_img, self.angle)
                img_rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(rotated_img, img_rect)
            else:
                pygame.draw.circle(surface, GOLD, (int(self.x), int(self.y)), self.radius)
                highlight_radius = max(2, self.radius // 4)
                pygame.draw.circle(surface, WHITE, (int(self.x - self.radius // 4), int(self.y - self.radius // 4)),
                                   highlight_radius)
            star_text = "★3x★"
            draw_text_with_effect(surface, star_text, small_font, GOLD, BLACK, (80, 80, 80),
                                  self.x - self.radius, self.y + self.radius - 20)
            return

        if self.use_image:
            img_rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.image, img_rect)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            highlight_radius = max(2, self.radius // 4)
            pygame.draw.circle(surface, WHITE, (int(self.x - self.radius // 4), int(self.y - self.radius // 4)),
                               highlight_radius)

        bounce_text = f"Bounce:{self.bounce_count}/{MAX_BOUNCES}"
        draw_text_with_effect(surface, bounce_text, small_font, WHITE, BLACK, (80, 80, 80),
                              self.x - self.radius, self.y - self.radius - 10)

        if self.is_special:
            star_text = "★3x★"
            draw_text_with_effect(surface, star_text, small_font, GOLD, BLACK, (80, 80, 80),
                                  self.x - self.radius, self.y + self.radius - 20)

    def check_slice(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        cx, cy = self.x, self.y
        r = self.radius
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(cx - x1, cy - y1) <= r
        t = ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        nearest_x = x1 + t * dx
        nearest_y = y1 + t * dy
        dist = math.hypot(cx - nearest_x, cy - nearest_y)
        return dist <= r


# ========== 刀光效果 ==========
class SwipeTrail:
    def __init__(self):
        self.points = []
        self.max_len = 8
        self.life = 15

    def add_point(self, pos):
        self.points.append((pos[0], pos[1], self.life))
        if len(self.points) > self.max_len:
            self.points.pop(0)

    def update(self):
        for i in range(len(self.points)):
            x, y, life = self.points[i]
            life -= 1
            self.points[i] = (x, y, life)
        self.points = [p for p in self.points if p[2] > 0]

    def draw(self, surface):
        if len(self.points) < 2:
            return
        for i in range(len(self.points) - 1):
            x1, y1, life1 = self.points[i]
            x2, y2, life2 = self.points[i + 1]
            pygame.draw.line(surface, (200, 200, 200), (x1, y1), (x2, y2), max(2, int(5 * life1 / self.life)))


# ========== 按钮类 ==========
class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.use_image = button_img_normal is not None
        if self.use_image:
            self.img_normal = pygame.transform.scale(button_img_normal, (w, h))
            self.img_hover = self.img_normal.copy()
            self.img_hover.fill((50, 50, 50, 0), special_flags=pygame.BLEND_RGB_ADD)
        else:
            self.color = (50, 50, 150)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse_pos)
        if self.use_image:
            img = self.img_hover if hover else self.img_normal
            surface.blit(img, self.rect)
        else:
            color = (100, 100, 200) if hover else self.color
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
            draw_text_with_effect(surface, self.text, small_font, WHITE, BLACK, (80, 80, 80),
                                  self.rect.x + self.rect.width // 2 - small_font.size(self.text)[0] // 2,
                                  self.rect.y + self.rect.height // 2 - small_font.get_height() // 2)


# 音乐相关
MUSIC_FOLDER = "music"
music_files = ["1.mp3", "2.mp3", "3.mp3", "4.mp3", "5.mp3"]
current_music_index = 0
music_playing = True


def load_music(index):
    global music_playing
    try:
        path = os.path.join(MUSIC_FOLDER, music_files[index])
        pygame.mixer.music.load(path)
        if music_playing:
            pygame.mixer.music.play(-1)
        return True
    except:
        print(f"Cannot load music: {path}")
        return False


def switch_music():
    global current_music_index, music_playing
    current_music_index = (current_music_index + 1) % len(music_files)
    if load_music(current_music_index):
        print(f"Switched to: {music_files[current_music_index]}")
    else:
        print("Music switch failed")


# ========== 得分与寿命调整 ==========
def adjust_lifespan_by_score(gain, loss):
    global score_gain_count, score_loss_count, current_lifespan_ms
    if gain > 0:
        score_gain_count += gain
        if score_gain_count >= 10:
            times = score_gain_count // 10
            for _ in range(times):
                new_lifespan = current_lifespan_ms - 2000
                if new_lifespan >= MIN_LIFESPAN_MS:
                    current_lifespan_ms = new_lifespan
                else:
                    current_lifespan_ms = MIN_LIFESPAN_MS
            score_gain_count %= 10
    if loss > 0:
        score_loss_count += loss
        if score_loss_count >= 10:
            times = score_loss_count // 10
            for _ in range(times):
                new_lifespan = current_lifespan_ms + 2000
                if new_lifespan <= MAX_LIFESPAN_MS:
                    current_lifespan_ms = new_lifespan
                else:
                    current_lifespan_ms = MAX_LIFESPAN_MS
            score_loss_count %= 10


# 生成特殊水果
def spawn_special_fruit(fruits_list):
    for f in fruits_list:
        if f.is_special:
            return
    special = Fruit(current_lifespan_ms, is_special=True)
    fruits_list.append(special)
    print("Special fruit spawned! (Rotating & scaling, random image)")


# ========== 主游戏函数 ==========
def main():
    global SPEED_FACTOR, combo_counter, score, current_lifespan_ms
    global score_gain_count, score_loss_count, fruits

    load_resources()

    speed_slider = Slider(20, SCREEN_HEIGHT - 50, 200, 16, 0.5, 2.5, 1.0, "Speed")
    music_button = Button(SCREEN_WIDTH - 110, 10, 100, 40, "Next", switch_music)

    fruits = []
    swipe_trail = SwipeTrail()
    mouse_down = False
    last_mouse_pos = None
    score = 0
    running = True

    while running:
        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill(BLACK)
            game_rect = pygame.Rect(0, GAME_AREA_TOP, SCREEN_WIDTH, GAME_AREA_BOTTOM - GAME_AREA_TOP)
            pygame.draw.rect(screen, (20, 20, 30), game_rect)

        pygame.draw.line(screen, (100, 100, 100), (0, GAME_AREA_BOTTOM), (SCREEN_WIDTH, GAME_AREA_BOTTOM), 2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            speed_slider.handle_event(event)
            music_button.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down = True
                last_mouse_pos = event.pos
                swipe_trail.points = []
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_down = False
                last_mouse_pos = None
            elif event.type == pygame.MOUSEMOTION and mouse_down:
                if last_mouse_pos:
                    swipe_trail.add_point(event.pos)
                    p1 = last_mouse_pos
                    p2 = event.pos
                    for fruit in fruits[:]:
                        if fruit.check_slice(p1, p2):
                            fruit.sliced = True
                            gain = fruit.score_multiplier
                            score += gain
                            adjust_lifespan_by_score(gain=gain, loss=0)

                            if fruit.is_special:
                                combo_counter = 0
                            else:
                                combo_counter += 1
                                if combo_counter >= 3:
                                    spawn_special_fruit(fruits)
                                    combo_counter = 0

                            fruits.remove(fruit)
                            break
                last_mouse_pos = event.pos

        SPEED_FACTOR = speed_slider.val
        swipe_trail.update()

        for fruit in fruits[:]:
            if fruit.update(SPEED_FACTOR):
                if not fruit.sliced:
                    score -= 1
                    adjust_lifespan_by_score(gain=0, loss=1)
                    combo_counter = 0
                fruits.remove(fruit)

        if len(fruits) == 0:
            fruits.append(Fruit(current_lifespan_ms, is_special=False))

        for fruit in fruits:
            fruit.draw(screen)

        swipe_trail.draw(screen)

        # UI 文字
        draw_text_with_effect(screen, "Fruit Ninja - Bounce Edition", font, WHITE, BLACK, (80, 80, 80),
                              SCREEN_WIDTH // 2 - font.size("Fruit Ninja - Bounce Edition")[0] // 2, 20)
        draw_text_with_effect(screen, f"Score: {score}", font, YELLOW, BLACK, (80, 80, 80), 20, 65)
        lifespan_sec = current_lifespan_ms // 1000
        draw_text_with_effect(screen, f"Fruit Lifespan: {lifespan_sec}s", small_font, WHITE, BLACK, (80, 80, 80), 20, 100)
        draw_text_with_effect(screen, f"Combo: {combo_counter}", combo_font, ORANGE, BLACK, (80, 80, 80), 20, 130)

        if fruits:
            fruit = fruits[0]
            elapsed = pygame.time.get_ticks() - fruit.birth_time
            remaining = max(0, fruit.lifespan_ms - elapsed) // 1000
            info_text = f"Bounce: {fruit.bounce_count}/{MAX_BOUNCES} Time left: {remaining}s"
            draw_text_with_effect(screen, info_text, small_font, WHITE, BLACK, (80, 80, 80),
                                  SCREEN_WIDTH // 2 - small_font.size(info_text)[0] // 2, GAME_AREA_TOP - 40)

        speed_slider.draw(screen)
        music_button.draw(screen)
        draw_text_with_effect(screen, f"Music: {music_files[current_music_index]}", small_font, WHITE, BLACK, (80, 80, 80),
                              SCREEN_WIDTH - 220, 60)

        hint_text = "Hold and swipe to cut fruits"
        draw_text_with_effect(screen, hint_text, small_font, (200, 200, 200), BLACK, (80, 80, 80),
                              SCREEN_WIDTH // 2 - small_font.size(hint_text)[0] // 2, GAME_AREA_TOP - 20)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()



# $$透明、随机、旋转速度适中，没有合适背景音0505 但是运行关闭后会自动再次运行
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pygame
import random
import math
import os

# 初始化 Pygame
pygame.init()
pygame.mixer.init()

# 屏幕设置
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fruit Ninja - Bounce Edition")
clock = pygame.time.Clock()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GOLD = (255, 215, 0)
COLORS = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE]

# 游戏区域 (上边界提高，为文字留出空间)
GAME_AREA_TOP = 150
GAME_AREA_BOTTOM = SCREEN_HEIGHT - 80

# 物理参数
GRAVITY = 0.3
BASE_FALL_SPEED = 2.0
BOUNCE_DAMP = 0.8
MAX_BOUNCES = 5
BASE_LIFESPAN_MS = 30000
MIN_LIFESPAN_MS = 5000
MAX_LIFESPAN_MS = 60000

# 得分影响寿命的累计计数
score_gain_count = 0
score_loss_count = 0
current_lifespan_ms = BASE_LIFESPAN_MS

# 全局速度因子
SPEED_FACTOR = 1.0

# 连击计数器
combo_counter = 0


# ==================== 资源加载 ====================
FRUIT_IMAGES_FOLDER = "fruits"
SPECIAL_FRUIT_FOLDER = os.path.join(FRUIT_IMAGES_FOLDER, "videos")  # 特殊水果存放路径
BACKGROUND_IMAGE_FOLDER = "background"
BUTTON_IMAGES_FOLDER = "buttons"

fruit_images = []
special_fruit_images = []      # 改为列表，存储所有特殊水果图片
background_img = None
button_img_normal = None
button_img_hover = None


def load_image(path, scale_size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale_size:
            img = pygame.transform.scale(img, scale_size)
        return img
    except:
        return None


def load_resources():
    global fruit_images, special_fruit_images, background_img, button_img_normal, button_img_hover

    # 加载普通水果图片
    if os.path.exists(FRUIT_IMAGES_FOLDER):
        for file in os.listdir(FRUIT_IMAGES_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                # 跳过 videos 子文件夹，避免当作普通水果加载
                full_path = os.path.join(FRUIT_IMAGES_FOLDER, file)
                if os.path.isdir(full_path):
                    continue
                img = load_image(full_path)
                if img:
                    fruit_images.append(img)
        print(f"Loaded {len(fruit_images)} fruit images")
    else:
        print(f"Folder '{FRUIT_IMAGES_FOLDER}' not found, using circles")

    # 加载特殊水果图片 (fruits/videos/ 下所有图片)
    if os.path.exists(SPECIAL_FRUIT_FOLDER):
        for file in os.listdir(SPECIAL_FRUIT_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = load_image(os.path.join(SPECIAL_FRUIT_FOLDER, file))
                if img:
                    special_fruit_images.append(img)
        if special_fruit_images:
            print(f"Loaded {len(special_fruit_images)} special fruit images from fruits/videos/")
        else:
            print("No valid images in fruits/videos/, using golden circle for special fruit")
    else:
        print(f"Folder '{SPECIAL_FRUIT_FOLDER}' not found, using golden circle for special fruit")

    # 加载背景（优先加载 background/2.jpg）
    if os.path.exists(BACKGROUND_IMAGE_FOLDER):
        # 优先尝试加载 2.jpg
        bg_path_jpg = os.path.join(BACKGROUND_IMAGE_FOLDER, "2.jpg")
        if os.path.exists(bg_path_jpg):
            background_img = load_image(bg_path_jpg)
            if background_img:
                background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print("Background image loaded: 2.jpg")
        else:
            # 若没有2.jpg，则加载任意一张图片
            for file in os.listdir(BACKGROUND_IMAGE_FOLDER):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    background_img = load_image(os.path.join(BACKGROUND_IMAGE_FOLDER, file))
                    if background_img:
                        background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                        print(f"Background image loaded: {file}")
                        break
    else:
        print(f"Folder '{BACKGROUND_IMAGE_FOLDER}' not found, using default background")

    # 加载按钮图片
    if os.path.exists(BUTTON_IMAGES_FOLDER):
        for file in os.listdir(BUTTON_IMAGES_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                button_img_normal = load_image(os.path.join(BUTTON_IMAGES_FOLDER, file))
                if button_img_normal:
                    button_img_normal = pygame.transform.scale(button_img_normal, (100, 40))
                    print("Button image loaded")
                    break
    else:
        print(f"Folder '{BUTTON_IMAGES_FOLDER}' not found, using default button")


load_resources()

# 字体 (安全加载)
try:
    font = pygame.font.SysFont("SimHei", 24)
    small_font = pygame.font.SysFont("SimHei", 18)
    combo_font = pygame.font.SysFont("SimHei", 22)
except:
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    combo_font = pygame.font.Font(None, 22)


# ========== 带阴影和边框的文字绘制函数 ==========
def draw_text_with_effect(surface, text, font, color, outline_color, shadow_color, x, y, shadow_offset=(2, 2)):
    # 绘制带边框和阴影的文字
    # 先绘制阴影
    shadow_surf = font.render(text, True, shadow_color)
    surface.blit(shadow_surf, (x + shadow_offset[0], y + shadow_offset[1]))
    # 再绘制边框（通过多次位移模拟）
    text_surf = font.render(text, True, color)
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        outline_surf = font.render(text, True, outline_color)
        surface.blit(outline_surf, (x + dx, y + dy))
    # 最后绘制本身
    surface.blit(text_surf, (x, y))


# ========== 速度滑块 ==========
class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min = min_val
        self.max = max_val
        self.val = initial_val
        self.handle_radius = h // 2
        self.handle_x = self.rect.x + int((initial_val - min_val) / (max_val - min_val) * w)
        self.dragging = False
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_handle(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_handle(event.pos[0])

    def update_handle(self, mouse_x):
        self.handle_x = max(self.rect.left, min(mouse_x, self.rect.right))
        ratio = (self.handle_x - self.rect.left) / self.rect.width
        self.val = self.min + ratio * (self.max - self.min)

    def draw(self, surface):
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=self.rect.height // 2)
        fill_rect = pygame.Rect(self.rect.left, self.rect.top, self.handle_x - self.rect.left, self.rect.height)
        pygame.draw.rect(surface, (0, 150, 200), fill_rect, border_radius=self.rect.height // 2)
        pygame.draw.circle(surface, WHITE, (self.handle_x, self.rect.centery), self.handle_radius)
        pygame.draw.circle(surface, BLACK, (self.handle_x, self.rect.centery), self.handle_radius, 2)
        # 滑块标签使用特效文字
        label_text = f"{self.label}: {self.val:.1f}"
        draw_text_with_effect(surface, label_text, small_font, WHITE, BLACK, (80, 80, 80),
                              self.rect.left, self.rect.top - 20)


speed_slider = Slider(20, SCREEN_HEIGHT - 50, 200, 16, 0.5, 2.5, 1.0, "Speed")


# ========== 水果类 ==========
class Fruit:
    def __init__(self, lifespan_ms, is_special=False):
        self.radius = random.randint(20, 40)
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = GAME_AREA_TOP - self.radius
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = BASE_FALL_SPEED * random.uniform(0.8, 1.2)
        self.sliced = False
        self.bounce_count = 0
        self.birth_time = pygame.time.get_ticks()
        self.lifespan_ms = lifespan_ms
        self.is_special = is_special
        self.score_multiplier = 3 if is_special else 1

        # 特殊水果特有属性：旋转、缩放、自由下落
        if self.is_special:
            self.fall_mode = True           # 启用特殊掉落模式
            self.initial_radius = self.radius
            self.scale_factor = 1.0
            self.angle = 0
            self.fall_vy = random.uniform(2.5, 4.5)   # 固定下落速度
            self.fall_vx = random.uniform(-1.0, 1.0)   # 水平飘移
            self.vx = self.fall_vx
            # 禁用原有的寿命和弹跳逻辑
            self.bounce_count = 0
            self.lifespan_ms = 9999999      # 很大，不会因时间消失
        else:
            self.fall_mode = False

        # 加载图片
        if self.is_special and special_fruit_images:
            # 随机选择一张特殊水果图片
            base_img = random.choice(special_fruit_images)
            self.image = pygame.transform.scale(base_img, (self.radius * 2, self.radius * 2))
            self.use_image = True
        elif fruit_images:
            self.image = random.choice(fruit_images)
            self.image = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
            self.use_image = True
        else:
            self.color = GOLD if self.is_special else random.choice(COLORS)
            self.use_image = False

    def update(self, speed_factor):
        # 特殊水果：旋转掉落 + 缩放变大
        if self.is_special and self.fall_mode:
            # 缩放因子逐渐增加，最大5倍
            self.scale_factor = min(5.0, self.scale_factor + 0.022)
            self.radius = int(self.initial_radius * self.scale_factor)
            # 旋转角度递增，每帧增加6度 → 每秒旋转一周（60帧 * 6° = 360°）
            self.angle = (self.angle + 6) % 360
            # 水平飘移与固定下落
            self.x += self.vx * speed_factor
            self.y += self.fall_vy * speed_factor
            # 超出游戏区域（上、下、左、右）则消失
            if (self.y + self.radius < GAME_AREA_TOP or
                self.y - self.radius > GAME_AREA_BOTTOM or
                self.x + self.radius < 0 or
                self.x - self.radius > SCREEN_WIDTH):
                return True
            return False

        # 普通水果：原有物理逻辑
        self.vy += GRAVITY * speed_factor
        self.x += self.vx
        self.y += self.vy * speed_factor

        # 边界反弹
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = -self.vx * BOUNCE_DAMP
            self.bounce_count += 1
        if self.x + self.radius >= SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -self.vx * BOUNCE_DAMP
            self.bounce_count += 1
        if self.y - self.radius <= GAME_AREA_TOP:
            self.y = GAME_AREA_TOP + self.radius
            self.vy = -self.vy * BOUNCE_DAMP
            self.bounce_count += 1
        if self.y + self.radius >= GAME_AREA_BOTTOM:
            self.y = GAME_AREA_BOTTOM - self.radius
            self.vy = -self.vy * BOUNCE_DAMP
            self.bounce_count += 1

        # 消失条件
        if self.bounce_count >= MAX_BOUNCES:
            return True
        if pygame.time.get_ticks() - self.birth_time >= self.lifespan_ms:
            return True
        return False

    def draw(self, surface):
        # 特殊水果：旋转+缩放绘制
        if self.is_special and self.fall_mode:
            if self.use_image:
                # 每帧重新缩放图片（因为半径在变化）
                scaled_img = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
                rotated_img = pygame.transform.rotate(scaled_img, self.angle)
                img_rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(rotated_img, img_rect)
            else:
                # 如果没有图片，绘制金色圆，并随半径增大
                pygame.draw.circle(surface, GOLD, (int(self.x), int(self.y)), self.radius)
                highlight_radius = max(2, self.radius // 4)
                pygame.draw.circle(surface, WHITE, (int(self.x - self.radius // 4), int(self.y - self.radius // 4)),
                                   highlight_radius)
            # 特殊水果标记 ★3x★
            star_text = "★3x★"
            draw_text_with_effect(surface, star_text, small_font, GOLD, BLACK, (80, 80, 80),
                                  self.x - self.radius, self.y + self.radius - 20)
            return

        # 普通水果：原有绘制
        if self.use_image:
            img_rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.image, img_rect)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            highlight_radius = max(2, self.radius // 4)
            pygame.draw.circle(surface, WHITE, (int(self.x - self.radius // 4), int(self.y - self.radius // 4)),
                               highlight_radius)

        # 弹跳次数文字
        bounce_text = f"Bounce:{self.bounce_count}/{MAX_BOUNCES}"
        draw_text_with_effect(surface, bounce_text, small_font, WHITE, BLACK, (80, 80, 80),
                              self.x - self.radius, self.y - self.radius - 10)

        # 特殊水果标记（仅在非掉落模式下保留，但特殊水果走上面分支了，这里不会执行到）
        if self.is_special:
            star_text = "★3x★"
            draw_text_with_effect(surface, star_text, small_font, GOLD, BLACK, (80, 80, 80),
                                  self.x - self.radius, self.y + self.radius - 20)

    def check_slice(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        cx, cy = self.x, self.y
        r = self.radius
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(cx - x1, cy - y1) <= r
        t = ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        nearest_x = x1 + t * dx
        nearest_y = y1 + t * dy
        dist = math.hypot(cx - nearest_x, cy - nearest_y)
        return dist <= r


# ========== 刀光效果 ==========
class SwipeTrail:
    def __init__(self):
        self.points = []
        self.max_len = 8
        self.life = 15

    def add_point(self, pos):
        self.points.append((pos[0], pos[1], self.life))
        if len(self.points) > self.max_len:
            self.points.pop(0)

    def update(self):
        for i in range(len(self.points)):
            x, y, life = self.points[i]
            life -= 1
            self.points[i] = (x, y, life)
        self.points = [p for p in self.points if p[2] > 0]

    def draw(self, surface):
        if len(self.points) < 2:
            return
        for i in range(len(self.points) - 1):
            x1, y1, life1 = self.points[i]
            x2, y2, life2 = self.points[i + 1]
            pygame.draw.line(surface, (200, 200, 200), (x1, y1), (x2, y2), max(2, int(5 * life1 / self.life)))


# ========== 按钮类 ==========
class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.use_image = button_img_normal is not None
        if self.use_image:
            self.img_normal = pygame.transform.scale(button_img_normal, (w, h))
            self.img_hover = self.img_normal.copy()
            self.img_hover.fill((50, 50, 50, 0), special_flags=pygame.BLEND_RGB_ADD)
        else:
            self.color = (50, 50, 150)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse_pos)
        if self.use_image:
            img = self.img_hover if hover else self.img_normal
            surface.blit(img, self.rect)
        else:
            color = (100, 100, 200) if hover else self.color
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
            draw_text_with_effect(surface, self.text, small_font, WHITE, BLACK, (80, 80, 80),
                                  self.rect.x + self.rect.width // 2 - small_font.size(self.text)[0] // 2,
                                  self.rect.y + self.rect.height // 2 - small_font.get_height() // 2)


# 音乐相关
MUSIC_FOLDER = "music"
music_files = ["1.mp3", "2.mp3", "3.mp3", "4.mp3", "5.mp3"]
current_music_index = 0
music_playing = True


def load_music(index):
    global music_playing
    try:
        path = os.path.join(MUSIC_FOLDER, music_files[index])
        pygame.mixer.music.load(path)
        if music_playing:
            pygame.mixer.music.play(-1)
        return True
    except:
        print(f"Cannot load music: {path}")
        return False


if os.path.exists(MUSIC_FOLDER):
    load_music(current_music_index)
else:
    print(f"Music folder '{MUSIC_FOLDER}' not found, music disabled.")


def switch_music():
    global current_music_index, music_playing
    current_music_index = (current_music_index + 1) % len(music_files)
    if load_music(current_music_index):
        print(f"Switched to: {music_files[current_music_index]}")
    else:
        print("Music switch failed")


music_button = Button(SCREEN_WIDTH - 110, 10, 100, 40, "Next", switch_music)


# ========== 得分与寿命调整 ==========
def adjust_lifespan_by_score(gain, loss):
    global score_gain_count, score_loss_count, current_lifespan_ms
    if gain > 0:
        score_gain_count += gain
        if score_gain_count >= 10:
            times = score_gain_count // 10
            for _ in range(times):
                new_lifespan = current_lifespan_ms - 2000
                if new_lifespan >= MIN_LIFESPAN_MS:
                    current_lifespan_ms = new_lifespan
                else:
                    current_lifespan_ms = MIN_LIFESPAN_MS
            score_gain_count %= 10
    if loss > 0:
        score_loss_count += loss
        if score_loss_count >= 10:
            times = score_loss_count // 10
            for _ in range(times):
                new_lifespan = current_lifespan_ms + 2000
                if new_lifespan <= MAX_LIFESPAN_MS:
                    current_lifespan_ms = new_lifespan
                else:
                    current_lifespan_ms = MAX_LIFESPAN_MS
            score_loss_count %= 10


# 生成特殊水果（连续切3个普通水果后触发）
def spawn_special_fruit():
    # 避免同时存在多个特殊水果
    for f in fruits:
        if f.is_special:
            return
    special = Fruit(current_lifespan_ms, is_special=True)
    fruits.append(special)
    print("Special fruit spawned! (Rotating & scaling, random image)")


# ========== 主游戏循环 ==========
fruits = []
swipe_trail = SwipeTrail()
mouse_down = False
last_mouse_pos = None
score = 0
running = True

while running:
    if background_img:
        screen.blit(background_img, (0, 0))
    else:
        screen.fill(BLACK)
        # 如果无背景图，绘制半透明游戏区（避免全黑）
        game_rect = pygame.Rect(0, GAME_AREA_TOP, SCREEN_WIDTH, GAME_AREA_BOTTOM - GAME_AREA_TOP)
        pygame.draw.rect(screen, (20, 20, 30), game_rect)

    pygame.draw.line(screen, (100, 100, 100), (0, GAME_AREA_BOTTOM), (SCREEN_WIDTH, GAME_AREA_BOTTOM), 2)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        speed_slider.handle_event(event)
        music_button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_down = True
            last_mouse_pos = event.pos
            swipe_trail.points = []
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mouse_down = False
            last_mouse_pos = None
        elif event.type == pygame.MOUSEMOTION and mouse_down:
            if last_mouse_pos:
                swipe_trail.add_point(event.pos)
                p1 = last_mouse_pos
                p2 = event.pos
                for fruit in fruits[:]:
                    if fruit.check_slice(p1, p2):
                        fruit.sliced = True
                        # 增加得分（注意特殊水果三倍）
                        gain = fruit.score_multiplier
                        score += gain
                        adjust_lifespan_by_score(gain=gain, loss=0)

                        # 处理连击逻辑
                        if fruit.is_special:
                            # 切中特殊水果，重置连击
                            combo_counter = 0
                        else:
                            # 切中普通水果，连击+1
                            combo_counter += 1
                            if combo_counter >= 3:
                                spawn_special_fruit()
                                combo_counter = 0

                        fruits.remove(fruit)
                        break
            last_mouse_pos = event.pos

    SPEED_FACTOR = speed_slider.val
    swipe_trail.update()

    # 更新水果并检查消失
    for fruit in fruits[:]:
        if fruit.update(SPEED_FACTOR):
            if not fruit.sliced:
                # 水果自然消失，扣分并重置连击
                score -= 1
                adjust_lifespan_by_score(gain=0, loss=1)
                combo_counter = 0
            fruits.remove(fruit)

    # 保证至少有一个普通水果（如果没有水果，生成一个普通水果）
    if len(fruits) == 0:
        fruits.append(Fruit(current_lifespan_ms, is_special=False))

    # 绘制所有水果
    for fruit in fruits:
        fruit.draw(screen)

    swipe_trail.draw(screen)

    # === UI 文字绘制（使用特效文字避免重叠）===
    # 标题
    draw_text_with_effect(screen, "Fruit Ninja - Bounce Edition", font, WHITE, BLACK, (80, 80, 80),
                          SCREEN_WIDTH // 2 - font.size("Fruit Ninja - Bounce Edition")[0] // 2, 20)
    # 得分
    draw_text_with_effect(screen, f"Score: {score}", font, YELLOW, BLACK, (80, 80, 80), 20, 65)
    # 寿命
    lifespan_sec = current_lifespan_ms // 1000
    draw_text_with_effect(screen, f"Fruit Lifespan: {lifespan_sec}s", small_font, WHITE, BLACK, (80, 80, 80), 20, 100)
    # 连击数
    draw_text_with_effect(screen, f"Combo: {combo_counter}", combo_font, ORANGE, BLACK, (80, 80, 80), 20, 130)

    # 当前水果信息（弹跳剩余时间等）
    if fruits:
        fruit = fruits[0]
        elapsed = pygame.time.get_ticks() - fruit.birth_time
        remaining = max(0, fruit.lifespan_ms - elapsed) // 1000
        info_text = f"Bounce: {fruit.bounce_count}/{MAX_BOUNCES} Time left: {remaining}s"
        draw_text_with_effect(screen, info_text, small_font, WHITE, BLACK, (80, 80, 80),
                              SCREEN_WIDTH // 2 - small_font.size(info_text)[0] // 2, GAME_AREA_TOP - 40)

    speed_slider.draw(screen)
    music_button.draw(screen)
    draw_text_with_effect(screen, f"Music: {music_files[current_music_index]}", small_font, WHITE, BLACK, (80, 80, 80),
                          SCREEN_WIDTH - 220, 60)

    hint_text = "Hold and swipe to cut fruits"
    draw_text_with_effect(screen, hint_text, small_font, (200, 200, 200), BLACK, (80, 80, 80),
                          SCREEN_WIDTH // 2 - small_font.size(hint_text)[0] // 2, GAME_AREA_TOP - 20)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
"""
