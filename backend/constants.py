# constants.py
# Shared game definitions for Number Mayhem.
# These values are copied EXACTLY from the original terminal game.
# Both the terminal version and the web version use these same definitions.

# ============================================================
# DIFFICULTY DEFINITIONS
# ============================================================

DIFFICULTIES = {
    "baby": {
        "name": "Baby",
        "icon": "👶",
        "low": 1,
        "high": 10,
        "attempts": 10,
        "base_reward": 5,
        "decimals": False,
        "description": "1 - 10, super easy!"
    },
    "easy": {
        "name": "Easy",
        "icon": "🟢",
        "low": 1,
        "high": 50,
        "attempts": 8,
        "base_reward": 15,
        "decimals": False,
        "description": "1 - 50, a gentle warm-up."
    },
    "normal": {
        "name": "Normal",
        "icon": "🟡",
        "low": 1,
        "high": 1000,
        "attempts": 10,
        "base_reward": 50,
        "decimals": False,
        "description": "1 - 1,000, the classic challenge."
    },
    "hard": {
        "name": "Hard",
        "icon": "🔴",
        "low": 1,
        "high": 10000,
        "attempts": 8,
        "base_reward": 150,
        "decimals": False,
        "description": "1 - 10,000, for serious players."
    },
    "extreme": {
        "name": "Extreme",
        "icon": "☠️",
        "low": 1,
        "high": 1000000,
        "attempts": 10,
        "base_reward": 1000,
        "decimals": False,
        "description": "1 - 1,000,000, only the brave."
    },
    "impossible": {
        "name": "Impossible",
        "icon": "💀",
        "low": 0.1,
        "high": 10000,
        "attempts": 5,
        "base_reward": 10000,
        "decimals": True,
        "description": "0.1 - 10,000 with decimals. Good luck."
    }
}

# ============================================================
# SHOP ITEMS
# ============================================================

SHOP_ITEMS = {
    "hint": {
        "name": "Hint",
        "icon": "🔮",
        "cost": 50,
        "description": "Reveals a clue about the number (even/odd, range, or digit)."
    },
    "free_guess": {
        "name": "Free Guess",
        "icon": "🎟️",
        "cost": 100,
        "description": "Make a guess without using an attempt."
    },
    "reveal_digit": {
        "name": "Reveal Digit",
        "icon": "🔍",
        "cost": 250,
        "description": "Reveals one digit of the secret number."
    },
    "double_reward": {
        "name": "Double Reward",
        "icon": "💰",
        "cost": 500,
        "description": "Doubles the coins you earn on a win."
    },
    "lucky_guess": {
        "name": "Lucky Guess",
        "icon": "🎲",
        "cost": 750,
        "description": "Auto-guesses a random number (50% chance to be correct)."
    },
    "streak_shield": {
        "name": "Streak Shield",
        "icon": "🛡️",
        "cost": 300,
        "description": "Protects your win streak from one loss."
    }
}

# ============================================================
# ACHIEVEMENTS
# ============================================================

ACHIEVEMENTS = {
    "first_blood": {
        "name": "First Blood",
        "icon": "🩸",
        "description": "Win your first game.",
        "condition": lambda p: p["games_won"] >= 1
    },
    "getting_started": {
        "name": "Getting Started",
        "icon": "🚀",
        "description": "Win 10 games.",
        "condition": lambda p: p["games_won"] >= 10
    },
    "millionaire": {
        "name": "Millionaire",
        "icon": "💎",
        "description": "Earn 1,000,000 total coins.",
        "condition": lambda p: p["total_coins_earned"] >= 1000000
    },
    "impossible_winner": {
        "name": "Impossible",
        "icon": "💀",
        "description": "Beat Impossible difficulty.",
        "condition": lambda p: p["difficulty_wins"].get("impossible", 0) >= 1
    },
    "insanity": {
        "name": "Insanity",
        "icon": "🧠",
        "description": "Beat Impossible without using items.",
        "condition": lambda p: p["difficulty_wins"].get("impossible", 0) >= 1 and p.get("impossible_no_items", False)
    },
    "perfectionist": {
        "name": "Perfectionist",
        "icon": "🎯",
        "description": "Guess the number on your first attempt.",
        "condition": lambda p: p["perfect_games"] >= 1
    },
    "fortunes_favorite": {
        "name": "Fortune's Favorite",
        "icon": "🔥",
        "description": "Win 10 games consecutively.",
        "condition": lambda p: p["highest_streak"] >= 10
    },
    "the_machine": {
        "name": "The Machine",
        "icon": "🤖",
        "description": "Win 100 games.",
        "condition": lambda p: p["games_won"] >= 100
    },
    "survivor": {
        "name": "Survivor",
        "icon": "🛡️",
        "description": "Win a game using Streak Shield.",
        "condition": lambda p: p.get("streak_shield_wins", 0) >= 1
    },
    "gambler": {
        "name": "Gambler",
        "icon": "🎲",
        "description": "Win a game using Lucky Guess.",
        "condition": lambda p: p.get("lucky_guess_wins", 0) >= 1
    },
    "item_master": {
        "name": "Item Master",
        "icon": "🧪",
        "description": "Use 25 items total.",
        "condition": lambda p: p["items_used"] >= 25
    },
    "number_god": {
        "name": "Number God",
        "icon": "👑",
        "description": "Win on Extreme or Impossible 5 times.",
        "condition": lambda p: p["difficulty_wins"].get("extreme", 0) + p["difficulty_wins"].get("impossible", 0) >= 5
    }
}

# ============================================================
# PLAYER DEFAULTS
# ============================================================

def default_player():
    """Create a new player with default stats."""
    return {
        "coins": 250,
        "total_coins_earned": 0,
        "games_won": 0,
        "games_lost": 0,
        "win_streak": 0,
        "highest_streak": 0,
        "items_used": 0,
        "perfect_games": 0,
        "inventory": {
            "hint": 0,
            "free_guess": 0,
            "reveal_digit": 0,
            "double_reward": 0,
            "lucky_guess": 0,
            "streak_shield": 0
        },
        "achievements": [],
        "difficulty_wins": {},
        "streak_shield_wins": 0,
        "lucky_guess_wins": 0,
        "impossible_no_items": False
    }