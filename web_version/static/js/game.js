// CircleStrike Web Game Client
class CircleStrikeGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.ws = null;
        this.players = {};
        this.bullets = {};
        this.myPlayerId = null;
        this.gameOver = false;
        this.canShoot = true;
        this.cooldownEndTime = 0;

        // Input state
        this.keys = {};
        this.mousePos = { x: 0, y: 0 };
        this.movement = { x: 0, y: 0 };

        // Mobile controls
        this.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        this.joystick = {
            active: false,
            startPos: { x: 0, y: 0 },
            currentPos: { x: 0, y: 0 }
        };

        // Game state
        this.game_paused = false;
        this.pause_reason = "";
        this.pause_countdown = 0;

        this.init();

        // Display room code
        if (typeof roomCode !== 'undefined') {
            document.getElementById('roomCode').textContent = roomCode;
        }
    }

    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.gameLoop();

        if (this.isMobile) {
            this.setupMobileControls();
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/${roomCode}`);

        this.ws.onopen = () => {
            this.updateStatus('Connected', '#00ff00');
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleServerMessage(message);
        };

        this.ws.onclose = () => {
            this.updateStatus('Disconnected', '#ff0000');
        };

        this.ws.onerror = () => {
            this.updateStatus('Connection Error', '#ff0000');
        };
    }

    handleServerMessage(message) {
        switch (message.type) {
            case 'init':
                this.myPlayerId = message.player_id;
                this.players = {};
                for (const [playerId, playerData] of Object.entries(message.players)) {
                    this.players[playerId] = playerData;
                }
                this.updatePlayerInfo();
                break;

            case 'player_joined':
                this.players[message.player_id] = message.player_data;
                break;

            case 'player_left':
                delete this.players[message.player_id];
                break;

            case 'player_moved':
                if (this.players[message.player_id]) {
                    this.players[message.player_id].x = message.x;
                    this.players[message.player_id].y = message.y;
                    this.players[message.player_id].angle = message.angle;
                }
                break;

            case 'bullet_fired':
                this.bullets[message.bullet.id] = message.bullet;
                break;

            case 'bullet_removed':
                delete this.bullets[message.bullet_id];
                break;

            case 'player_update':
                if (this.players[message.player_id]) {
                    this.players[message.player_id].health = message.health;
                    this.players[message.player_id].lives = message.lives;
                    this.players[message.player_id].alive = message.alive;
                    this.players[message.player_id].x = message.x;
                    this.players[message.player_id].y = message.y;
                    this.updatePlayerInfo();
                }
                break;

            case 'player_cooldown':
                if (message.player_id === this.myPlayerId) {
                    this.canShoot = false;
                    this.cooldownEndTime = message.cooldown_end;
                }
                break;

            case 'player_cooldown_ended':
                if (message.player_id === this.myPlayerId) {
                    this.canShoot = true;
                    document.getElementById('cooldown').style.display = 'none';
                }
                break;

            case 'game_over':
                this.gameOver = true;
                this.showGameOver(message.winner_id === this.myPlayerId);
                break;

            case 'game_paused':
                this.game_paused = true;
                this.pause_reason = message.reason;
                this.pause_countdown = message.pause_duration;
                break;

            case 'game_resumed':
                this.game_paused = false;
                this.pause_reason = "";
                this.pause_countdown = 0;
                break;
        }
    }

    setupEventListeners() {
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            this.keys[e.key.toLowerCase()] = true;

            // ESC key to quit game
            if (e.key === 'Escape') {
                e.preventDefault();
                quitGame();
            }

            // Spacebar to shoot
            if (e.key === ' ' || e.key === 'Space') {
                e.preventDefault();
                if (!this.gameOver && this.canShoot && this.myPlayerId && this.players[this.myPlayerId] && this.players[this.myPlayerId].alive) {
                    this.shoot();
                }
            }
        });

        document.addEventListener('keyup', (e) => {
            this.keys[e.key.toLowerCase()] = false;
        });

        // Mouse events
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const scaleX = this.canvas.width / rect.width;
            const scaleY = this.canvas.height / rect.height;

            this.mousePos.x = (e.clientX - rect.left) * scaleX;
            this.mousePos.y = (e.clientY - rect.top) * scaleY;
        });

        this.canvas.addEventListener('click', (e) => {
            if (!this.gameOver && this.canShoot) {
                this.shoot();
            }
        });
    }

    setupMobileControls() {
        const joystickBase = document.getElementById('joystickBase');
        const joystickKnob = document.getElementById('joystickKnob');
        const shootButton = document.getElementById('shootButton');

        // Joystick touch events
        joystickBase.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const rect = joystickBase.getBoundingClientRect();
            this.joystick.active = true;
            this.joystick.startPos = {
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2
            };
        });

        document.addEventListener('touchmove', (e) => {
            if (this.joystick.active) {
                e.preventDefault();
                const touch = e.touches[0];
                const dx = touch.clientX - this.joystick.startPos.x;
                const dy = touch.clientY - this.joystick.startPos.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const maxDistance = 40;

                if (distance <= maxDistance) {
                    this.joystick.currentPos = { x: dx, y: dy };
                } else {
                    this.joystick.currentPos = {
                        x: (dx / distance) * maxDistance,
                        y: (dy / distance) * maxDistance
                    };
                }

                // Update knob position
                joystickKnob.style.transform = `translate(calc(-50% + ${this.joystick.currentPos.x}px), calc(-50% + ${this.joystick.currentPos.y}px))`;

                // Calculate movement
                this.movement.x = this.joystick.currentPos.x / maxDistance;
                this.movement.y = this.joystick.currentPos.y / maxDistance;
            }
        });

        document.addEventListener('touchend', (e) => {
            if (this.joystick.active) {
                this.joystick.active = false;
                this.joystick.currentPos = { x: 0, y: 0 };
                this.movement = { x: 0, y: 0 };
                joystickKnob.style.transform = 'translate(-50%, -50%)';
            }
        });

        // Shoot button
        shootButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (!this.gameOver && this.canShoot) {
                this.shoot();
            }
        });

    }

    updateMovement() {
        if (this.gameOver || this.game_paused || !this.myPlayerId || !this.players[this.myPlayerId]) return;

        const player = this.players[this.myPlayerId];
        let dx = 0, dy = 0;
        let moved = false;

        if (this.isMobile) {
            dx = this.movement.x;
            dy = this.movement.y;
        } else {
            if (this.keys['w'] || this.keys['arrowup']) dy = -1;
            if (this.keys['s'] || this.keys['arrowdown']) dy = 1;
            if (this.keys['a'] || this.keys['arrowleft']) dx = -1;
            if (this.keys['d'] || this.keys['arrowright']) dx = 1;
        }

        if (dx !== 0 || dy !== 0) {
            const speed = 5;
            const newX = player.x + dx * speed;
            const newY = player.y + dy * speed;

            // Keep player on screen
            player.x = Math.max(20, Math.min(1004, newX));
            player.y = Math.max(20, Math.min(748, newY));
            moved = true;
        }

        // Update angle towards mouse/center
        let targetX, targetY;
        if (this.isMobile) {
            targetX = this.canvas.width / 2;
            targetY = this.canvas.height / 2;
        } else {
            targetX = this.mousePos.x;
            targetY = this.mousePos.y;
        }

        const newAngle = Math.atan2(targetY - player.y, targetX - player.x);
        const angleChanged = Math.abs(newAngle - player.angle) > 0.01;
        player.angle = newAngle;

        // Send movement to server only if something changed
        if ((moved || angleChanged) && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'move',
                x: player.x,
                y: player.y,
                angle: player.angle
            }));
        }
    }

    shoot() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'shoot'
            }));
        }
    }

    updateCooldown() {
        if (!this.canShoot) {
            const remaining = Math.max(0, this.cooldownEndTime - Date.now() / 1000);
            if (remaining > 0) {
                document.getElementById('cooldown').style.display = 'block';
                document.getElementById('cooldownText').textContent = `Cooldown: ${remaining.toFixed(1)}s`;
            }
        }
    }

    updatePlayerInfo() {
        if (this.myPlayerId && this.players[this.myPlayerId]) {
            const player = this.players[this.myPlayerId];
            document.getElementById('playerId').textContent = `Player: ${this.myPlayerId}`;
            document.getElementById('lives').textContent = `Lives: ${player.lives}`;
            document.getElementById('health').textContent = `Health: ${player.health}`;
        }

        // Update player count
        const playerCount = Object.keys(this.players).length;
        this.updateStatus(`Connected - Players: ${playerCount}`, '#00ff00');
    }

    updateStatus(text, color) {
        const statusElement = document.getElementById('status');
        statusElement.textContent = text;
        statusElement.style.color = color;
    }

    showGameOver(isWinner) {
        const gameOverScreen = document.getElementById('gameOverScreen');
        const gameOverText = document.getElementById('gameOverText');

        gameOverText.textContent = isWinner ? 'YOU WIN!' : 'YOU LOSE!';
        gameOverText.style.color = isWinner ? '#ffdd44' : '#ff4444';
        gameOverScreen.style.display = 'flex';
    }


    updateBullets() {
        // Don't update bullets if game is paused
        if (this.game_paused) return;

        // Update bullet positions client-side for smooth movement
        for (const bullet of Object.values(this.bullets)) {
            bullet.x += Math.cos(bullet.angle) * 10;
            bullet.y += Math.sin(bullet.angle) * 10;

            // Remove bullets that go off-screen
            if (bullet.x < 0 || bullet.x > 1024 || bullet.y < 0 || bullet.y > 768) {
                delete this.bullets[bullet.id];
            }
        }
    }

    updatePause() {
        if (this.game_paused && this.pause_countdown > 0) {
            this.pause_countdown -= 1/60; // Decrease by frame time
            if (this.pause_countdown <= 0) {
                this.pause_countdown = 0;
            }
        }
    }

    render() {
        // Clear canvas
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw players
        for (const [playerId, player] of Object.entries(this.players)) {
            if (!player.alive) continue;

            // Draw player circle
            this.ctx.fillStyle = `rgb(${player.color[0]}, ${player.color[1]}, ${player.color[2]})`;
            this.ctx.beginPath();
            this.ctx.arc(player.x, player.y, 20, 0, Math.PI * 2);
            this.ctx.fill();

            // Highlight own player
            if (playerId === this.myPlayerId) {
                this.ctx.strokeStyle = '#fff';
                this.ctx.lineWidth = 3;
                this.ctx.beginPath();
                this.ctx.arc(player.x, player.y, 23, 0, Math.PI * 2);
                this.ctx.stroke();
            }

            // Draw direction indicator
            this.ctx.strokeStyle = '#fff';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.moveTo(player.x, player.y);
            this.ctx.lineTo(
                player.x + Math.cos(player.angle) * 30,
                player.y + Math.sin(player.angle) * 30
            );
            this.ctx.stroke();

            // Draw health bar
            const barWidth = 40;
            const barHeight = 6;
            const barX = player.x - barWidth / 2;
            const barY = player.y - 35;

            this.ctx.fillStyle = '#ff0000';
            this.ctx.fillRect(barX, barY, barWidth, barHeight);
            this.ctx.fillStyle = '#00ff00';
            this.ctx.fillRect(barX, barY, barWidth * (player.health / 100), barHeight);

            // Draw lives
            for (let i = 0; i < player.lives; i++) {
                this.ctx.fillStyle = '#fff';
                this.ctx.beginPath();
                this.ctx.arc(player.x - 15 + (i * 10), player.y - 45, 3, 0, Math.PI * 2);
                this.ctx.fill();
            }

            // Draw player ID
            this.ctx.fillStyle = '#fff';
            this.ctx.font = '12px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(playerId, player.x, player.y + 40);
        }

        // Draw bullets
        this.ctx.fillStyle = '#ffff00';
        for (const bullet of Object.values(this.bullets)) {
            this.ctx.beginPath();
            this.ctx.arc(bullet.x, bullet.y, 3, 0, Math.PI * 2);
            this.ctx.fill();
        }

    }

    gameLoop() {
        this.updateMovement();
        this.updateBullets();
        this.updatePause();
        this.updateCooldown();
        this.render();
        requestAnimationFrame(() => this.gameLoop());
    }
}

// Play again function
function playAgain() {
    // Go back to lobby to create/join new room
    window.location.href = '/';
}

function quitGame() {
    // Disconnect from WebSocket and go back to lobby
    if (window.game && window.game.ws) {
        window.game.ws.close();
    }
    window.location.href = '/';
}

// Start the game when page loads
window.addEventListener('load', () => {
    window.game = new CircleStrikeGame();
});