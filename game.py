import pgzrun
import pygame #usado para espelhar a imagem, redimensionar e rect.
import sys

WIDTH = 640
HEIGHT = 480
DEBUG_MODE = True
TITLE = "Jumping Sky"

VELOCIDADE_ANIMACAO = 0.09 
VELOCIDADE_JOGADOR = 3
FORCA_PULO = -10
GRAVIDADE = 0.5
FOOTSTEP_INTERVAL = 0.3
ENEMY_IDLE_DURATION = 1.5
background_frame_atual = 0
background_timer = 0
VELOCIDADE_FUNDO = 0.3

# --- Layout do Nível ---
# P = Plataforma, H = Herói (start), E = Inimigo, F = Final
LEVEL_MAP = [
    "                                                                                                                      ",
    "                                                                                                                      ",
    "                                                                                                                      ",
    "                                                                                                                      ",
    "                                            E                                                                         ",
    "                      E                  PPPPPPPP                                            F                        ",
    "           E         PPPPPPPP         PP                                                   PPPPP                      ",
    "         PPPPP                  PP                     E                           PPPP   P                           ",
    "                   PP       E                     PPPPPPPPPPP                   P                    PP               ",
    "      P                   PPPPP      PPPP       P                     PP   PPP          P                             ",
    "   PP     PP    P    PPP                      P                PPPPP                             PP                   ",
    "H     E             E           E                 E      E           E     E       E         E                        ",
    "PPPPPPPPPPPPPPP   PPPPPPPPPP   PPPPPPPPPPPPP   PPPPP  PPPPPPP    PPPPPPPPPPPPPPPP PPPPP     PPPPP     PPPP   PPP      ",
]

game_state = 'menu'
sound_enabled = True

class Player:
    def __init__(self, pos):
        # Animações
        self.animations = {
            'idle': ['char_pink_idle08', 'char_pink_idle09', 'char_pink_idle10', 'char_pink_idle11'],
            'run': ['char_pink08', 'char_pink09', 'char_pink10','char_pink11'],
            'jump': ['char_pink10']
        }
        self.idle_surfaces = [images.load(f) for f in self.animations['idle']]
        self.run_surfaces = [images.load(f) for f in self.animations['run']]
        self.jump_surfaces = [images.load(f) for f in self.animations['jump']]
        
        self.state = 'idle'; self.last_state = 'idle'; self.facing_left = False
        
        # O ator começa com uma imagem, mas sua posição na tela será controlada pela câmera
        self.actor = Actor(self.animations['idle'][0])
        self.actor.world_pos = pos # Guarda a posição "real" no mundo
        
        self.frame_atual = 0; self.tempo_desde_ultimo_frame = 0
        self.velocity_y = 0; self.on_ground = True; self.footstep_timer = 0

    def update(self, dt):
        world_x, world_y = self.actor.world_pos
        tecla_esquerda = keyboard.left
        tecla_direita = keyboard.right
        tecla_pulo = keyboard.space

        if tecla_esquerda:
            world_x -= VELOCIDADE_JOGADOR
            self.facing_left = True
            if self.on_ground: self.state = 'run'
        elif tecla_direita:
            world_x += VELOCIDADE_JOGADOR
            self.facing_left = False
            if self.on_ground: self.state = 'run'
        else:
            if self.on_ground: self.state = 'idle'
        
        if self.on_ground and tecla_pulo:
            self.velocity_y = FORCA_PULO
            self.state = 'jump'
            self.on_ground = False
            if sound_enabled: sounds.jump.play()

        self.velocity_y += GRAVIDADE
        world_y += self.velocity_y
        self.actor.world_pos = (world_x, world_y)
        
        if self.state == 'run' and self.on_ground:
            self.footstep_timer += dt
            if self.footstep_timer >= FOOTSTEP_INTERVAL:
                self.footstep_timer = 0
                if sound_enabled: sounds.footstep_grass_001.play()
        else:
            self.footstep_timer = 0
        self.animar(dt)

    def animar(self, dt):
        if self.state != self.last_state: self.frame_atual = 0; self.tempo_desde_ultimo_frame = 0
        self.tempo_desde_ultimo_frame += dt
        if self.tempo_desde_ultimo_frame > VELOCIDADE_ANIMACAO:
            self.tempo_desde_ultimo_frame = 0
            surfaces = self.idle_surfaces if self.state == 'idle' else (self.run_surfaces if self.state == 'run' else self.jump_surfaces)
            self.frame_atual = (self.frame_atual + 1) % len(surfaces)
            surface_atual = surfaces[self.frame_atual]
            if self.facing_left: self.actor._surf = pygame.transform.flip(surface_atual, True, False)
            else: self.actor._surf = surface_atual
        self.last_state = self.state

    def draw(self): self.actor.draw()

    @property
    def hitbox(self):
        scale_w = 0.5  
        scale_h = 0.8  
        
        hitbox_width = self.actor.width * scale_w
        hitbox_height = self.actor.height * scale_h
        
        hb = pygame.Rect(0, 0, hitbox_width, hitbox_height)
        hb.center = self.actor.center
        return hb

