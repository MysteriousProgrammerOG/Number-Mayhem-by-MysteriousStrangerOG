# 🎮 NUMBER MAYHEM

**The Ultimate Number Guessing Game** — now available as both a terminal game and a web game!

Guess the secret number, earn coins, buy items, build streaks, and unlock achievements. The web version features a futuristic hacker-terminal interface powered by Python (FastAPI) on the backend and HTML/CSS/JavaScript on the frontend.

---

## 📋 What Is Number Mayhem?

Number Mayhem is a number-guessing game with a full game economy:

- **6 Difficulties**: Baby, Easy, Normal, Hard, Extreme, and Impossible (with decimals!)
- **Coin Economy**: Win games to earn coins, spend them in the shop
- **6 Shop Items**: Hint, Free Guess, Reveal Digit, Double Reward, Lucky Guess, Streak Shield
- **Win Streaks**: Build streaks for bigger rewards (up to ×2.0 multiplier)
- **12 Achievements**: Unlock achievements as you progress
- **Persistent Save**: Your progress is saved automatically

---

## 📁 Project Structure

```
NUMBER-MAYHEM/
├── backend/
│   ├── __init__.py       # Marks backend as a Python package
│   ├── main.py           # FastAPI server + all API endpoints
│   ├── game.py           # GameSession class (core game logic)
│   ├── player.py         # Player class (data + shop + achievements)
│   ├── constants.py      # Game definitions (difficulties, items, achievements)
│   └── database.py       # SQLite persistence layer
├── frontend/
│   ├── index.html        # Game interface (HTML)
│   ├── style.css         # Hacker terminal theme (CSS)
│   └── script.js         # Frontend logic (JavaScript)
├── tests/
│   └── test_game.py      # Backend game logic tests
├── Number Mahem.py       # Original terminal version (refactored to use shared logic)
├── requirements.txt      # Python dependencies
├── .gitignore            # Files to exclude from version control
└── README.md             # This file
```

---

## 🚀 How to Run Locally

### 1. Install Python Dependencies

Open a terminal in the `NUMBER-MAYHEM` folder and run:

```bash
pip install -r requirements.txt
```

This installs:
- **fastapi** — the web framework for the backend
- **uvicorn** — the server that runs FastAPI
- **pytest** — for running tests

### 2. Run the Web Game

```bash
uvicorn backend.main:app --reload
```

Then open your browser and go to:

```
http://localhost:8000
```

You should see the boot sequence, then the main game interface.

### 3. Run the Terminal Game

```bash
python "Number Mahem.py"
```

This runs the original terminal version, now using the same shared game logic as the web version.

### 4. Run the Tests

```bash
pytest tests/test_game.py
```

This runs all the backend game logic tests to make sure everything works correctly.

# 5. The Website

If you don't want to have to do all the above steps, you can simply visit https://number-mayhem-by-mysteriousstrangerog.onrender.com/ to play! 

---

## 🌐 How the Frontend Communicates with the Backend

The frontend (HTML/CSS/JavaScript) never makes game decisions. It only **displays** what the backend tells it.

Here's how a guess works:

1. You type a guess and click **EXECUTE**
2. JavaScript sends the guess to the backend: `POST /api/game/guess`
3. The Python backend validates the guess and decides if it's correct, too high, or too low
4. The backend updates the game state and player data
5. The backend returns the result as JSON
6. JavaScript displays the result in the terminal

**Important**: The secret number is generated and stored **only on the server**. It is never sent to the browser until the game ends.

### API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the game page |
| `/api/player` | GET | Get player data (coins, stats, inventory) |
| `/api/shop` | GET | Get shop items and inventory |
| `/api/shop/buy` | POST | Buy an item (server validates coins) |
| `/api/achievements` | GET | Get all achievements with unlock status |
| `/api/stats` | GET | Get all player statistics |
| `/api/game/start` | POST | Start a new game (server generates secret number) |
| `/api/game/guess` | POST | Make a guess (server decides result) |
| `/api/game/use-item` | POST | Use an item (server validates ownership) |
| `/api/game/state` | GET | Get current game state (no secret number) |

---

## 💾 How Player Data Works

Player data is stored in a **SQLite database** file called `players.db` in the project root.

The database is created automatically on first run. It stores the player's:
- Coins and total coins earned
- Games won/lost
- Win streak and highest streak
- Perfect games
- Items used
- Inventory (all 6 items)
- Achievements
- Difficulty wins
- Special stats (streak shield wins, lucky guess wins, etc.)

The persistence layer is in `backend/database.py`. It's designed so it can be swapped for PostgreSQL later without changing the game logic.

---

## 🧠 Understanding the Code

### Backend (Python)

- **`constants.py`** — All the game definitions. These are copied exactly from the original terminal game. If you want to change a difficulty, item cost, or achievement, this is where you do it.
- **`game.py`** — The `GameSession` class. This is the heart of the game. It handles generating the secret number, validating guesses, tracking attempts, using items, and calculating rewards.
- **`player.py`** — The `Player` class. Handles player data, shop purchases, and achievement checks.
- **`database.py`** — SQLite connection and save/load functions.
- **`main.py`** — The FastAPI server. Defines all the API endpoints and serves the frontend files.

### Frontend (HTML/CSS/JavaScript)

