import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()
pygame.display.set_caption("Platformer")

WIDTH,HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
window = pygame.display.set_mode((WIDTH,HEIGHT))

#角色朝向的变化
def flip(sprites):
    return [pygame.transform.flip(sprite,True,False) for sprite in sprites]

#加载精灵图像表并处理成可用的动画帧
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path,image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width()//width):
            surface = pygame.Surface((width,height),pygame.SRCALPHA,32)
            rect = pygame.Rect(i * width,0,width,height)
            surface.blit(sprite_sheet,(0,0),rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png","") + "_right"] = sprites
            all_sprites[image.replace(".png","") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png","")] = sprites
    return all_sprites

#从精灵图像表中提取指定类型的地块
def get_block(size, block_type):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(block_type * size, 0, size, size)  # 根据 block_type 选择不同的块
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    color = (255,0,0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 5

    def __init__(self,x,y,width,height):
        super().__init__()
        self.start_x = x
        self.start_y = y
        self.rect = pygame.Rect(x,y,width,height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.sprite = None
        # character facing
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.update_sprite()

    def jump(self):
         self.y_vel = -self.GRAVITY * 8
         self.animation_count = 0
         self.jump_count += 1
         if self.jump_count == 1:
             self.fall_count = 0

    def move(self,dx,dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self,vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0
    def move_right(self,vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self,fps):
        self.y_vel += min(1,(self.fall_count/fps)*self.GRAVITY)
        self.move(self.x_vel,self.y_vel)
        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        if self.sprite is not None:  # 确保self.sprite已经初始化
            self.rect = self.sprite.get_rect(topleft=(self.rect.x,self.rect.y))
            self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x, offset_y):
        if self.sprite is not None:
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y - offset_y))

    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.x_vel = 0
        self.y_vel = 0
        self.fall_count = 0
        self.jump_count = 0
        self.update_sprite()
        return True  # 返回复活标志

#定义游戏中所有物体的基础属性和方法
class Object(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,name=None):
        super().__init__()
        self.rect = pygame.Rect(x,y,width,height)
        self.image = pygame.Surface((width,height),pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x, offset_y):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))

#继承自Object类，表示游戏中的地块
class Block(Object):
    def __init__(self,x,y,size,block_type):
        super().__init__(x,y,size,size)
        block = get_block(size,block_type)
        self.image.blit(block,(0,0))
        self.mask = pygame.mask.from_surface(self.image)

class Spike(Object):
    ANIMATION_DELAY = 20

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "Spike")
        self.spike = load_sprite_sheets("Traps", "Spike Head", width, height)
        self.image = self.spike["Blink (54x52)"][0]  # 初始图像
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Blink (54x52)"

    def loop(self):
        sprites = self.spike[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    for a in range(WIDTH // width + 1):
        for b in range(HEIGHT // height + 1):
            pos = (a * width, b * height)
            tiles.append(pos)
    return tiles, image

#绘制背景、物体和玩家
def draw(window, background, bg_image,player,objects,offset_x, offset_y):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window,offset_x,offset_y)

    player.draw(window,offset_x, offset_y)
    pygame.display.update()


#检查玩家与物体的水平碰撞
def collide(player,objects,dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player,obj):
            collided_object = obj
            break

    player.move(-dx,0)
    player.update()
    return collided_object

#处理玩家与物体的垂直碰撞
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if isinstance(obj, Spike):
                if player.reset():
                    return True  # 玩家复活，返回标志
            elif dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    return False


#处理玩家移动和碰撞检测
def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    if handle_vertical_collision(player, objects, player.y_vel):
        return True  # 返回复活标志
    return False


def create_map():
    size = 96
    map_data = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
        [1, 1, 2, 0, 0, 3, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1],
        [1, 0, 2, 0, 1, 2, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 2, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 2, 1, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 2, 0, 0, 2, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 0, 0, 0, 2, 1, 13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 13, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 0, 0, 13, 13, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [13, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    blocks = []
    for y, row in enumerate(map_data):
        for x, col in enumerate(row):
            if col == 1:
                blocks.append(Block(x * size, y * size, size, col - 1))
            elif col == 2:
                blocks.append(Block(x * size, y * size, size, col - 1))
            elif col == 13:
                blocks.append(Spike(x * size, y * size, 54, 52))
    return blocks

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Yellow.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    blocks = create_map()
    objects = blocks

    scroll_area_width = 200
    scroll_area_height = 150
    offset_x = 0
    offset_y = 0

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()

        # 检查玩家是否复活，如果复活则重置摄像机
        if handle_move(player, objects):
            offset_x = max(0, player.rect.x - WIDTH // 2)
            offset_y = max(0, player.rect.y - HEIGHT // 2)

        player.loop(FPS)

        for obj in objects:
            if isinstance(obj, Spike):
                obj.loop()

        draw(window, background, bg_image, player, objects, offset_x, offset_y)

        #camera
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or \
           ((player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

        if ((player.rect.bottom - offset_y >= HEIGHT - scroll_area_height) and player.y_vel > 0) or \
           ((player.rect.top - offset_y <= scroll_area_height) and player.y_vel < 0):
            offset_y += player.y_vel

    pygame.quit()
    quit()

if __name__ == "__main__":
    main(window)


