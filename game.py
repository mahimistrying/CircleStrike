import pygame
import sys
import socket
import threading
import json
import math

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

class Bullet:
    def __init__(self, x, y, angle, owner_id):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10
        self.radius = 3
        self.owner_id = owner_id
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

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CircleStrike - Single Player")
        self.clock = pygame.time.Clock()
        self.running = True

        self.players = {}
        self.bullets = []
        self.my_player_id = None

    def handle_input(self):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        if self.my_player_id and self.my_player_id in self.players:
            player = self.players[self.my_player_id]

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

            # Rotation towards mouse
            player.rotate_towards(mouse_pos[0], mouse_pos[1])

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.my_player_id:  # Left click
                    self.shoot()

    def shoot(self):
        if self.my_player_id in self.players:
            player = self.players[self.my_player_id]
            bullet = Bullet(player.x, player.y, player.angle, self.my_player_id)
            self.bullets.append(bullet)

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.active:
                self.bullets.remove(bullet)

    def check_collisions(self):
        for bullet in self.bullets[:]:
            if not bullet.active:
                continue

            for player_id, player in self.players.items():
                if player_id == bullet.owner_id:
                    continue

                # Check collision
                dx = bullet.x - player.x
                dy = bullet.y - player.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < player.radius + bullet.radius:
                    player.health -= 25
                    bullet.active = False

                    if player.health <= 0:
                        player.health = 100
                        # Reset position
                        player.x = SCREEN_WIDTH // 2
                        player.y = SCREEN_HEIGHT // 2

    def draw(self):
        self.screen.fill(BLACK)

        # Draw players
        for player in self.players.values():
            player.draw(self.screen)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen)

        # Draw UI
        font = pygame.font.Font(None, 36)
        text = font.render(f"Players: {len(self.players)}", True, WHITE)
        self.screen.blit(text, (10, 10))

        pygame.display.flip()

    def run_local(self):
        # Create a local player for testing
        self.my_player_id = "local_player"
        self.players[self.my_player_id] = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BLUE, self.my_player_id)

        while self.running:
            self.handle_input()
            self.update_bullets()
            self.check_collisions()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    print("Starting local game (single player for testing)")
    print("Controls: WASD/Arrow keys to move, mouse to aim, left click to shoot")
    game.run_local()