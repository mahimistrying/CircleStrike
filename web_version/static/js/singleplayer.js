// CircleStrike Single Player Game Client with Bots
class SinglePlayerGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.players = {};
        this.bullets = {};
        this.myPlayerId = 'player';
        this.gameOver = false;
        this.canShoot = true;
        this.cooldownEndTime = 0;
        this.bulletId = 0;
        this.botId = 0;

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
        this.pause_countdown = 0;

        // Bot AI settings
        this.bots = {};
        this.botCount = 3;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializePlayers();
        this.gameLoop();
        this.updateStatus('Ready to fight!', '#00ff00');

        if (this.isMobile) {
            this.setupMobileControls();
        }
    }

    initializePlayers() {
        // Add player
        this.players[this.myPlayerId] = {
            id: this.myPlayerId,
            x: 100,
            y: 100,
            angle: 0,
            health: 100,
            lives: 3,
            alive: true,
            color: '#00ff00'
        };

        // Add bots
        for (let i = 0; i < this.botCount; i++) {
            const botId = `bot${i}`;
            this.players[botId] = {
                id: botId,
                x: Math.random() * 800 + 100,
                y: Math.random() * 600 + 100,
                angle: Math.random() * Math.PI * 2,
                health: 100,
                lives: 3,
                alive: true,
                color: '#ff4444'
            };

            // Bot AI properties
            this.bots[botId] = {
                targetX: Math.random() * 800 + 100,
                targetY: Math.random() * 600 + 100,
                lastShot: 0,
                lastTargetChange: Date.now(),
                shootingAt: null,
                difficulty: 0.7 + Math.random() * 0.3 // 0.7-1.0 difficulty
            };
        }

        this.updatePlayerInfo();
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
            if (!this.gameOver && this.canShoot && this.players[this.myPlayerId].alive) {
                this.shoot();
            }
        });
    }

    setupMobileControls() {
        const mobileControls = document.getElementById('mobileControls');
        const joystick = document.getElementById('joystick');
        const shootButton = document.getElementById('shootButton');

        mobileControls.style.display = 'block';

        // Joystick events
        joystick.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const rect = joystick.getBoundingClientRect();
            this.joystick.active = true;
            this.joystick.startPos = {
                x: touch.clientX - rect.left - rect.width / 2,
                y: touch.clientY - rect.top - rect.height / 2
            };
        });

        joystick.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (!this.joystick.active) return;

            const touch = e.touches[0];
            const rect = joystick.getBoundingClientRect();
            this.joystick.currentPos = {
                x: touch.clientX - rect.left - rect.width / 2,
                y: touch.clientY - rect.top - rect.height / 2
            };

            // Limit to circle
            const distance = Math.sqrt(this.joystick.currentPos.x ** 2 + this.joystick.currentPos.y ** 2);
            const maxDistance = 50;
            if (distance > maxDistance) {
                this.joystick.currentPos.x = (this.joystick.currentPos.x / distance) * maxDistance;
                this.joystick.currentPos.y = (this.joystick.currentPos.y / distance) * maxDistance;
            }

            // Update movement
            this.movement.x = this.joystick.currentPos.x / maxDistance;
            this.movement.y = this.joystick.currentPos.y / maxDistance;
        });

        joystick.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.joystick.active = false;
            this.joystick.currentPos = { x: 0, y: 0 };
            this.movement = { x: 0, y: 0 };
        });

        // Shoot button
        shootButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (!this.gameOver && this.canShoot && this.players[this.myPlayerId].alive) {
                this.shoot();
            }
        });
    }

    updateInput() {
        if (!this.players[this.myPlayerId] || !this.players[this.myPlayerId].alive) return;

        let moveX = 0;
        let moveY = 0;

        // Keyboard movement
        if (this.keys['w'] || this.keys['arrowup']) moveY -= 1;
        if (this.keys['s'] || this.keys['arrowdown']) moveY += 1;
        if (this.keys['a'] || this.keys['arrowleft']) moveX -= 1;
        if (this.keys['d'] || this.keys['arrowright']) moveX += 1;

        // Mobile movement
        if (this.joystick.active) {
            moveX = this.movement.x;
            moveY = this.movement.y;
        }

        // Update player position
        const player = this.players[this.myPlayerId];
        const speed = 300;
        const deltaTime = 1/60;

        player.x += moveX * speed * deltaTime;
        player.y += moveY * speed * deltaTime;

        // Keep player in bounds
        player.x = Math.max(20, Math.min(1004, player.x));
        player.y = Math.max(20, Math.min(748, player.y));

        // Update player angle to face mouse
        const dx = this.mousePos.x - player.x;
        const dy = this.mousePos.y - player.y;
        player.angle = Math.atan2(dy, dx);
    }

    updateBots() {
        const now = Date.now();

        for (const botId in this.bots) {
            const bot = this.players[botId];
            const botAI = this.bots[botId];

            if (!bot.alive) continue;

            // Find closest enemy (player)
            let closestEnemy = null;
            let closestDistance = Infinity;

            for (const playerId in this.players) {
                const player = this.players[playerId];
                if (playerId === botId || !player.alive) continue;

                const dx = player.x - bot.x;
                const dy = player.y - bot.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < closestDistance) {
                    closestDistance = distance;
                    closestEnemy = player;
                }
            }

            if (closestEnemy) {
                // Face the enemy
                const dx = closestEnemy.x - bot.x;
                const dy = closestEnemy.y - bot.y;
                bot.angle = Math.atan2(dy, dx);

                // Shoot at enemy if close enough and not on cooldown
                if (closestDistance < 300 && now - botAI.lastShot > 1000 / botAI.difficulty) {
                    this.botShoot(botId);
                    botAI.lastShot = now;
                }

                // Move strategy: if too close, back away; if too far, approach
                let moveX = 0;
                let moveY = 0;

                if (closestDistance < 150) {
                    // Back away
                    moveX = -(dx / closestDistance);
                    moveY = -(dy / closestDistance);
                } else if (closestDistance > 250) {
                    // Approach
                    moveX = dx / closestDistance;
                    moveY = dy / closestDistance;
                } else {
                    // Strafe around enemy
                    moveX = -dy / closestDistance;
                    moveY = dx / closestDistance;
                }

                // Add some randomness to movement
                moveX += (Math.random() - 0.5) * 0.3;
                moveY += (Math.random() - 0.5) * 0.3;

                // Move bot
                const speed = 200 * botAI.difficulty;
                const deltaTime = 1/60;

                bot.x += moveX * speed * deltaTime;
                bot.y += moveY * speed * deltaTime;

                // Keep bot in bounds
                bot.x = Math.max(20, Math.min(1004, bot.x));
                bot.y = Math.max(20, Math.min(748, bot.y));
            }
        }
    }

    shoot() {
        const player = this.players[this.myPlayerId];
        if (!player || !player.alive) return;

        const bulletId = `bullet_${this.bulletId++}`;
        this.bullets[bulletId] = {
            id: bulletId,
            x: player.x,
            y: player.y,
            angle: player.angle,
            speed: 500,
            owner_id: this.myPlayerId,
            active: true
        };

        this.canShoot = false;
        this.cooldownEndTime = Date.now() + 500;
        this.updateCooldown();
    }

    botShoot(botId) {
        const bot = this.players[botId];
        if (!bot || !bot.alive) return;

        const bulletId = `bullet_${this.bulletId++}`;
        this.bullets[bulletId] = {
            id: bulletId,
            x: bot.x,
            y: bot.y,
            angle: bot.angle,
            speed: 500,
            owner_id: botId,
            active: true
        };
    }

    updateBullets() {
        for (const bulletId in this.bullets) {
            const bullet = this.bullets[bulletId];
            if (!bullet.active) continue;

            // Update bullet position
            bullet.x += Math.cos(bullet.angle) * bullet.speed * (1/60);
            bullet.y += Math.sin(bullet.angle) * bullet.speed * (1/60);

            // Check if bullet is off screen
            if (bullet.x < 0 || bullet.x > 1024 || bullet.y < 0 || bullet.y > 768) {
                bullet.active = false;
                delete this.bullets[bulletId];
                continue;
            }

            // Check collision with players
            for (const playerId in this.players) {
                const player = this.players[playerId];
                if (playerId === bullet.owner_id || !player.alive) continue;

                const dx = bullet.x - player.x;
                const dy = bullet.y - player.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 23) {
                    // Hit!
                    player.health -= 25;
                    bullet.active = false;
                    delete this.bullets[bulletId];

                    if (player.health <= 0) {
                        player.lives -= 1;
                        player.health = 100;

                        // Pause game for 2 seconds
                        this.game_paused = true;
                        this.pause_countdown = 2;

                        if (player.lives > 0) {
                            // Respawn
                            player.x = Math.random() * 800 + 100;
                            player.y = Math.random() * 600 + 100;
                        } else {
                            player.alive = false;
                        }

                        this.updatePlayerInfo();
                        this.checkWinCondition();
                    }
                    break;
                }
            }
        }
    }

    checkWinCondition() {
        const alivePlayers = Object.values(this.players).filter(p => p.alive);

        if (alivePlayers.length === 1) {
            this.gameOver = true;
            const winner = alivePlayers[0];

            if (winner.id === this.myPlayerId) {
                this.showGameOver('YOU WIN!', '#00ff00');
            } else {
                this.showGameOver('YOU LOSE!', '#ff0000');
            }
        } else if (alivePlayers.length === 0) {
            this.gameOver = true;
            this.showGameOver('DRAW!', '#ffff00');
        }
    }

    updateCooldown() {
        const cooldownDiv = document.getElementById('cooldown');
        const cooldownText = document.getElementById('cooldownText');

        if (!this.canShoot) {
            const timeLeft = Math.max(0, (this.cooldownEndTime - Date.now()) / 1000);
            if (timeLeft > 0) {
                cooldownDiv.style.display = 'block';
                cooldownText.textContent = `Cooldown: ${timeLeft.toFixed(1)}s`;
            } else {
                this.canShoot = true;
                cooldownDiv.style.display = 'none';
            }
        }
    }

    render() {
        // Clear canvas
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw players
        for (const playerId in this.players) {
            const player = this.players[playerId];
            if (!player.alive) continue;

            this.ctx.save();
            this.ctx.translate(player.x, player.y);
            this.ctx.rotate(player.angle);

            // Draw player body
            this.ctx.fillStyle = player.color;
            this.ctx.beginPath();
            this.ctx.arc(0, 0, 20, 0, Math.PI * 2);
            this.ctx.fill();

            // Draw cannon
            this.ctx.fillStyle = '#888';
            this.ctx.fillRect(15, -3, 15, 6);

            // Draw health bar
            this.ctx.restore();
            const barWidth = 40;
            const barHeight = 6;
            const healthPercent = player.health / 100;

            this.ctx.fillStyle = '#333';
            this.ctx.fillRect(player.x - barWidth/2, player.y - 35, barWidth, barHeight);

            this.ctx.fillStyle = healthPercent > 0.5 ? '#00ff00' : healthPercent > 0.25 ? '#ffff00' : '#ff0000';
            this.ctx.fillRect(player.x - barWidth/2, player.y - 35, barWidth * healthPercent, barHeight);

            // Draw lives
            this.ctx.fillStyle = '#fff';
            this.ctx.font = '12px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(`Lives: ${player.lives}`, player.x, player.y - 40);
        }

        // Draw bullets
        this.ctx.fillStyle = '#ffff00';
        for (const bulletId in this.bullets) {
            const bullet = this.bullets[bulletId];
            if (!bullet.active) continue;

            this.ctx.beginPath();
            this.ctx.arc(bullet.x, bullet.y, 3, 0, Math.PI * 2);
            this.ctx.fill();
        }

        // Draw pause overlay
        if (this.game_paused && this.pause_countdown > 0) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

            this.ctx.fillStyle = '#fff';
            this.ctx.font = '48px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('PAUSED', this.canvas.width / 2, this.canvas.height / 2);

            this.ctx.font = '24px Arial';
            this.ctx.fillText(`Resuming in ${this.pause_countdown.toFixed(1)}s`, this.canvas.width / 2, this.canvas.height / 2 + 50);
        }
    }

    gameLoop() {
        if (this.gameOver) return;

        // Update pause
        if (this.game_paused) {
            this.pause_countdown -= 1/60;
            if (this.pause_countdown <= 0) {
                this.game_paused = false;
            }
        } else {
            this.updateInput();
            this.updateBots();
            this.updateBullets();
        }

        this.updateCooldown();
        this.render();

        requestAnimationFrame(() => this.gameLoop());
    }

    updateStatus(message, color = '#ffffff') {
        const statusElement = document.getElementById('status');
        statusElement.textContent = message;
        statusElement.style.color = color;
    }

    updatePlayerInfo() {
        const player = this.players[this.myPlayerId];
        if (player) {
            document.getElementById('lives').textContent = `Lives: ${player.lives}`;
            document.getElementById('health').textContent = `Health: ${player.health}`;
        }
    }

    showGameOver(text, color) {
        document.getElementById('gameOverText').textContent = text;
        document.getElementById('gameOverText').style.color = color;
        document.getElementById('gameOverScreen').style.display = 'flex';
    }
}

// Play again function
function playAgain() {
    // Reload the single player game
    window.location.reload();
}

function quitGame() {
    // Go back to lobby
    window.location.href = '/';
}

// Start the game when page loads
window.addEventListener('load', () => {
    window.game = new SinglePlayerGame();
});