import pygame
import socket
import threading
import json
import math
import sys

pygame.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

class Player:
    def __init__(self, x, y, color, player_id):
        self.x = x
        self.y = y
        self.color = color
        self.player_id = player_id
        self.radius = 20
        self.speed = 5
        self.health = 100
        self.lives = 3
        self.alive = True
        self.angle = 0

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        # Keep player on screen
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

    def rotate_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        self.angle = math.atan2(dy, dx)

    def draw(self, screen):
        # Draw player circle
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

        # Draw direction indicator
        end_x = self.x + math.cos(self.angle) * (self.radius + 10)
        end_y = self.y + math.sin(self.angle) * (self.radius + 10)
        pygame.draw.line(screen, WHITE, (self.x, self.y), (end_x, end_y), 3)

        # Draw health bar
        bar_width = 40
        bar_height = 6
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.radius - 15

        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_width * (self.health / 100), bar_height))

        # Draw lives indicator
        for i in range(self.lives):
            life_x = self.x - 15 + (i * 10)
            life_y = self.y - self.radius - 25
            pygame.draw.circle(screen, WHITE, (int(life_x), int(life_y)), 3)

        # Draw player ID
        font = pygame.font.Font(None, 24)
        text = font.render(self.player_id, True, WHITE)
        text_rect = text.get_rect(center=(self.x, self.y + self.radius + 25))
        screen.blit(text, text_rect)

class Bullet:
    def __init__(self, x, y, angle, owner_id, bullet_id):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10
        self.radius = 3
        self.owner_id = owner_id
        self.bullet_id = bullet_id
        self.active = True

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # Remove bullet if off screen
        if (self.x < 0 or self.x > SCREEN_WIDTH or
            self.y < 0 or self.y > SCREEN_HEIGHT):
            self.active = False

    def draw(self, screen):
        if self.active:
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)

class MultiplayerClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Multishot - Multiplayer Client")
        self.clock = pygame.time.Clock()
        self.running = True

        self.players = {}
        self.bullets = {}
        self.my_player_id = None

        # Input tracking
        self.last_position = None
        self.last_angle = None

        # Cooldown system
        self.can_shoot = True
        self.cooldown_end_time = 0

        # Game state
        self.game_over = False
        self.is_winner = False

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to server at {self.host}:{self.port}")

            # Start network thread
            threading.Thread(target=self.network_loop, daemon=True).start()
            return True

        except socket.error as e:
            print(f"Failed to connect: {e}")
            return False

    def network_loop(self):
        try:
            while self.connected:
                data = self.socket.recv(1024)
                if not data:
                    break

                try:
                    message = json.loads(data.decode('utf-8'))
                    self.process_server_message(message)
                except json.JSONDecodeError:
                    continue

        except socket.error:
            pass
        finally:
            self.connected = False
            print("Disconnected from server")

    def process_server_message(self, message):
        msg_type = message.get('type')

        if msg_type == 'init':
            self.my_player_id = message['player_id']
            for player_id, player_data in message['players'].items():
                self.players[player_id] = Player(
                    player_data['x'],
                    player_data['y'],
                    tuple(player_data['color']),
                    player_id
                )
                self.players[player_id].health = player_data['health']
                self.players[player_id].lives = player_data.get('lives', 3)
                self.players[player_id].alive = player_data.get('alive', True)
                self.players[player_id].angle = player_data['angle']

        elif msg_type == 'player_joined':
            player_id = message['player_id']
            player_data = message['player_data']
            self.players[player_id] = Player(
                player_data['x'],
                player_data['y'],
                tuple(player_data['color']),
                player_id
            )
            self.players[player_id].health = player_data['health']
            self.players[player_id].lives = player_data.get('lives', 3)
            self.players[player_id].alive = player_data.get('alive', True)
            self.players[player_id].angle = player_data['angle']

        elif msg_type == 'player_left':
            player_id = message['player_id']
            if player_id in self.players:
                del self.players[player_id]

        elif msg_type == 'player_moved':
            player_id = message['player_id']
            if player_id in self.players and player_id != self.my_player_id:
                self.players[player_id].x = message['x']
                self.players[player_id].y = message['y']
                self.players[player_id].angle = message['angle']

        elif msg_type == 'bullet_fired':
            bullet_data = message['bullet']
            bullet = Bullet(
                bullet_data['x'],
                bullet_data['y'],
                bullet_data['angle'],
                bullet_data['owner_id'],
                bullet_data['id']
            )
            self.bullets[bullet_data['id']] = bullet

        elif msg_type == 'player_health_update':
            player_id = message['player_id']
            if player_id in self.players:
                self.players[player_id].health = message['health']
                self.players[player_id].x = message['x']
                self.players[player_id].y = message['y']

        elif msg_type == 'bullet_removed':
            bullet_id = message['bullet_id']
            if bullet_id in self.bullets:
                del self.bullets[bullet_id]

        elif msg_type == 'player_update':
            player_id = message['player_id']
            if player_id in self.players:
                self.players[player_id].health = message['health']
                self.players[player_id].lives = message['lives']
                self.players[player_id].alive = message['alive']
                self.players[player_id].x = message['x']
                self.players[player_id].y = message['y']

        elif msg_type == 'player_cooldown':
            player_id = message['player_id']
            if player_id == self.my_player_id:
                self.can_shoot = False
                self.cooldown_end_time = message['cooldown_end']

        elif msg_type == 'player_cooldown_ended':
            player_id = message['player_id']
            if player_id == self.my_player_id:
                self.can_shoot = True

        elif msg_type == 'game_over':
            winner_id = message.get('winner_id')
            self.game_over = True
            if winner_id == self.my_player_id:
                self.is_winner = True
            else:
                self.is_winner = False

    def send_to_server(self, data):
        if self.connected:
            try:
                message = json.dumps(data).encode('utf-8')
                self.socket.send(message)
            except socket.error:
                self.connected = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        if self.my_player_id and self.my_player_id in self.players:
            player = self.players[self.my_player_id]
            moved = False

            # Movement
            dx = dy = 0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = 1
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy = -1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy = 1

            if dx != 0 or dy != 0:
                player.move(dx, dy)
                moved = True

            # Rotation towards mouse
            old_angle = player.angle
            player.rotate_towards(mouse_pos[0], mouse_pos[1])
            if abs(player.angle - old_angle) > 0.01:
                moved = True

            # Send position update if moved
            if moved or (self.last_position != (player.x, player.y) or self.last_angle != player.angle):
                self.send_to_server({
                    'type': 'move',
                    'x': player.x,
                    'y': player.y,
                    'angle': player.angle
                })
                self.last_position = (player.x, player.y)
                self.last_angle = player.angle

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.my_player_id and self.can_shoot and not self.game_over:  # Left click
                    self.shoot()

    def shoot(self):
        if self.my_player_id in self.players:
            player = self.players[self.my_player_id]
            self.send_to_server({
                'type': 'shoot',
                'x': player.x,
                'y': player.y,
                'angle': player.angle
            })

    def update_bullets(self):
        for bullet_id in list(self.bullets.keys()):
            bullet = self.bullets[bullet_id]
            bullet.update()
            if not bullet.active:
                del self.bullets[bullet_id]

    def draw(self):
        self.screen.fill(BLACK)

        # Draw players
        for player in self.players.values():
            if player.alive:  # Only draw alive players
                # Highlight own player
                if player.player_id == self.my_player_id:
                    pygame.draw.circle(self.screen, WHITE, (int(player.x), int(player.y)), player.radius + 3, 2)
                player.draw(self.screen)

        # Draw bullets
        for bullet in self.bullets.values():
            bullet.draw(self.screen)

        # Draw UI
        font = pygame.font.Font(None, 36)
        status = "Connected" if self.connected else "Disconnected"
        color = GREEN if self.connected else RED
        text = font.render(f"Status: {status} | Players: {len(self.players)}", True, color)
        self.screen.blit(text, (10, 10))

        if self.my_player_id:
            text2 = font.render(f"You are: {self.my_player_id}", True, WHITE)
            self.screen.blit(text2, (10, 50))

            # Debug: Show my player position and lives
            if self.my_player_id in self.players:
                my_player = self.players[self.my_player_id]
                debug_text = font.render(f"Lives: {my_player.lives} | Health: {my_player.health}", True, WHITE)
                self.screen.blit(debug_text, (10, 90))

                # Show cooldown timer
                if not self.can_shoot:
                    import time
                    remaining = max(0, self.cooldown_end_time - time.time())
                    if remaining > 0:
                        cooldown_text = font.render(f"Cooldown: {remaining:.1f}s", True, RED)
                        self.screen.blit(cooldown_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))

        # Instructions
        if not self.game_over:
            font_small = pygame.font.Font(None, 24)
            instructions = [
                "WASD/Arrow keys: Move",
                "Mouse: Aim",
                "Left Click: Shoot"
            ]
            for i, instruction in enumerate(instructions):
                text = font_small.render(instruction, True, WHITE)
                self.screen.blit(text, (10, SCREEN_HEIGHT - 80 + i * 25))

        # Game Over Screen
        if self.game_over:
            # Create a semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))

            # Big font for game over message
            big_font = pygame.font.Font(None, 120)
            medium_font = pygame.font.Font(None, 60)

            if self.is_winner:
                # Winner message
                win_text = big_font.render("YOU WIN!", True, RED)
                win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
                self.screen.blit(win_text, win_rect)

                # Victory message
                victory_text = medium_font.render("VICTORY!", True, (255, 215, 0))  # Gold color
                victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                self.screen.blit(victory_text, victory_rect)
            else:
                # Loser message
                lose_text = big_font.render("YOU LOSE!", True, RED)
                lose_rect = lose_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
                self.screen.blit(lose_text, lose_rect)

                # Defeat message
                defeat_text = medium_font.render("DEFEATED!", True, (128, 128, 128))  # Gray color
                defeat_rect = defeat_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                self.screen.blit(defeat_text, defeat_rect)

            # Play again instruction
            small_font = pygame.font.Font(None, 36)
            restart_text = small_font.render("Press ESC to exit", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
            self.screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            self.update_bullets()
            self.draw()
            self.clock.tick(FPS)

        if self.connected:
            try:
                self.socket.close()
            except:
                pass

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    client = MultiplayerClient()

    if not client.connect():
        print("Failed to connect to server. Make sure the server is running!")
        input("Press Enter to exit...")
        sys.exit(1)

    print("Connected! Starting game...")
    print("Controls: WASD/Arrow keys to move, mouse to aim, left click to shoot")
    client.run()