class Enemy:
    def __init__(self, pos):
        # Dicionário de animações, igual ao do Player
        self.animations = {
            'idle': ['enemy1_idle08','enemy1_idle09','enemy1_idle10', 'enemy1_idle11'],
            'run': ['enemy1_08', 'enemy1_09','enemy1_10', 'enemy1_11']
        }
        self.idle_surfaces = [images.load(f) for f in self.animations['idle']]
        self.run_surfaces = [images.load(f) for f in self.animations['run']]
        
        
        self.state = 'run'
        self.last_state = 'run'
        self.facing_left = False
        
        
        self.actor = Actor('enemy1_idle08', pos)
        self.actor.world_pos = pos
        self.frame_atual = 0
        self.tempo_desde_ultimo_frame = 0

        # Lógica de patrulha
        self.move_speed = 0.6
        self.patrol_range = 60
        self.start_x = pos[0]
        self.target_x = self.start_x + self.patrol_range
        
        # Timer para o estado 'idle'
        self.idle_timer = 0

    def update(self, dt):
        world_x, world_y = self.actor.world_pos

        if self.state == 'run':
            if world_x < self.target_x:
                world_x += self.move_speed
                self.facing_left = False
            else:
                world_x -= self.move_speed
                self.facing_left = True
            
            # Se chegou perto do alvo, muda para o estado 'idle'
            if abs(world_x - self.target_x) < self.move_speed:
                self.state = 'idle'
                self.idle_timer = 0
                # Define o próximo alvo
                if self.target_x == self.start_x:
                    self.target_x = self.start_x + self.patrol_range
                else:
                    self.target_x = self.start_x
        
        elif self.state == 'idle':
            self.idle_timer += dt
            if self.idle_timer > ENEMY_IDLE_DURATION:
                self.state = 'run'
        
        self.actor.world_pos = (world_x, world_y)
        self.animar(dt)

    def animar(self, dt):
        if self.state != self.last_state:
            self.frame_atual = 0
            self.tempo_desde_ultimo_frame = 0
        
        self.tempo_desde_ultimo_frame += dt
        
        if self.tempo_desde_ultimo_frame > VELOCIDADE_ANIMACAO:
            self.tempo_desde_ultimo_frame = 0
            
            surfaces_para_animar = self.run_surfaces if self.state == 'run' else self.idle_surfaces
            
            self.frame_atual = (self.frame_atual + 1) % len(surfaces_para_animar)
            surface_atual = surfaces_para_animar[self.frame_atual]
            
            if self.facing_left:
                self.actor._surf = pygame.transform.flip(surface_atual, True, False)
            else:
                self.actor._surf = surface_atual
        
        self.last_state = self.state

    def draw(self):
        self.actor.draw()

    @property
    def hitbox(self):
        scale_w = 0.6
        scale_h = 0.8
        
        hitbox_width = self.actor.width * scale_w
        hitbox_height = self.actor.height * scale_h
        
        hb = pygame.Rect(0, 0, hitbox_width, hitbox_height)
        hb.center = self.actor.center
        return hb

