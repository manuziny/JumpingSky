import pgzrun
import pygame #usado apenas para para espelhar a imagem

WIDTH = 640
HEIGHT = 480
DEBUG_MODE = True
TITLE = "Pink Saur Game"

VELOCIDADE_ANIMACAO = 0.09  # Animação um pouco mais rápida
VELOCIDADE_JOGADOR = 3
FORCA_PULO = -11
GRAVIDADE = 0.5
FOOTSTEP_INTERVAL = 0.3
ENEMY_IDLE_DURATION = 1.5

# --- Layout do Nível ---
# P = Plataforma, H = Herói (start), E = Inimigo, F = Bandeira (Flag/Fim)
LEVEL_MAP = [
    "                                                                             ",
    "                                                                             ",
    "                                                                             ",
    "                                                                             ",
    "                                                                       ",
    "                     E         PPP        PPPPPPPPPP               F         ",
    "                   PPPPPPPPPP                                     PPPPP      ",
    "                                                       E                     ",
    "                                                     PPPPPPPPPPP                ",
    "    PPPP              PP         PPPPP       PPPP                                ",
    "                  PPPPP                                      PPPPP                ",
    "H           E                   E                 E                          ",
    "PPPPPPPPPPPPPPPPPPPPPPPPP   PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP",
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
        # Cria um retângulo menor para uma colisão mais justa
        # scale_w/h: 0.5 = 50% do tamanho. Ajuste para o que ficar melhor!
        scale_w = 0.5  # Largura do hitbox será 50% da largura da imagem
        scale_h = 0.8  # Altura do hitbox será 80% da altura da imagem
        
        hitbox_width = self.actor.width * scale_w
        hitbox_height = self.actor.height * scale_h
        
        # Cria o Rect do hitbox e o centraliza com o ator
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
        scale_w = 0.6 # Inimigos podem ter um hitbox um pouco diferente
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
        """A única função do update da bandeira é animá-la."""
        self.tempo_desde_ultimo_frame += dt
        
        if self.tempo_desde_ultimo_frame > VELOCIDADE_ANIMACAO:
            self.tempo_desde_ultimo_frame = 0
            
            # Avança para o próximo frame
            self.frame_atual = (self.frame_atual + 1) % len(self.idle_surfaces)
            self.actor._surf = self.idle_surfaces[self.frame_atual]

    def draw(self):
        self.actor.draw()

        
#Variáveis Globais do Jogo
player = None
platforms = []
enemies = []
coin = None
camera_x = 0
camera_y = 0
menu_background_actor = Actor('menu_sprite', center=(WIDTH / 4, HEIGHT / 4))


# --- Botões (Menu e Game Over) ---
start_button = Rect((WIDTH / 2 - 125, 200), (250, 50))
sound_button = Rect((WIDTH / 2 - 125, 270), (250, 50))
exit_button = Rect((WIDTH / 2 - 125, 340), (250, 50))

restart_button = Rect((WIDTH / 2 - 100, 250), (200, 50))
exit_game_over_button = Rect((WIDTH / 2 - 100, 320), (200, 50))

# redimensionando a sprite do menu
scale_factor = 6
original_surf = menu_background_actor._surf
new_width = original_surf.get_width() * scale_factor
new_height = original_surf.get_height() * scale_factor
menu_background_actor._surf = pygame.transform.scale(original_surf, (new_width, new_height))
menu_background_actor.center = (WIDTH / 4.25, HEIGHT / 100)

# --- Definição dos Botões do Menu ---
#Rects para definir a área clicável dos botões
start_button = Rect((WIDTH / 2 - 125, 200), (250, 50))
sound_button = Rect((WIDTH / 2 - 125, 270), (250, 50))
exit_button = Rect((WIDTH / 2 - 125, 340), (250, 50))
restart_button = Rect((WIDTH / 2 - 100, 250), (200, 50))
exit_game_over_button = Rect((WIDTH / 2 - 100, 320), (200, 50))

# --- Funções de Inicialização ---
def start_game():
    global player, coin, game_state, win_timer

    platforms.clear()
    enemies.clear()

    tile_size = 36 # Tamanho de cada "bloco" do nosso mapa

    for row_index, row in enumerate(LEVEL_MAP):
        for col_index, char in enumerate(row):
            x = col_index * tile_size
            y = row_index * tile_size
            
            if char == 'P':
                platform_actor = Actor('tile_01', topleft=(x, y))
                platform_actor.world_pos = (x, y)
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
    # sincroniza world_pos com a posição corrigida
    player.actor.world_pos = (player.actor.world_pos[0], player.actor.y + camera_y)


    game_state = 'playing'
    if sound_enabled:
        music.play('pixel-adventure')
        music.set_volume(0.1)

def update_camera_and_positions():
    """Calcula a posição da câmera e atualiza a posição de tela de todos os objetos."""
    global camera_x, camera_y
    
    # Câmera segue o jogador com um movimento suave (lerp)
    target_camera_x = player.actor.world_pos[0] - WIDTH / 2
    target_camera_y = player.actor.world_pos[1] - HEIGHT / 2
    camera_x += (target_camera_x - camera_x) * 0.1
    camera_y += (target_camera_y - camera_y) * 0.1

    # Limites da Câmera (para não mostrar fora do mapa)
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
    screen.fill((255, 192, 203)) 
    menu_background_actor.draw()
    screen.draw.text("Pink Saur Game", center=(WIDTH / 2, 130), fontsize=50, color=(195, 93, 93))

    # Desenha os botões
    screen.draw.filled_rect(start_button, (255, 153, 153))
    screen.draw.text("Start Game", center=start_button.center, fontsize=35, color="black")

    screen.draw.filled_rect(sound_button, (255, 153, 153))
    sound_text = f"Music: {'OFF' if sound_enabled else 'ON'}"
    screen.draw.text(sound_text, center=sound_button.center, fontsize=35, color="black")

    screen.draw.filled_rect(exit_button, (155, 53, 53))
    screen.draw.text("Exit", center=exit_button.center, fontsize=35, color="black")

#Tela gameplay
def draw_game():
    screen.fill((173, 216, 230))
    for p in platforms:
        p.draw()
    for e in enemies:
        e.actor.draw()
    if coin:
        coin.draw()
    if player:
        player.draw()

def draw_game_over():
    screen.fill((255, 182, 193)) # Fundo vermelho escuro
    screen.draw.text("GAME OVER", center=(WIDTH / 2, 150), fontsize=80, color="red")

    # Desenha os botões
    screen.draw.filled_rect(restart_button, (255, 153, 153))
    screen.draw.text("Reiniciar", center=restart_button.center, fontsize=35, color="white")

    screen.draw.filled_rect(exit_game_over_button, (255, 153, 153))
    screen.draw.text("Sair do Jogo", center=exit_game_over_button.center, fontsize=35, color="white")

def draw_win():
    screen.fill((175, 238, 238))
    screen.draw.text("Conseguiu!", center=(WIDTH / 2, 150), fontsize=80, color="white")

    # Reutiliza os mesmos botões da tela de Game Over
    screen.draw.filled_rect(restart_button, (255, 153, 153))
    screen.draw.text("Reiniciar", center=restart_button.center, fontsize=35, color="white")

    screen.draw.filled_rect(exit_game_over_button, (255, 153, 153))
    screen.draw.text("Sair do Jogo", center=exit_game_over_button.center, fontsize=35, color="white")

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
    global game_state

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
                    if player.state == 'jump':
                        player.state = 'idle'
        
    
        player.actor.world_pos = (player.actor.world_pos[0], player.actor.y + camera_y)
        if player.actor.world_pos[1] > len(LEVEL_MAP) * 36 + 100: 
            game_state = 'game_over'; music.stop()
        for e in enemies:
            if player.hitbox.colliderect(e.hitbox): 
                game_state = 'game_over'; music.stop()
        if coin and player.actor.colliderect(coin.actor): 
            game_state = 'win'; music.stop()
            

def on_mouse_down(pos):
    global game_state, sound_enabled
    
    if game_state == 'menu':
        if start_button.collidepoint(pos): start_game()
        elif sound_button.collidepoint(pos):
            sound_enabled = not sound_enabled
            if sound_enabled: music.unpause() if music.is_playing() else music.play('background_music')
            else: music.pause()
        elif exit_button.collidepoint(pos): quit()
        
    # Game over
    elif game_state == 'game_over':
        if restart_button.collidepoint(pos):
            start_game() 
        elif exit_game_over_button.collidepoint(pos): quit()

    # Win
    elif game_state == 'win':
        if restart_button.collidepoint(pos):
            start_game()
        elif exit_game_over_button.collidepoint(pos): quit()

music.play('pixel-adventure')
music.set_volume(0.2)

pgzrun.go()