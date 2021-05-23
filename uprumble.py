import pygame
from pygame import mixer
import os
import random
import csv

#initialize pygame and it's mixer component for audio
mixer.init()
pygame.init()

#set screen values and initialize it
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

#set an icon for the program and its caption
pygame.display.set_caption("UP Rumble: Raquel's Revenge")
programIcon = pygame.image.load('icon.png')
pygame.display.set_icon(programIcon)

#setting global variables for the game, capitalized ones are static
clock = pygame.time.Clock()
FPS = 60

GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 4
screen_scroll = 0
bg_scroll = 0
level = 1
agent_loaded = False
choose_agent = False
start_game = False
start_intro = False
next_level = False
active_ultimate = False
AGENT = None

#define player action variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

#load sounds
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_sound = pygame.mixer.Sound('audio/jump.wav')
jump_sound.set_volume(0.5)
shot_sound = pygame.mixer.Sound('audio/shot.wav')
shot_sound.set_volume(0.5)
grenade_sound = pygame.mixer.Sound('audio/grenade.wav')
grenade_sound.set_volume(0.5)

#load images

#buttons
start_img = pygame.image.load('images/buttons/start_btn.png').convert_alpha()
exit_img = pygame.image.load('images/buttons/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('images/buttons/restart_btn.png').convert_alpha()
#background
up_bg_img = pygame.image.load('images/background/up_bg.png')
#characters
alcaraz = pygame.image.load('images/characters/alcaraz.png').convert_alpha()
cristian = pygame.image.load('images/characters/cristian.png').convert_alpha()
del_puerto = pygame.image.load('images/characters/del_Puerto.png').convert_alpha()
elba = pygame.image.load('images/characters/elba.png').convert_alpha()
piña = pygame.image.load('images/characters/piña.png').convert_alpha()
#tiles
img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'images/tile/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE,TILE_SIZE))
	img_list.append(img)
#bullets
bullet_img = pygame.image.load('images/bullet.png').convert_alpha()
raquel_bullet_img = pygame.image.load('images/raquels_bullet.png').convert_alpha()
#grenade
grenade_img = pygame.image.load('images/grenade.png').convert_alpha()
#pick up boxes
health_box_img = pygame.image.load('images/tile/19.png').convert_alpha()

#define colors
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

#define font
font = pygame.font.SysFont('Futura', 30)

#Global functions
def draw_text(text, font, color, x, y):
	#it's used to draw some input text in x y coordinates
	img = font.render(text, True, color)
	screen.blit(img, (x, y))

def draw_cut_scene_text(text, font, size, color, x, y):
	text_surface = font.render(text, True, color)
	text_rect = text_surface.get_rect()
	text_rect.topleft = (x,y)
	screen.blit(text_surface, text_rect)

def black_bg():
	#clears the screen
	screen.fill(BLACK)

def draw_bg():
	#updates the game background
	screen.blit(up_bg_img, ((0, 0)))

def reset_level():
	#clears all groups so they can be loaded again later on, it avoids duplicate of enemies, tiles and even the player.
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	#create empty tile list so it can be reloaded
	data = []
	for row in range(ROWS):
		r = [-1] * COLS
		data.append(r)

	return data

#Classes
class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, grenades):
		pygame.sprite.Sprite.__init__(self)
		#general variables
		self.alive = True
		self.char_type = char_type
		if char_type == 'agents/Alcaraz' or char_type == 'agents/Cristian' or char_type == 'agents/DelPuerto' or char_type == 'agents/Elba' or char_type == 'agents/Piña':
			self.type = 'player'
		else:
			self.type = 'enemy'
		self.speed = speed
		self.can_shoot = True
		self.shoot_cooldown = 0
		self.heal_cooldown = 0
		self.grenades = grenades
		if char_type == 'agents/Raquel':
			if AGENT == 'agents/Alcaraz':
				self.health = 1200
			else:
				self.health = 2000
		else:
			self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.double_jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()
		self.ultimate_ready = False
		self.active_boss = False
		#ai specific variables
		self.move_counter = 0
		self.ai_shoot_cooldown = 0
		if char_type == 'agents/Raquel':
			if AGENT == 'agents/Alcaraz':
				self.vision = pygame.Rect(0, 0, 150, 20)
			else:
				self.vision = pygame.Rect(0, 0, 500, 40)
		else:
			self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0
		#random bools for del puertos's ultimate
		self.raquel_can_ultimate = True
		self.random_taken = False
		self.can_ai = True
		self.raquel_can_shoot = True
		
		#load all images for the players
		animation_types = ['Idle', 'Run', 'Jump', 'Death']
		for animation in animation_types:
			#reset temporary list of images
			temp_list = []
			#count number of files in the folder
			num_of_frames = len(os.listdir(f'images/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'images/{self.char_type}/{animation}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		#get image dimensions
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()

	def update(self):
		self.update_animation()
		self.check_alive()
		#update cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1
		if self.ai_shoot_cooldown > 0:
			self.ai_shoot_cooldown -= 1
		if self.heal_cooldown > 0:
			self.heal_cooldown -= 1

	def move(self, moving_left, moving_right):
		#reset movement variables
		screen_scroll = 0
		dx = 0
		dy = 0

		#assign movement variables if moving left or right
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1

		#jump
		if self.jump == True and self.in_air == False:
			self.vel_y = -11
			self.jump = False
			self.in_air = True

		#apply gravity
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y
		dy += self.vel_y

		#check for collision
		for tile in world.obstacle_list:
			#check collision in the x direction
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
				#if the ai has hit a wall then make it turn around
				if self.type == 'enemy':
					self.direction *= -1
					self.move_counter = 0
			#check for collision in the y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#check if below the ground, i.e. jumping
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom


		#check for collision with water
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health = 0

		#check for collision with exit
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True

		#check if fallen off the map
		if self.rect.bottom > SCREEN_HEIGHT:
			self.health = 0


		#check if going off the edges of the screen
		if self.type == 'player':
			if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
				dx = 0

		#update rectangle position
		self.rect.x += dx
		self.rect.y += dy

		#update scroll based on player position
		if self.type == 'player':
			if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
				or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
				self.rect.x -= dx
				screen_scroll = -dx

		return screen_scroll, level_complete

	def shoot(self):
		if self.shoot_cooldown == 0 and self.can_shoot:
			if AGENT == 'agents/Cristian' and self.type != 'enemy' and active_ultimate:
				self.shoot_cooldown = 5
			else:
				self.shoot_cooldown = 20

			if self.char_type == 'agents/Raquel':
				bullet = RaquelsBullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			else:	
				bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			shot_sound.play()

	def ai(self):
		if self.alive and player.alive and player.can_ai:
			#if self.rect.colliderect(player.rect):
			#	player.health -= .01

			if self.idling == False and random.randint(1, 200) == 1:
				self.update_action(0)#0: idle
				self.idling = True
				if self.char_type == 'agents/Raquel':
					self.idling_counter = 5
				else:
					self.idling_counter = 50
			#check if the ai is watching the player
			if self.vision.colliderect(player.rect) and self.ai_shoot_cooldown == 0:
				#stop running and face the player
				self.update_action(0)
				if self.char_type == 'agents/Raquel' and player.raquel_can_shoot:
					self.shoot()
				elif self.char_type == 'enemy' :
					self.shoot()
				self.ai_shoot_cooldown = 25
			else:
				if self.idling == False:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False
					ai_moving_left = not ai_moving_right
					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)#1: run
					self.move_counter += 1
					#update ai vision as the enemy moves
					if self.char_type == 'agents/Raquel':
						if self.char_type == 'agents/Alcaraz':
							self.vision.center = (self.rect.centerx + 115 * self.direction, self.rect.centery)
						else:
							self.vision.center = (self.rect.centerx + 285 * self.direction, self.rect.centery)
					else:
						self.vision.center = (self.rect.centerx + 115 * self.direction, self.rect.centery)

					if self.move_counter > TILE_SIZE:
						self.direction *= -1
						self.move_counter *= -1
				else:
					self.idling_counter -= 1
					if self.idling_counter <= 0:
						self.idling = False

		#scroll
		self.rect.x += screen_scroll

	def update_animation(self):
		#update animation
		ANIMATION_COOLDOWN = 100
		#update image depending on current frame
		self.image = self.animation_list[self.action][self.frame_index]
		#check if enough time has passed since the last update
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		#if the animation has run out the reset back to the start
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0

	def update_action(self, new_action):
		#check if the new action is different to the previous one
		if new_action != self.action:
			self.action = new_action
			#update the animation settings
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()

	def check_alive(self):
		if self.health <= 0:
			self.can_shoot = False
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)

	def piña_ultimate(self):
		if AGENT == 'agents/Piña' and self.type != 'enemy' and active_ultimate:
			if self.health < 100 and self.heal_cooldown == 0:
				self.health += 1
				self.heal_cooldown = 25

	def delPuerto_ultimate(self, enemy):
		if AGENT == 'agents/DelPuerto' and self.type != 'enemy' and self.random_taken == False and self.active_boss:
			if enemy.char_type == 'agents/Raquel':
				decision = random.randint(1, 100)
				self.random_taken = True
				if decision == 1:
					enemy.alive = False
					enemy.update_action(3)
				elif decision == 2:
					player.can_ai = False
				elif decision == 3:
					player.raquel_can_shoot = False
				else:
					self.raquel_can_ultimate = False

	def elba_ultimate(self):
		if AGENT == 'agents/Elba':
			player.grenades = 7

	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

	def win(self, enemy):
		if enemy.char_type == 'agents/Raquel':
			if enemy.health <= 0:
				cut_scene_manager.start_cut_scene(VictoryCutScene())