- **`index.html`** — The structure of the page. Contains the boot screen, main game interface, and modal panels for shop/inventory/stats/achievements.
- **`style.css`** — The visual theme. Dark background, green/cyan terminal colors, CRT scanlines, glowing text.
- **`script.js`** — The browser logic. Uses `fetch()` to call the backend API. Heavily commented so you can learn how it works.

---

## 🚢 How to Deploy for Free

### Option 1: Render.com (Recommended)

1. Create a free account at [render.com](https://render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository (or upload the project)
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**

Render's free tier includes:
- A free web service (spins down after 15 min of inactivity)
- A free SQLite database (stored on the service's disk)

### Option 2: PythonAnywhere

1. Create a free account at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload the project files
3. Create a new web app with **Manual configuration** and **Python 3.x**
4. In the WSGI configuration file, point to `backend.main:app`
5. Install dependencies with `pip install -r requirements.txt`

### Option 3: Railway

1. Create a free account at [railway.app](https://railway.app)
2. Create a new project and deploy from GitHub
3. Set the start command to: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

---

## 🔧 How to Make Future Changes

### Change a Difficulty

Edit `backend/constants.py`:

```python
"normal": {
    "name": "Normal",
    "icon": "🟡",
    "low": 1,
    "high": 1000,
    "attempts": 10,
    "base_reward": 50,
    "decimals": False,
    "description": "1 - 1,000, the classic challenge."
}
```

### Change an Item Cost

Edit `backend/constants.py`:

```python
"hint": {
    "name": "Hint",
    "icon": "🔮",
    "cost": 50,  # Change this number
    "description": "Reveals a clue about the number (even/odd, range, or digit)."
}
```

### Add a New Achievement

Edit `backend/constants.py`:

```python
"my_new_achievement": {
    "name": "My Achievement",
    "icon": "🌟",
    "description": "What you need to do to unlock it.",
    "condition": lambda p: p["games_won"] >= 50  # The unlock condition
}
```

### Change the Visual Theme

Edit `frontend/style.css`. The colors are defined at the top in the `:root` section:

```css
:root {
    --bg-primary: #0a0e14;      /* Main background */
    --green: #00ff9d;           /* Primary accent color */
    --cyan: #00d4ff;            /* Secondary accent color */
    --gold: #ffd700;            /* Coin color */
    --red: #ff4757;             /* Error color */
}
```

---

## 🎮 Gameplay Details

### Difficulties

| Difficulty | Range | Attempts | Base Reward | Decimals |
|---|---|---|---|---|
| 👶 Baby | 1–10 | 10 | 5 🪙 | No |
| 🟢 Easy | 1–50 | 8 | 15 🪙 | No |
| 🟡 Normal | 1–1,000 | 10 | 50 🪙 | No |
| 🔴 Hard | 1–10,000 | 8 | 150 🪙 | No |
| ☠️ Extreme | 1–1,000,000 | 10 | 1,000 🪙 | No |
| 💀 Impossible | 0.1–10,000 | 5 | 10,000 🪙 | **Yes** |

### Shop Items

| Item | Cost | Effect |
|---|---|---|
| 🔮 Hint | 50 🪙 | Reveals even/odd, a range, or a digit |
| 🎟️ Free Guess | 100 🪙 | Guess without using an attempt |
| 🔍 Reveal Digit | 250 🪙 | Shows one digit like `_ 3 _ _` |
| 💰 Double Reward | 500 🪙 | Doubles your win payout |
| 🎲 Lucky Guess | 750 🪙 | Auto-guesses with 50% hit chance |
| 🛡️ Streak Shield | 300 🪙 | Protects your streak from a loss |

### Reward Formula

```
Total = (Base + AttemptsBonus + PerfectBonus) × StreakMultiplier × DoubleReward
```

- **AttemptsBonus**: +2 coins per unused attempt
- **PerfectBonus**: +50% of base reward (guessed on first attempt)
- **StreakMultiplier**: 1.0 + 0.1 per 2 wins, capped at 2.0
- **DoubleReward**: ×2 if the item was used

### Achievements

| Achievement | Condition |
|---|---|
| 🩸 First Blood | Win your first game |
| 🚀 Getting Started | Win 10 games |
| 💎 Millionaire | Earn 1,000,000 total coins |
| 💀 Impossible | Beat Impossible difficulty |
| 🧠 Insanity | Beat Impossible without using items |
| 🎯 Perfectionist | Guess on your first attempt |
| 🔥 Fortune's Favorite | Win 10 games consecutively |
| 🤖 The Machine | Win 100 games |
| 🛡️ Survivor | Win using Streak Shield |
| 🎲 Gambler | Win using Lucky Guess |
| 🧪 Item Master | Use 25 items total |
| 👑 Number God | Win on Extreme or Impossible 5 times |

---

## 🛡️ Security Notes

The browser is treated as **untrusted**. All game decisions happen on the Python backend:

- The secret number is generated and stored **server-side only**
- The server validates every guess
- The server calculates all rewards
- The server verifies item ownership before use
- The server verifies coin balance before purchases
- The server decides achievement unlocks

The frontend only displays what the server tells it. This means players cannot cheat by modifying browser code.

---

## 📝 License

This project is for learning and personal use. Feel free to modify and expand it!