class Coin:
    def __init__(self, pos):
        self.idle_frames = ['coin_00', 'coin_01', 'coin_02', 'coin_03', 'coin_04', 'coin_05','coin_06','coin_07','coin_08', 'coin_09', 'coin_10', 'coin_11']
        self.idle_surfaces = [images.load(f) for f in self.idle_frames]
        
        self.actor = Actor(self.idle_frames[0], pos)
        self.actor.world_pos = pos
        
        self.frame_atual = 0
        self.tempo_desde_ultimo_frame = 0

    def update(self, dt):
        self.tempo_desde_ultimo_frame += dt
        
        if self.tempo_desde_ultimo_frame > VELOCIDADE_ANIMACAO:
            self.tempo_desde_ultimo_frame = 0
            
            # Avança para o próximo frame
            self.frame_atual = (self.frame_atual + 1) % len(self.idle_surfaces)
            self.actor._surf = self.idle_surfaces[self.frame_atual]

    def draw(self):
        self.actor.draw()
        
# Variáveis Globais do Jogo
player = None
platforms = []
enemies = []
background_frames = []
coin = None
camera_x = 0
camera_y = 0
NUM_BACKGROUND_FRAMES = 4
menu_background_actor = Actor('menu_sprite', center=(WIDTH / 4, HEIGHT / 4))

# Animação do céu
for i in range(NUM_BACKGROUND_FRAMES):
    frame_name = f"ceu{i:02d}.gif"
    background_frames.append(frame_name)

background_actor = Actor(background_frames[0])


# Botões (Menu e Game Over) ---
start_button = Rect((WIDTH / 2 - 125, 200), (250, 50))
sound_button = Rect((WIDTH / 2 - 125, 270), (250, 50))
exit_button = Rect((WIDTH / 2 - 125, 340), (250, 50))

restart_button = Rect((WIDTH / 2 - 100, 250), (200, 50))
exit_game_over_button = Rect((WIDTH / 2 - 100, 320), (200, 50))


# Definição dos Botões do Menu
# Rects para definir a área clicável dos botões
start_button = Rect((WIDTH / 2 - 125, 200), (250, 50))
sound_button = Rect((WIDTH / 2 - 125, 270), (250, 50))
exit_button = Rect((WIDTH / 2 - 125, 340), (250, 50))
restart_button = Rect((WIDTH / 2 - 100, 250), (200, 50))
exit_game_over_button = Rect((WIDTH / 2 - 100, 320), (200, 50))

# Funções de Inicialização 
def start_game():
    global player, coin, game_state, win_timer
    platforms.clear(); enemies.clear(); coin = None
    tile_size = 36

    for row_index, row in enumerate(LEVEL_MAP):
        for col_index, char in enumerate(row):
            x = col_index * tile_size
            y = row_index * tile_size
            
            # Lógica para montar os tiles
            if char == 'P':
                try:
                    is_left_p = (LEVEL_MAP[row_index][col_index - 1] == 'P')
                except IndexError:
                    is_left_p = False 

                try:
                    is_right_p = (LEVEL_MAP[row_index][col_index + 1] == 'P')
                except IndexError:
                    is_right_p = False 

                tile_name = 'tile_middle' 
                
                if not is_left_p and is_right_p:
                    tile_name = 'tile_left'
                elif is_left_p and not is_right_p:
                    tile_name = 'tile_right'
                elif not is_left_p and not is_right_p:
                    tile_name = 'tile_single' 

                platform_actor = Actor(tile_name, topleft=(x, y))
                platform_actor.world_pos = (x, y)
                
                # Redimensiosa tile
                original_surf = platform_actor._surf
                scaled_surf = pygame.transform.scale(original_surf, (tile_size, tile_size))
                platform_actor._surf = scaled_surf
                
                platforms.append(platform_actor)

            elif char == 'H':
                player = Player((x, y))
            elif char == 'E':
                enemies.append(Enemy((x, y)))
            elif char == 'F':
                coin = Coin((x, y))

    camera_x = player.actor.world_pos[0] - WIDTH / 2
    camera_y = player.actor.world_pos[1] - HEIGHT / 2

    player.on_ground = False
    for p in platforms:
        if player.actor.colliderect(p):
            player.actor.bottom = p.top
            player.on_ground = True
            player.velocity_y = 0
            break
    
    player.actor.world_pos = (player.actor.world_pos[0], player.actor.y + camera_y)


    game_state = 'playing'
    if sound_enabled:
        music.play('pixel-adventure')
        music.set_volume(0.2)

