import socket
import threading
import json
import time
import math

class GameServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.clients = {}
        self.players = {}
        self.bullets = []
        self.running = False

        print(f"Server initialized on {host}:{port}")

    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            print(f"Server listening on {self.host}:{self.port}")

            # Start game loop in separate thread
            threading.Thread(target=self.game_loop, daemon=True).start()

            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    print(f"New connection from {address}")

                    player_id = f"player_{len(self.clients)}"
                    self.clients[player_id] = {
                        'socket': client_socket,
                        'address': address,
                        'connected': True
                    }

                    # Initialize player data
                    player_count = len(self.players)
                    colors = [[0, 0, 255], [255, 0, 0], [0, 255, 0], [255, 255, 0], [255, 0, 255], [0, 255, 255]]
                    self.players[player_id] = {
                        'x': 512,
                        'y': 384,
                        'angle': 0,
                        'health': 100,
                        'lives': 3,
                        'can_shoot': True,
                        'shoot_cooldown_end': 0,
                        'alive': True,
                        'color': colors[player_count % len(colors)]
                    }

                    # Send initial data
                    self.send_to_client(player_id, {
                        'type': 'init',
                        'player_id': player_id,
                        'players': self.players
                    })

                    # Start client handler thread
                    threading.Thread(target=self.handle_client, args=(player_id,), daemon=True).start()

                    # Notify all clients about new player
                    self.broadcast({
                        'type': 'player_joined',
                        'player_id': player_id,
                        'player_data': self.players[player_id]
                    })

                except socket.error as e:
                    if self.running:
                        print(f"Error accepting connection: {e}")

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.shutdown()

    def handle_client(self, player_id):
        client_socket = self.clients[player_id]['socket']

        try:
            while self.running and self.clients[player_id]['connected']:
                data = client_socket.recv(1024)
                if not data:
                    break

                try:
                    message = json.loads(data.decode('utf-8'))
                    self.process_message(player_id, message)
                except json.JSONDecodeError:
                    continue

        except socket.error:
            pass
        finally:
            self.disconnect_client(player_id)

    def process_message(self, player_id, message):
        msg_type = message.get('type')

        if msg_type == 'move':
            if player_id in self.players:
                self.players[player_id]['x'] = message['x']
                self.players[player_id]['y'] = message['y']
                self.players[player_id]['angle'] = message['angle']

                # Broadcast to all other clients
                self.broadcast({
                    'type': 'player_moved',
                    'player_id': player_id,
                    'x': message['x'],
                    'y': message['y'],
                    'angle': message['angle']
                }, exclude=player_id)

        elif msg_type == 'shoot':
            # Check if player can shoot
            if (player_id in self.players and
                self.players[player_id]['can_shoot'] and
                self.players[player_id]['alive']):

                bullet_data = {
                    'x': message['x'],
                    'y': message['y'],
                    'angle': message['angle'],
                    'owner_id': player_id,
                    'id': f"bullet_{time.time()}_{player_id}",
                    'speed': 10,
                    'active': True
                }
                self.bullets.append(bullet_data)

                # Broadcast bullet to all clients
                self.broadcast({
                    'type': 'bullet_fired',
                    'bullet': bullet_data
                })

    def game_loop(self):
        while self.running:
            # Update bullets and check collisions
            active_bullets = []
            for bullet in self.bullets[:]:
                if not bullet['active']:
                    continue

                # Update bullet position
                bullet['x'] += math.cos(bullet['angle']) * bullet['speed']
                bullet['y'] += math.sin(bullet['angle']) * bullet['speed']

                # Check if bullet is off screen
                if (bullet['x'] < 0 or bullet['x'] > 1024 or
                    bullet['y'] < 0 or bullet['y'] > 768):
                    bullet['active'] = False
                    continue

                # Check collision with players
                hit_player = False
                for player_id, player in self.players.items():
                    if player_id == bullet['owner_id'] or not player['alive']:
                        continue

                    # Calculate distance between bullet and player
                    dx = bullet['x'] - player['x']
                    dy = bullet['y'] - player['y']
                    distance = math.sqrt(dx * dx + dy * dy)

                    # Check collision (bullet radius 3 + player radius 20)
                    if distance < 23:
                        # Hit!
                        player['health'] -= 25
                        bullet['active'] = False
                        hit_player = True

                        print(f"Player {player_id} hit! Health: {player['health']}")

                        # Check if player died
                        if player['health'] <= 0:
                            player['lives'] -= 1
                            player['health'] = 100

                            if player['lives'] > 0:
                                # Respawn player
                                player['x'] = 512
                                player['y'] = 384
                                print(f"Player {player_id} died! Lives remaining: {player['lives']}")
                            else:
                                # Game over
                                player['alive'] = False
                                print(f"Player {player_id} eliminated! Game over.")

                            # Give killer a 3-second shooting cooldown
                            killer_id = bullet['owner_id']
                            if killer_id in self.players:
                                self.players[killer_id]['can_shoot'] = False
                                self.players[killer_id]['shoot_cooldown_end'] = time.time() + 3
                                print(f"Player {killer_id} has 3-second cooldown")

                        # Broadcast player update
                        self.broadcast({
                            'type': 'player_update',
                            'player_id': player_id,
                            'health': player['health'],
                            'lives': player['lives'],
                            'alive': player['alive'],
                            'x': player['x'],
                            'y': player['y']
                        })

                        # Check if game is over (only one player alive)
                        alive_players = [pid for pid, p in self.players.items() if p['alive']]
                        if len(alive_players) == 1:
                            winner_id = alive_players[0]
                            self.broadcast({
                                'type': 'game_over',
                                'winner_id': winner_id
                            })
                            print(f"Game Over! Winner: {winner_id}")
                        elif len(alive_players) == 0:
                            self.broadcast({
                                'type': 'game_over',
                                'winner_id': None
                            })
                            print("Game Over! No survivors!")

                        # Broadcast killer cooldown
                        if player['health'] <= 0:
                            self.broadcast({
                                'type': 'player_cooldown',
                                'player_id': bullet['owner_id'],
                                'cooldown_end': self.players[bullet['owner_id']]['shoot_cooldown_end']
                            })

                        # Broadcast bullet removal
                        self.broadcast({
                            'type': 'bullet_removed',
                            'bullet_id': bullet['id']
                        })

                        break

                if bullet['active']:
                    active_bullets.append(bullet)

            self.bullets = active_bullets

            # Check shooting cooldowns
            current_time = time.time()
            for player_id, player in self.players.items():
                if not player['can_shoot'] and current_time >= player['shoot_cooldown_end']:
                    player['can_shoot'] = True
                    self.broadcast({
                        'type': 'player_cooldown_ended',
                        'player_id': player_id
                    })
                    print(f"Player {player_id} can shoot again")

            time.sleep(1/60)  # 60 FPS server tick

    def send_to_client(self, player_id, data):
        if player_id in self.clients and self.clients[player_id]['connected']:
            try:
                message = json.dumps(data).encode('utf-8')
                self.clients[player_id]['socket'].send(message)
            except socket.error:
                self.disconnect_client(player_id)

    def broadcast(self, data, exclude=None):
        for player_id in list(self.clients.keys()):
            if exclude and player_id == exclude:
                continue
            self.send_to_client(player_id, data)

    def disconnect_client(self, player_id):
        if player_id in self.clients:
            self.clients[player_id]['connected'] = False
            try:
                self.clients[player_id]['socket'].close()
            except:
                pass
            del self.clients[player_id]

            if player_id in self.players:
                del self.players[player_id]

            # Notify remaining clients
            self.broadcast({
                'type': 'player_left',
                'player_id': player_id
            })

            print(f"Client {player_id} disconnected")

    def shutdown(self):
        self.running = False
        for player_id in list(self.clients.keys()):
            self.disconnect_client(player_id)
        try:
            self.socket.close()
        except:
            pass
        print("Server shutdown complete")

if __name__ == "__main__":
    server = GameServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()