# CircleStrike v1.2 - Web Version

Real-time multiplayer 2D shooter game with custom room system.

## 🎮 Features

- **Custom Room Codes**: Create rooms with easy codes like "CAT", "DOG", "123"
- **Real-time Multiplayer**: Play with friends worldwide via WebSockets
- **Mobile Support**: Touch controls for mobile devices
- **Lives System**: 3 lives per player with 2-second pause on death
- **Professional UI**: Modern lobby and game interface

## 🚀 Live Demo

Deploy this to any free hosting platform:

### Railway (Recommended)
1. Connect GitHub repo to Railway
2. Deploy from `web_version` folder
3. Automatic deployments on push

### Render
1. Connect GitHub repo to Render
2. Use `web_version` as root directory
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Heroku
1. `heroku create your-app-name`
2. `git subtree push --prefix=web_version heroku main`

## 🎯 How to Play

1. **Create Room**: Enter custom code (CAT, DOG) or leave empty for random
2. **Share Code**: Give room code to friends
3. **Join Room**: Friends enter code to join
4. **Play**: WASD to move, mouse to aim, click to shoot

## 🔧 Local Development

```bash
cd web_version
pip install -r requirements.txt
python main.py
```

Visit `http://localhost:8080`

## 📱 Mobile Support

- Touch joystick for movement
- Tap button for shooting
- Responsive design for all screen sizes

## 🌟 Portfolio Ready

Perfect for showcasing:
- Real-time networking with WebSockets
- FastAPI backend development
- HTML5 Canvas game development
- Mobile-responsive design
- Room management systems