def update_camera_and_positions():
    """Calcula a posição da câmera e atualiza a posição de tela de todos os objetos."""
    global camera_x, camera_y
    
    # Câmera segue o jogador com um movimento suave (lerp)
    target_camera_x = player.actor.world_pos[0] - WIDTH / 2
    target_camera_y = player.actor.world_pos[1] - HEIGHT / 2
    camera_x += (target_camera_x - camera_x) * 0.1
    camera_y += (target_camera_y - camera_y) * 0.1

    # Limites da Câmera para não mostrar fora do mapa
    level_width = len(LEVEL_MAP[0]) * 36
    level_height = len(LEVEL_MAP) * 36
    camera_x = max(0, min(camera_x, level_width - WIDTH))
    camera_y = max(0, min(camera_y, level_height - HEIGHT))

    # Atualiza a posição de TELA de todos os objetos
    all_game_objects = [player] + enemies + [coin]
    for obj in all_game_objects:
        if obj: obj.actor.x = obj.actor.world_pos[0] - camera_x
        obj.actor.y = obj.actor.world_pos[1] - camera_y
    for p in platforms:
        p.x = p.world_pos[0] - camera_x
        p.y = p.world_pos[1] - camera_y

#Desenha a tela do menu principal.
def draw_menu():
    background_actor.pos = (WIDTH / 2, HEIGHT / 2)
    background_actor.draw()
    screen.draw.text("Jumping Sky", center=(WIDTH / 2, 160), fontname="fonte.ttf", fontsize=50, color=(59, 142, 237))

    # Desenha os botões
    screen.draw.filled_rect(start_button, (59, 142, 237))
    screen.draw.text("Start Game", center=start_button.center, fontname="fonte.ttf",fontsize=25, color="white")

    screen.draw.filled_rect(sound_button, (59, 142, 237))
    sound_text = f"Music: {'OFF' if sound_enabled else 'ON'}"
    screen.draw.text(sound_text, center=sound_button.center, fontname="fonte.ttf", fontsize=25, color="white")

    screen.draw.filled_rect(exit_button, (190, 41, 41))
    screen.draw.text("Exit", center=exit_button.center, fontname="fonte.ttf", fontsize=25, color="white")

#Tela gameplay
def draw_game():
    background_actor.pos = (WIDTH / 2, HEIGHT / 2)
    background_actor.draw()

    for p in platforms:
        p.draw()
    for e in enemies:
        e.actor.draw()
    if coin:
        coin.draw()
    if player:
        player.draw()

def draw_game_over():
    background_actor.pos = (WIDTH / 2, HEIGHT / 2)
    background_actor.draw()
    screen.draw.text("GAME OVER", center=(WIDTH / 2, 200), fontname="fonte.ttf", fontsize=60, color=(190, 41, 41))
    
    screen.draw.filled_rect(restart_button, (189, 0, 3))
    screen.draw.text("Reiniciar", center=restart_button.center, fontname="fonte.ttf", fontsize=25, color="white")

    screen.draw.filled_rect(exit_game_over_button, (189, 0, 3))
    screen.draw.text("Sair", center=exit_game_over_button.center,fontname="fonte.ttf", fontsize=25, color="white")

