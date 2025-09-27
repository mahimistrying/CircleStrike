from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import json
import asyncio
import time
import math
import random
import string
from typing import Dict, List
import uuid

app = FastAPI(title="CircleStrike Web", description="Real-time multiplayer web game")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Game state
class Player:
    def __init__(self, player_id: str, websocket: WebSocket):
        self.id = player_id
        self.websocket = websocket
        self.x = 512
        self.y = 384
        self.angle = 0
        self.health = 100
        self.lives = 3
        self.alive = True
        self.can_shoot = True
        self.shoot_cooldown_end = 0
        self.color = [0, 0, 255]  # Default blue

class Bullet:
    def __init__(self, x: float, y: float, angle: float, owner_id: str):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.angle = angle
        self.owner_id = owner_id
        self.speed = 10
        self.active = True

class GameManager:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.bullets: List[Bullet] = []
        self.game_over = False
        self.winner_id = None
        self.colors = [[0, 0, 255], [255, 0, 0], [0, 255, 0], [255, 255, 0], [255, 0, 255], [0, 255, 255]]
        self.game_paused = False
        self.pause_end_time = 0

    async def add_player(self, websocket: WebSocket) -> str:
        player_id = f"player_{len(self.players)}"
        player = Player(player_id, websocket)
        player.color = self.colors[len(self.players) % len(self.colors)]
        self.players[player_id] = player

        # Send initial game state to new player
        await self.send_to_player(player_id, {
            "type": "init",
            "player_id": player_id,
            "players": {pid: self.player_to_dict(p) for pid, p in self.players.items()}
        })

        # Notify all other players
        await self.broadcast({
            "type": "player_joined",
            "player_id": player_id,
            "player_data": self.player_to_dict(player)
        }, exclude=player_id)

        return player_id

    async def remove_player(self, player_id: str):
        if player_id in self.players:
            del self.players[player_id]
            await self.broadcast({
                "type": "player_left",
                "player_id": player_id
            })

    def player_to_dict(self, player: Player) -> dict:
        return {
            "x": player.x,
            "y": player.y,
            "angle": player.angle,
            "health": player.health,
            "lives": player.lives,
            "alive": player.alive,
            "color": player.color
        }

    async def handle_message(self, player_id: str, message: dict):
        if player_id not in self.players:
            return

        player = self.players[player_id]
        msg_type = message.get("type")

        if msg_type == "move":
            player.x = max(20, min(1004, message.get("x", player.x)))
            player.y = max(20, min(748, message.get("y", player.y)))
            player.angle = message.get("angle", player.angle)

            await self.broadcast({
                "type": "player_moved",
                "player_id": player_id,
                "x": player.x,
                "y": player.y,
                "angle": player.angle
            }, exclude=player_id)

        elif msg_type == "shoot":
            if player.can_shoot and player.alive and not self.game_paused:
                bullet = Bullet(player.x, player.y, player.angle, player_id)
                self.bullets.append(bullet)

                await self.broadcast({
                    "type": "bullet_fired",
                    "bullet": {
                        "id": bullet.id,
                        "x": bullet.x,
                        "y": bullet.y,
                        "angle": bullet.angle,
                        "owner_id": bullet.owner_id
                    }
                })

    async def send_to_player(self, player_id: str, data: dict):
        if player_id in self.players:
            try:
                await self.players[player_id].websocket.send_text(json.dumps(data))
            except:
                pass

    async def broadcast(self, data: dict, exclude: str = None):
        for player_id in list(self.players.keys()):
            if exclude and player_id == exclude:
                continue
            await self.send_to_player(player_id, data)

    async def game_loop(self):
        while True:
            current_time = time.time()

            # Check if pause should end
            if self.game_paused and current_time >= self.pause_end_time:
                self.game_paused = False
                await self.broadcast({
                    "type": "game_resumed"
                })

            # Skip bullet updates if game is paused
            if self.game_paused:
                await asyncio.sleep(1/60)
                continue

            # Update bullets and check collisions
            active_bullets = []

            for bullet in self.bullets:
                if not bullet.active:
                    continue

                # Update bullet position
                bullet.x += math.cos(bullet.angle) * bullet.speed
                bullet.y += math.sin(bullet.angle) * bullet.speed

                # Check if bullet is off screen
                if bullet.x < 0 or bullet.x > 1024 or bullet.y < 0 or bullet.y > 768:
                    bullet.active = False
                    await self.broadcast({
                        "type": "bullet_removed",
                        "bullet_id": bullet.id
                    })
                    continue

                # Check collision with players
                hit = False
                for target_id, target in self.players.items():
                    if target_id == bullet.owner_id or not target.alive:
                        continue

                    dx = bullet.x - target.x
                    dy = bullet.y - target.y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < 23:  # collision
                        target.health -= 25
                        bullet.active = False
                        hit = True

                        if target.health <= 0:
                            target.lives -= 1
                            target.health = 100

                            # Pause game for 2 seconds when someone loses a life
                            self.game_paused = True
                            self.pause_end_time = current_time + 2

                            await self.broadcast({
                                "type": "game_paused",
                                "reason": f"{target_id} lost a life!",
                                "pause_duration": 2
                            })

                            if target.lives > 0:
                                target.x = 512
                                target.y = 384
                            else:
                                target.alive = False

                            # Give shooter cooldown
                            if bullet.owner_id in self.players:
                                shooter = self.players[bullet.owner_id]
                                shooter.can_shoot = False
                                shooter.shoot_cooldown_end = current_time + 3

                        await self.broadcast({
                            "type": "player_update",
                            "player_id": target_id,
                            "health": target.health,
                            "lives": target.lives,
                            "alive": target.alive,
                            "x": target.x,
                            "y": target.y
                        })

                        if target.health <= 0:
                            await self.broadcast({
                                "type": "player_cooldown",
                                "player_id": bullet.owner_id,
                                "cooldown_end": shooter.shoot_cooldown_end
                            })

                        await self.broadcast({
                            "type": "bullet_removed",
                            "bullet_id": bullet.id
                        })

                        # Check win condition
                        alive_players = [p for p in self.players.values() if p.alive]
                        if len(alive_players) == 1:
                            await self.broadcast({
                                "type": "game_over",
                                "winner_id": alive_players[0].id
                            })

                        break

                if bullet.active and not hit:
                    active_bullets.append(bullet)

            self.bullets = active_bullets

            # Check cooldowns
            for player in self.players.values():
                if not player.can_shoot and current_time >= player.shoot_cooldown_end:
                    player.can_shoot = True
                    await self.send_to_player(player.id, {
                        "type": "player_cooldown_ended",
                        "player_id": player.id
                    })

            await asyncio.sleep(1/60)  # 60 FPS