class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])
		#iterate through each value in level data file
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect)
					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)
					elif tile >= 9 and tile <= 10:
						water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
						water_group.add(water)
					elif tile >= 11 and tile <= 14:
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						decoration_group.add(decoration)
					elif tile == 15:#create player
						if AGENT == None:
							player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 0)
						else:
							player = Soldier(AGENT, x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 0)
						health_bar = HealthBar(10, 10, player.health, player.health)
					elif tile == 16:#create enemies
						enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 0)
						enemy_group.add(enemy)
					elif tile == 17:#generate raquel
						if AGENT == 'agents/Alcaraz':
							raquel = Soldier('agents/Raquel',x * TILE_SIZE, y * TILE_SIZE, 1.65, 3,0)
						else:
							raquel = Soldier('agents/Raquel',x * TILE_SIZE, y * TILE_SIZE, 2.65, 6,0)
						enemy_group.add(raquel)
						player.active_boss = True
					elif tile == 18:#create grenade box
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						decoration_group.add(decoration)	
					elif tile == 19:#create health box
						item_box = ItemBox(x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 20:#create exit
						exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
						exit_group.add(exit)

		return player, health_bar

	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])

class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

class ItemBox(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = health_box_img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		#scroll
		self.rect.x += screen_scroll
		#check if the player has picked up the box
		if pygame.sprite.collide_rect(self, player):
			#check what kind of box it was
			player.health += 25
			if player.health > 100:
				player.health = 100
			#delete the item box
			self.kill()

class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health

	def draw(self, health):
		#update with new health
		self.health = health
		#calculate health ratio
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		#move bullet
		self.rect.x += (self.direction * self.speed) + screen_scroll
		#check if bullet has gone off screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			if player.raquel_can_ultimate and level == MAX_LEVELS:
				player.health -= 200
			self.kill()
		#check for collision with level
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()

		#check collision with characters
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 25
					self.kill()

class RaquelsBullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = raquel_bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		#move bullet
		self.rect.x += (self.direction * self.speed) + screen_scroll
		#check if bullet has gone off screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill()
		#check for collision with level
		for tile in world.obstacle_list:
			#if not player.raquel_can_ultimate and level == MAX_LEVELS:
			#	player.health -= 100
			if tile[1].colliderect(self.rect):
				self.kill()

		#check collision with characters
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()

class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction

	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y

		#check for collision with level
		for tile in world.obstacle_list:
			#check collision with walls
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.direction *= -1
				dx = self.direction * self.speed
			#check for collision in the y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0
				#check if below the ground, i.e. thrown up
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom	


		#update grenade position
		self.rect.x += dx + screen_scroll
		self.rect.y += dy

		#countdown timer
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			grenade_sound.play()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			#do damage to anyone that is nearby
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
				abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
				player.health -= 50
			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
					abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
					enemy.health -= 150

class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f'images/explosion/exp{num}.png').convert_alpha()
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0

	def update(self):
		#scroll
		self.rect.x += screen_scroll

		EXPLOSION_SPEED = 4
		#update explosion amimation
		self.counter += 1

		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			#if the animation is complete then delete the explosion
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]

