# CircleStrike - Multiplayer Shooter Game

A real-time multiplayer 2D shooter game built with Python and Pygame.

## Features

- **Real-time multiplayer gameplay** - Multiple players can join and play simultaneously
- **Smooth movement and aiming** - WASD movement with mouse aiming
- **Shooting mechanics** - Left-click to shoot bullets
- **Health system** - Players have health bars that decrease when hit
- **Player identification** - Each player has a unique ID and color
- **Networked synchronization** - All player movements and shots are synchronized across clients

## Requirements

- Python 3.7+
- Pygame 2.5.2+

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## How to Play

### Starting a Game

1. **Start the Server:**
   ```bash
   python server.py
   ```

2. **Connect Clients:**
   ```bash
   python client.py
   ```
   Run this command in separate terminals for each player.

3. **Local Testing:**
   For single-player testing:
   ```bash
   python game.py
   ```

### Controls

- **Movement:** WASD or Arrow Keys
- **Aiming:** Mouse cursor
- **Shooting:** Left mouse click
- **Quit:** Close window or Alt+F4

### Gameplay

- Players spawn with 100 health points
- Each bullet hit deals 25 damage
- When a player's health reaches 0, they respawn at the center
- Players are represented by colored circles with health bars
- Your player has a white outline for identification

## Network Architecture

- **Client-Server Model:** Authoritative server handles game state
- **TCP Sockets:** Reliable connection for game messages
- **JSON Protocol:** Simple message format for client-server communication
- **Real-time Sync:** Player positions and shots synchronized at 60 FPS

## File Structure

```
circlestrike/
├── game.py           # Single-player version for testing
├── server.py         # Game server
├── client.py         # Multiplayer client
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Technical Details

### Server (server.py)
- Handles client connections and disconnections
- Manages game state (players, bullets)
- Broadcasts updates to all connected clients
- Runs game loop at 60 FPS

### Client (client.py)
- Connects to game server
- Handles local input and rendering
- Sends player actions to server
- Receives and applies game state updates

### Game Logic (game.py)
- Core game classes (Player, Bullet)
- Single-player version for testing
- Physics and collision detection

## Extending the Game

The game is designed to be easily extensible. Some ideas:

- **Power-ups:** Add special items that enhance player abilities
- **Different weapons:** Implement various weapon types
- **Game modes:** Add team deathmatch, capture the flag, etc.
- **Maps:** Create different levels with obstacles
- **Audio:** Add sound effects and music
- **Graphics:** Improve visual assets and animations

## Troubleshooting

### Connection Issues
- Ensure server is running before connecting clients
- Check firewall settings for the specified port
- Verify host and port configuration

### Performance Issues
- Lower FPS if experiencing lag
- Check network latency between clients and server
- Ensure Python and Pygame are up to date

### Installation Issues
- Use `pip install --upgrade pygame` for latest version
- Try `python -m pip install pygame` if regular pip fails
- Ensure Python 3.7+ is being used

## Documentation

- **[Developer Guide](DEVELOPER_GUIDE.md)** - Technical documentation and architecture
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](CHANGELOG.md)** - Version history and planned features

## Development

### For Developers
If you want to contribute or modify the game, check out the comprehensive documentation:

- **Architecture**: Client-server with TCP networking and JSON protocol
- **Adding Features**: Detailed guides for adding new game mechanics
- **Code Structure**: Well-documented classes and functions
- **Testing**: Guidelines for testing multiplayer functionality

### Future Features
- Power-ups (speed boost, rapid fire, shield)
- Different maps with obstacles
- Team-based gameplay modes
- Sound effects and music
- Better graphics and animations
- Server browser
- Statistics tracking

See [CHANGELOG.md](CHANGELOG.md) for the complete roadmap.

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to set up development environment
- Code style guidelines
- Pull request process
- Issue reporting guidelines

## License

This project is open source and available under the MIT License. See [LICENSE](LICENSE) for details.