# Room manager
class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, GameManager] = {}

    def create_room(self) -> str:
        # Generate 6-character room code
        room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        while room_code in self.rooms:
            room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        self.rooms[room_code] = GameManager()
        print(f"Created room: {room_code}")
        return room_code

    def get_room(self, room_code: str) -> GameManager:
        if room_code not in self.rooms:
            # Auto-create room if it doesn't exist
            self.rooms[room_code] = GameManager()
            print(f"Auto-created room: {room_code}")
        return self.rooms[room_code]

    def remove_empty_rooms(self):
        empty_rooms = [code for code, game in self.rooms.items() if len(game.players) == 0]
        for room_code in empty_rooms:
            del self.rooms[room_code]
            print(f"Removed empty room: {room_code}")

# Global room manager
room_manager = RoomManager()

@app.on_event("startup")
async def startup_event():
    # Start room cleanup task
    async def cleanup_rooms():
        while True:
            room_manager.remove_empty_rooms()
            await asyncio.sleep(60)  # Cleanup every minute

    asyncio.create_task(cleanup_rooms())

    # Start game loops for all rooms
    async def manage_game_loops():
        active_rooms = set()
        while True:
            current_rooms = set(room_manager.rooms.keys())
            new_rooms = current_rooms - active_rooms

            for room_code in new_rooms:
                game = room_manager.get_room(room_code)
                asyncio.create_task(game.game_loop())
                active_rooms.add(room_code)

            await asyncio.sleep(1)

    asyncio.create_task(manage_game_loops())

@app.get("/")
async def get_homepage(request: Request):
    return templates.TemplateResponse("lobby.html", {"request": request})

@app.get("/room/{room_code}")
async def get_game_room(request: Request, room_code: str):
    return templates.TemplateResponse("game.html", {"request": request, "room_code": room_code})

@app.post("/create-room")
async def create_room(request: Request):
    data = await request.json()
    custom_code = data.get("room_code", "").strip().upper()

    if custom_code:
        # Validate custom code
        if len(custom_code) < 2 or len(custom_code) > 20:
            return {"error": "Room code must be 2-20 characters"}

        # Check if room already exists
        if custom_code in room_manager.rooms and len(room_manager.rooms[custom_code].players) > 0:
            return {"error": "Room code already in use"}

        # Create room with custom code
        room_manager.rooms[custom_code] = GameManager()
        print(f"Created custom room: {custom_code}")
        return {"room_code": custom_code}
    else:
        # Generate random code if no custom code provided
        room_code = room_manager.create_room()
        return {"room_code": room_code}

@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    await websocket.accept()
    game = room_manager.get_room(room_code)
    player_id = await game.add_player(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await game.handle_message(player_id, message)
    except WebSocketDisconnect:
        await game.remove_player(player_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)