def draw_win():
    background_actor.pos = (WIDTH / 2, HEIGHT / 2)
    background_actor.draw()
    screen.draw.text("Conseguiu!", center=(WIDTH / 2, 200), fontname="fonte.ttf", fontsize=60, color=(59, 142, 237))

    # Reutiliza os mesmos botões da tela de Game Over
    screen.draw.filled_rect(restart_button, (49, 176, 63))
    screen.draw.text("Reiniciar", center=restart_button.center, fontname="fonte.ttf", fontsize=25, color="white")

    screen.draw.filled_rect(exit_game_over_button, (49, 176, 63))
    screen.draw.text("Sair", center=exit_game_over_button.center, fontname="fonte.ttf", fontsize=25, color="white")

def draw():
    screen.clear()
    if game_state == 'menu':
        draw_menu()
    elif game_state == 'playing':
        draw_game()
    elif game_state == 'game_over': 
        draw_game_over()
    elif game_state == 'win':      
        draw_win()

# Função update principal (fora das classes)
def update(dt):
    global game_state, background_frame_atual, background_timer

    background_timer += dt
    if background_timer >= VELOCIDADE_FUNDO:
        background_timer = 0
        background_frame_atual = (background_frame_atual + 1) % NUM_BACKGROUND_FRAMES
        background_actor.image = background_frames[background_frame_atual]

    if game_state == 'playing':
        player.update(dt)
        for e in enemies: e.update(dt)
        if coin: coin.update(dt)
        
        update_camera_and_positions()
        player.on_ground = False
        for p in platforms:
            if player.actor.colliderect(p) and player.velocity_y >= 0:
                # Uma verificação extra para garantir que o jogador está em cima
                if player.actor.bottom <= p.top + (player.velocity_y):
                    player.actor.bottom = p.top
                    player.on_ground = True
                    player.velocity_y = 0
                    if player.state == 'jump': player.state = 'idle'
                        
        
    
        player.actor.world_pos = (player.actor.world_pos[0], player.actor.y + camera_y)
        if player.actor.world_pos[1] > len(LEVEL_MAP) * 36 + 100: 
            if game_state == 'playing': # Garante que o som toque só uma vez
                if sound_enabled: sounds.morte.play()
                game_state = 'game_over'; music.stop()
        for e in enemies:
            if player.hitbox.colliderect(e.hitbox): 
                if sound_enabled: sounds.morte.play()
                game_state = 'game_over'; music.stop()
        if coin and player.actor.colliderect(coin.actor): 
            if sound_enabled:sounds.coin.play() 
            game_state = 'win'; music.stop()

        background_timer += dt
        if background_timer >= VELOCIDADE_FUNDO:
            background_timer = 0
            background_frame_atual = (background_frame_atual + 1) % NUM_BACKGROUND_FRAMES
            background_actor.image = background_frames[background_frame_atual]
            
def on_mouse_down(pos):
    global game_state, sound_enabled
    button_was_clicked = False
    
    if game_state == 'menu':
        if start_button.collidepoint(pos): 
            start_game()
            button_was_clicked = True
        
        elif sound_button.collidepoint(pos):
            sound_enabled = not sound_enabled
            if sound_enabled:
                music.play('pixel-adventure') 
                music.set_volume(0.2)
            else: music.pause()
            button_was_clicked = True
        elif exit_button.collidepoint(pos): 
            sys.exit()
            button_was_clicked = True
        
    # Game over
    elif game_state == 'game_over':
        if restart_button.collidepoint(pos):
            start_game()
            button_was_clicked = True 
        elif exit_game_over_button.collidepoint(pos):
            sys.exit()
            button_was_clicked = True

    # Win
    elif game_state == 'win':
        if restart_button.collidepoint(pos):
            start_game()
            button_was_clicked = True
        elif exit_game_over_button.collidepoint(pos):
            sys.exit()
            button_was_clicked = True
    
    if button_was_clicked and sound_enabled:
        sounds.click_001.play()

music.play('pixel-adventure')
music.set_volume(0.2)

pgzrun.go()