class Button():
	def __init__(self,x, y, image, scale):
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self, surface):
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		#draw button
		surface.blit(self.image, (self.rect.x, self.rect.y))

		return action

class ScreenFade():
	def __init__(self, direction, color, speed):
		self.direction = direction
		self.color = color
		self.speed = speed
		self.fade_counter = 0

	def fade(self):
		fade_complete = False
		self.fade_counter += self.speed
		if self.direction == 1:
			pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.color, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
			pygame.draw.rect(screen, self.color, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
		if self.direction == 2:
			pygame.draw.rect(screen, self.color, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
		if self.fade_counter >= SCREEN_WIDTH:
			fade_complete = True

		return fade_complete

class CutScene():
	def __init__(self, screen):
		self.cut_scenes_complete = []
		self.cut_scene = None
		self.cut_scene_running = False
		#Drawing Variables
		self.screen = screen
		self.window_size = 0

	def start_cut_scene(self, cut_scene):
		if cut_scene.name not in self.cut_scenes_complete:
			self.cut_scenes_complete.append(cut_scene.name)
			self.cut_scene = cut_scene
			self.cut_scene_running = True

	def end_cut_scene(self):
		self.cut_scene = None
		self.cut_scene_running = False

	def update(self):
		if self.cut_scene_running:
			if self.window_size < self.screen.get_height() * 0.3:
				self.window_size += 2
			self.cut_scene_running = self.cut_scene.update()
		else:
			self.end_cut_scene()

	def draw(self):
		if self.cut_scene_running:
			#Draw generic rect to all cut scenes
			pygame.draw.rect(self.screen, (0,0,0), (0,0,self.screen.get_width(),self.window_size))
			#Draw specific text for cut scene
			self.cut_scene.draw()

class InstructionsCutScene():
	def __init__(self):
		#Variables
		self.name = "Instructions"
		self.step = 0
		self.timer = pygame.time.get_ticks()
		self.cut_scene_running = True
		#Dialogue
		self.text = {
			'one': "Welcome to UP Rumble     ",
			'two': "Complete every level to fight the final boss     ",
			'three': "Oh, and don't let any enemy alive... Good luck!     "
		}
		self.text_counter = 0

	def update(self):
		#First part
		if self.step == 0:
			if int(self.text_counter) < len(self.text['one']):
				self.text_counter += 0.1
			else:
				self.step = 1
		#Second part
		if self.step == 1:
			if int(self.text_counter) < len(self.text['two']):
				self.text_counter += 0.08
			else:
				self.step = 2
		#Third part
		if self.step == 2:
			if int(self.text_counter) < len(self.text['three']):
				self.text_counter += 0.03
			else:
				#Finish the cut scene
				self.cut_scene_running = False

		return self.cut_scene_running

	def draw(self):
		if self.step == 0:
			draw_cut_scene_text(
				self.text['one'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)
		if self.step == 1:
			draw_cut_scene_text(
				self.text['two'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)
		if self.step == 2:
			draw_cut_scene_text(
				self.text['three'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)

class PrebossCutScene():
	def __init__(self):
		#Variables
		self.name = "Pre-boss"
		self.step = 0
		self.timer = pygame.time.get_ticks()
		self.cut_scene_running = True
		#Dialogue
		self.text = {
			'one': "You're pretty close     ",
			'two': "You'll finally fight the final boss and save the university     ",
			'three': "Soon you'll discover your special power     "
		}
		self.text_counter = 0

	def update(self):
		cheat = False
		#First part
		if self.step == 0:
			if int(self.text_counter) < len(self.text['one']):
				self.text_counter += 0.1
			else:
				self.step = 1
		#Second part
		if self.step == 1:
			if int(self.text_counter) < len(self.text['two']):
				self.text_counter += 0.2
			else:
				self.step = 2
		#Third part
		if self.step == 2:
			if not cheat:
				self.text_counter = 40
				cheat = True
			if int(self.text_counter) < len(self.text['three']):
				self.text_counter += 0.02
			else:
				#Finish the cut scene
				self.cut_scene_running = False

		return self.cut_scene_running

	def draw(self):
		if self.step == 0:
			draw_cut_scene_text(
				self.text['one'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)
		if self.step == 1:
			draw_cut_scene_text(
				self.text['two'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)
		if self.step == 2:
			draw_cut_scene_text(
				self.text['three'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)

class BossLevelCutScene():
	def __init__(self):
		#Variables
		self.name = "Boss-fight"
		self.step = 0
		self.timer = pygame.time.get_ticks()
		self.cut_scene_running = True
		#Dialogue
		if AGENT == 'agents/Alcaraz':
			self.text = {
				'one': "Nice job agent, let's do this!     ",
				'two': "With your powers, you achieved the final boss to get weaker.     ",
				'three': "Don't forget it, DON'T MISS A SHOT     "
			}

		if AGENT == 'agents/Cristian':
			self.text = {
				'one': "Nice job agent, let's do this!     ",
				'two': "With your powers, you can shoot faster and defeat her.     ",
				'three': "Don't forget it, DON'T MISS A SHOT     "
			}

		if AGENT == 'agents/DelPuerto':
			self.text = {
				'one': "Nice job agent, let's do this!     ",
				'two': "You randomly desactived one of her crucial powers so, go for her.     ",
				'three': "Probably you can miss some bullets, but try to avoid it...     "
			}

		if AGENT == 'agents/Elba':
			self.text = {
				'one': "Nice job agent, let's do this!     ",
				'two': "You've got 7 grandes in your inventory, make her blow up. (Press E key)     ",
				'three': "Don't forget it, DON'T MISS A SHOT     "
			}

		if AGENT == 'agents/Piña':
			self.text = {
				'one': "Nice job agent, let's do this!     ",
				'two': "Fortunately, your health will recover with time.     ",
				'three': "Don't forget it, DON'T MISS A SHOT     "
			}

		self.text_counter = 0

	def update(self):
		#First part
		if self.step == 0:
			if int(self.text_counter) < len(self.text['one']):
				self.text_counter += 0.15
			else:
				self.step = 1
		#Second part
		if self.step == 1:
			if int(self.text_counter) < len(self.text['two']):
				self.text_counter += 0.05
			else:
				self.step = 2
		#Third part
		if self.step == 2:
			if int(self.text_counter) < len(self.text['three']):
				self.text_counter += 0.001
			else:
				#Finish the cut scene
				self.cut_scene_running = False

		return self.cut_scene_running

	def draw(self):
		if self.step == 0:
			draw_cut_scene_text(
				self.text['one'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)
		if self.step == 1:
			draw_cut_scene_text(
				self.text['two'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)
		if self.step == 2:
			draw_cut_scene_text(
				self.text['three'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)

class VictoryCutScene():
	def __init__(self):
		#Variables
		self.name = "Victory"
		self.step = 0
		self.timer = pygame.time.get_ticks()
		self.cut_scene_running = True
		#Dialogue
		self.text = {
			'one': "You did this! You avenged UP!     ",
			'two': "Awesome job agent, you restored the lost peace.     ",
			'three': "Thanks a lot for playing!     "
		}
		self.text_counter = 0

	def update(self):
		#First part
		if self.step == 0:
			if int(self.text_counter) < len(self.text['one']):
				self.text_counter += 0.15
			else:
				self.step = 1
		#Second part
		if self.step == 1:
			if int(self.text_counter) < len(self.text['two']):
				self.text_counter += 0.15
			else:
				self.step = 2
		#Third part
		if self.step == 2:
			self.text_counter = 25
			if int(self.text_counter) < len(self.text['three']):
				self.text_counter += 0.1
			else:
				#Finish the cut scene
				self.cut_scene_running = False

		return self.cut_scene_running

	def draw(self):
		if self.step == 0:
			draw_cut_scene_text(
				self.text['one'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)
		if self.step == 1:
			draw_cut_scene_text(
				self.text['two'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)
		if self.step == 2:
			draw_cut_scene_text(
				self.text['three'][0:int(self.text_counter)],
				font,
				50,
				WHITE,
				50,
				50
			)

#Instantiation
#cut scene manager
cut_scene_manager = CutScene(screen)

#fades
intro_fade = ScreenFade(1, BLACK, 4)
death_fade = ScreenFade(2, BLACK, 4)

#buttons
start_button = Button(SCREEN_WIDTH // 2 - 65, SCREEN_HEIGHT // 2 + 180, start_img, .5)
exit_button = Button(SCREEN_WIDTH // 2 - 55, SCREEN_HEIGHT // 2 + 250, exit_img, .5)
restart_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

#agent's buttons
alcaraz_button = Button(SCREEN_WIDTH // 2 - 160, 0 + 80, alcaraz, 1)
cristian_button = Button(SCREEN_WIDTH // 2 + 60, 0 + 80, cristian, 1)
del_puerto_button = Button(SCREEN_WIDTH // 2 - 360, 0 + 80, del_puerto, 1)
elba_button = Button(SCREEN_WIDTH // 2 - 360, 0 + 280, elba, 1)
piña_button = Button(SCREEN_WIDTH // 2 - 160, 0 + 280, piña, 1)

#create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#game starts here
run = True
while run:
	clock.tick(FPS)

	#main menu
	if choose_agent == False:
		screen.blit(programIcon, (SCREEN_WIDTH // 2 - 230, 0))
		if start_button.draw(screen):
			choose_agent = True
		if exit_button.draw(screen):
			run = False
	#choose agent menu
	else:
		black_bg()
		draw_text('Choose your fighter: ', font, WHITE, 10, 35)
		if alcaraz_button.draw(screen):
			AGENT = 'agents/Alcaraz'
			start_intro = True
			start_game = True
		if cristian_button.draw(screen):
			AGENT = 'agents/Cristian'
			start_intro = True
			start_game = True
		if del_puerto_button.draw(screen):
			AGENT = 'agents/DelPuerto'
			start_intro = True
			start_game = True
		if elba_button.draw(screen):
			AGENT = 'agents/Elba'
			start_intro = True
			start_game = True
		if piña_button.draw(screen):
			AGENT = 'agents/Piña'
			start_intro = True
			start_game = True
	#game
	if start_game:
		#load selected agent
		if agent_loaded == False:
			world_data = []
			for row in range(ROWS):
				r = [-1] * COLS
				world_data.append(r)
			#load in level data and create world
			with open(f'levels/level{level}_data.csv', newline='') as csvfile:
				reader = csv.reader(csvfile, delimiter=',')
				for x, row in enumerate(reader):
					for y, tile in enumerate(row):
						world_data[x][y] = int(tile)
			world = World()
			player, health_bar = world.process_data(world_data)
			agent_loaded = True
			player.shoot_cooldown = 20
		#update background
		draw_bg()
		cut_scene_manager.update()
		cut_scene_manager.draw()
		#draw world map
		world.draw()
		#show player health
		health_bar.draw(player.health)
		player.update()
		player.draw()
		cut_scene_manager.start_cut_scene(InstructionsCutScene())
		#show the character's ultimate name at the left corner
		if level == MAX_LEVELS:
			if AGENT == 'agents/Alcaraz':
				draw_text('Reducing to an Absurdity', font, BLACK, 10, 35)
			if AGENT == 'agents/Cristian':
				draw_text('Power Gym', font, BLACK, 10, 35)
			if AGENT == 'agents/DelPuerto':
				draw_text('Lethal Boolean', font, BLACK, 10, 35)
			if AGENT == 'agents/Elba':
				draw_text('Dignity-Bomb', font, BLACK, 10, 35)
			if AGENT == 'agents/Piña':
				draw_text("God's protection", font, BLACK, 10, 35)
			active_ultimate = True
		#counts enemies in level and the dead ones, so if both are equal, level can be completed, instead,
		# the character must return to kill them all and then, complete the level.
		enemies_in_level = len(enemy_group)
		dead_enemies = 0

		#update enemy and its behaviour
		for enemy in enemy_group:
			#check if the character's challenging Raquel, so he can apply its ultimate
			player.delPuerto_ultimate(enemy)
			player.win(enemy)
			if not enemy.alive:
				dead_enemies += 1
			enemy.ai()
			enemy.update()
			enemy.draw()

		if enemies_in_level - dead_enemies == 0:
			next_level = True
		else:
			next_level = False

		#update and draw groups
		bullet_group.update()
		grenade_group.update()
		explosion_group.update()
		item_box_group.update()
		decoration_group.update()
		water_group.update()
		exit_group.update()
		bullet_group.draw(screen)
		grenade_group.draw(screen)
		explosion_group.draw(screen)
		item_box_group.draw(screen)
		decoration_group.draw(screen)
		water_group.draw(screen)
		exit_group.draw(screen)

		#start intro
		if start_intro == True:
			if intro_fade.fade():
				start_intro = False
				intro_fade.fade_counter = 0

		#update player actions
		if player.alive:
			player.piña_ultimate()
			#shoot bullets
			if shoot:
				player.shoot()
			#throw grenades
			elif grenade and grenade_thrown == False and player.grenades > 0:
				grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
				 			player.rect.top, player.direction)
				grenade_group.add(grenade)
				player.grenades -= 1
				grenade_thrown = True
			if player.in_air:
				player.update_action(2)#jump
			elif moving_left or moving_right:
				player.update_action(1)#run
			else:
				player.update_action(0)#idle
			screen_scroll, level_complete = player.move(moving_left, moving_right)
			bg_scroll -= screen_scroll
			#check if player has completed the level
			if level_complete and next_level:
				start_intro = True
				level += 1
				bg_scroll = 0
				world_data = reset_level()
				if level == MAX_LEVELS-1:
					cut_scene_manager.start_cut_scene(PrebossCutScene())
				#load in level data and create world
				if level <= MAX_LEVELS:
					with open(f'levels/level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)
					player.shoot_cooldown = 20
					if level == MAX_LEVELS:
						cut_scene_manager.start_cut_scene(BossLevelCutScene())
						player.elba_ultimate()
		#death
		else:
			screen_scroll = 0
			if death_fade.fade():
				#reload current level and try again
				if restart_button.draw(screen):
					death_fade.fade_counter = 0
					start_intro = True
					bg_scroll = 0
					world_data = reset_level()
					#load in level data and create world
					with open(f'levels/level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)
					if level == MAX_LEVELS:
						player.elba_ultimate()
			player.can_shoot = True
			player.shoot_cooldown = 20

	#keys
	for event in pygame.event.get():
		#quit game
		if event.type == pygame.QUIT:
			run = False

		#mouse
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			shoot = True
		#mouse button released
		if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			shoot = False

        #keyboard
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_e:
				grenade = True
			if event.key == pygame.K_w or event.key == pygame.K_SPACE:
				player.jump = True
				jump_sound.play()
        #keyboard button released
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_e:
				grenade = False
				grenade_thrown = False
			if event.key == pygame.K_w or event.key == pygame.K_SPACE:
				player.jump = False

	pygame.display.update()

pygame.quit()