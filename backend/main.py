# main.py
# FastAPI backend for Number Mayhem.
# This server:
#   - Serves the frontend (index.html, style.css, script.js)
#   - Handles all game logic through API endpoints
#   - Validates everything server-side (never trust the browser!)
#   - Stores the secret number server-side only
#
# Run with:  uvicorn backend.main:app --reload

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .constants import DIFFICULTIES, SHOP_ITEMS
from .game import GameSession
from .player import Player

# Project root is one level up from the backend/ folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(title="Number Mayhem")

# Global game state
player = Player()          # The single local player
current_session = None     # The active game session (None when no game is running)

# ============================================================
# REQUEST MODELS (validated by FastAPI/Pydantic)
# ============================================================

class StartGameRequest(BaseModel):
    difficulty: str

class GuessRequest(BaseModel):
    guess: float

class UseItemRequest(BaseModel):
    item_id: str

class BuyItemRequest(BaseModel):
    item_id: str

# ============================================================
# FRONTEND STATIC FILES
# ============================================================

# Serve the frontend files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_index():
    """Serve the main game page."""
    return FileResponse(FRONTEND_DIR / "index.html")


# ============================================================
# PLAYER ENDPOINTS
# ============================================================

@app.get("/api/player")
def get_player():
    """Return the player's data (safe to show in the browser)."""
    return player.get_public_data()


@app.get("/api/shop")
def get_shop():
    """Return the shop items with the player's current inventory counts."""
    return {
        "items": SHOP_ITEMS,
        "inventory": player.get_inventory(),
        "coins": player.data["coins"]
    }


@app.post("/api/shop/buy")
def buy_item(request: BuyItemRequest):
    """Purchase an item from the shop.
    The server verifies the item exists and the player has enough coins.
    """
    success, message = player.buy_item(request.item_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "player": player.get_public_data()
    }


@app.get("/api/achievements")
def get_achievements():
    """Return all achievements with their unlocked status."""
    return {
        "achievements": player.get_all_achievements(),
        "unlocked_ids": player.get_achievements()
    }


@app.get("/api/stats")
def get_stats():
    """Return all player statistics."""
    return player.get_public_data()


# ============================================================
# GAME ENDPOINTS
# ============================================================

@app.post("/api/game/start")
def start_game(request: StartGameRequest):
    """Start a new game session.
    The secret number is generated and stored SERVER-SIDE.
    It is never sent to the browser.
    """
    global current_session

    if request.difficulty not in DIFFICULTIES:
        raise HTTPException(status_code=400, detail="Unknown difficulty.")

    # Start a new game session
    current_session = GameSession(player, request.difficulty)

    return {
        "success": True,
        "message": f"Game started on {DIFFICULTIES[request.difficulty]['name']} difficulty.",
        "state": current_session.get_public_state()
    }


@app.post("/api/game/guess")
def make_guess(request: GuessRequest):
    """Process a player's guess.
    The server validates the guess and determines the result.
    The browser never decides if a guess is correct.
    """
    global current_session

    if current_session is None:
        raise HTTPException(status_code=400, detail="No active game. Start a game first.")

    result = current_session.make_guess(request.guess)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/api/game/use-item")
def use_item(request: UseItemRequest):
    """Use an item during the game.
    The server verifies the player owns the item.
    """
    global current_session

    if current_session is None:
        raise HTTPException(status_code=400, detail="No active game. Start a game first.")

    result = current_session.use_item(request.item_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.get("/api/game/state")
def get_game_state():
    """Return the current game state (without the secret number)."""
    global current_session

    if current_session is None:
        return {"active": False}

    return {
        "active": True,
        "state": current_session.get_public_state()
    }