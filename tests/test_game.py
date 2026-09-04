# test_game.py
# Tests for the Number Mayhem backend game logic.
# Run with:  pytest tests/test_game.py
#
# These tests verify that the game logic works correctly.
# They test the GameSession class and Player class directly,
# without needing a browser or the FastAPI server.

import os
import sys
import tempfile

import pytest

# Add the project root to the path so we can import the backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.constants import DIFFICULTIES, SHOP_ITEMS, ACHIEVEMENTS, default_player
from backend.game import GameSession
from backend.player import Player


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Redirect the persistence layer to a temporary database.

    Every test gets its own temp SQLite file so the real local
    players.db save file is never read or written by the test suite.
    DB_PATH is resolved at call time inside backend/database.py,
    so patching the module attribute there redirects every save/load.
    """
    from backend import database

    temp_db = tmp_path / "test_players.db"
    monkeypatch.setattr(database, "DB_PATH", temp_db)


# ============================================================
# TEST HELPERS
# ============================================================

def make_player():
    """Create a fresh player for testing.
    Uses default values instead of loading from the database,
    so each test starts with a clean player.
    """
    player = Player.__new__(Player)  # Skip __init__ (which loads from DB)
    player.data = default_player()
    return player


def make_session(player, difficulty="baby"):
    """Create a game session for testing."""
    return GameSession(player, difficulty)


# ============================================================
# DIFFICULTY TESTS
# ============================================================

def test_all_difficulties_exist():
    """All 6 difficulties should be defined."""
    assert set(DIFFICULTIES.keys()) == {"baby", "easy", "normal", "hard", "extreme", "impossible"}


def test_difficulty_values():
    """Difficulty values should match the original game exactly."""
    assert DIFFICULTIES["baby"]["low"] == 1
    assert DIFFICULTIES["baby"]["high"] == 10
    assert DIFFICULTIES["baby"]["attempts"] == 10
    assert DIFFICULTIES["baby"]["base_reward"] == 5

    assert DIFFICULTIES["easy"]["low"] == 1
    assert DIFFICULTIES["easy"]["high"] == 50
    assert DIFFICULTIES["easy"]["attempts"] == 8
    assert DIFFICULTIES["easy"]["base_reward"] == 15

    assert DIFFICULTIES["normal"]["low"] == 1
    assert DIFFICULTIES["normal"]["high"] == 1000
    assert DIFFICULTIES["normal"]["attempts"] == 10
    assert DIFFICULTIES["normal"]["base_reward"] == 50

    assert DIFFICULTIES["hard"]["low"] == 1
    assert DIFFICULTIES["hard"]["high"] == 10000
    assert DIFFICULTIES["hard"]["attempts"] == 8
    assert DIFFICULTIES["hard"]["base_reward"] == 150

    assert DIFFICULTIES["extreme"]["low"] == 1
    assert DIFFICULTIES["extreme"]["high"] == 1000000
    assert DIFFICULTIES["extreme"]["attempts"] == 10
    assert DIFFICULTIES["extreme"]["base_reward"] == 1000

    assert DIFFICULTIES["impossible"]["low"] == 0.1
    assert DIFFICULTIES["impossible"]["high"] == 10000
    assert DIFFICULTIES["impossible"]["attempts"] == 5
    assert DIFFICULTIES["impossible"]["base_reward"] == 10000
    assert DIFFICULTIES["impossible"]["decimals"] is True


def test_shop_items():
    """Shop items should match the original game exactly."""
    assert set(SHOP_ITEMS.keys()) == {"hint", "free_guess", "reveal_digit", "double_reward", "lucky_guess", "streak_shield"}
    assert SHOP_ITEMS["hint"]["cost"] == 50
    assert SHOP_ITEMS["free_guess"]["cost"] == 100
    assert SHOP_ITEMS["reveal_digit"]["cost"] == 250
    assert SHOP_ITEMS["double_reward"]["cost"] == 500
    assert SHOP_ITEMS["lucky_guess"]["cost"] == 750
    assert SHOP_ITEMS["streak_shield"]["cost"] == 300


def test_achievements_exist():
    """All 12 achievements should be defined."""
    assert len(ACHIEVEMENTS) == 12
    assert "first_blood" in ACHIEVEMENTS
    assert "getting_started" in ACHIEVEMENTS
    assert "millionaire" in ACHIEVEMENTS
    assert "impossible_winner" in ACHIEVEMENTS
    assert "insanity" in ACHIEVEMENTS
    assert "perfectionist" in ACHIEVEMENTS
    assert "fortunes_favorite" in ACHIEVEMENTS
    assert "the_machine" in ACHIEVEMENTS
    assert "survivor" in ACHIEVEMENTS
    assert "gambler" in ACHIEVEMENTS
    assert "item_master" in ACHIEVEMENTS
    assert "number_god" in ACHIEVEMENTS


# ============================================================
# GAME SESSION TESTS
# ============================================================

def test_game_start():
    """Starting a game should create a valid session."""
    player = make_player()
    session = make_session(player, "normal")

    assert session.difficulty_id == "normal"
    assert session.low == 1
    assert session.high == 1000
    assert session.max_attempts == 10
    assert session.attempts == 0
    assert session.game_over is False
    assert session.won is False

    # The secret number should be in range
    assert 1 <= session.secret_number <= 1000


def test_game_start_impossible_decimals():
    """Impossible difficulty should generate decimal numbers."""
    player = make_player()
    session = make_session(player, "impossible")

    assert session.decimals is True
    assert 0.1 <= session.secret_number <= 10000


def test_invalid_difficulty():
    """Invalid difficulty should raise an error."""
    player = make_player()
    try:
        GameSession(player, "not_a_difficulty")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_correct_guess():
    """A correct guess should win the game."""
    player = make_player()
    session = make_session(player, "baby")

    # Force the secret number so we know the answer
    session.secret_number = 5

    result = session.make_guess(5)

    assert result["success"] is True
    assert result["correct"] is True
    assert result["game_over"] is True
    assert result["won"] is True
    assert result["secret_number"] == 5
    assert player.data["games_won"] == 1
    assert player.data["win_streak"] == 1


def test_incorrect_guess_too_low():
    """A guess below the secret number should say too low."""
    player = make_player()
    session = make_session(player, "baby")
    session.secret_number = 7

    result = session.make_guess(3)

    assert result["success"] is True
    assert result["correct"] is False
    assert result["feedback"] == "too_low"
    assert result["game_over"] is False
    assert session.attempts == 1


def test_incorrect_guess_too_high():
    """A guess above the secret number should say too high."""
    player = make_player()
    session = make_session(player, "baby")
    session.secret_number = 3

    result = session.make_guess(9)

    assert result["success"] is True
    assert result["correct"] is False
    assert result["feedback"] == "too_high"
    assert result["game_over"] is False
    assert session.attempts == 1


def test_invalid_guess_out_of_range():
    """A guess outside the range should be rejected."""
    player = make_player()
    session = make_session(player, "baby")

    result = session.make_guess(100)

    assert result["success"] is False
    assert "between" in result["error"]


def test_invalid_guess_non_numeric():
    """A non-numeric guess should be rejected."""
    player = make_player()
    session = make_session(player, "baby")

    result = session.make_guess("abc")

    assert result["success"] is False


def test_decimal_guess_on_integer_difficulty():
    """A decimal guess on a non-decimal difficulty should be rejected."""
    player = make_player()
    session = make_session(player, "baby")

    result = session.make_guess(5.5)

    assert result["success"] is False
    assert "whole number" in result["error"]


def test_decimal_guess_on_impossible():
    """A decimal guess on Impossible should be accepted."""
    player = make_player()
    session = make_session(player, "impossible")
    session.secret_number = 500.5

    result = session.make_guess(500.5)

    assert result["success"] is True
    assert result["correct"] is True


def test_attempt_limit_loss():
    """Running out of attempts should lose the game."""
    player = make_player()
    session = make_session(player, "baby")
    session.secret_number = 10

    # Use all attempts with wrong guesses
    for i in range(10):
        result = session.make_guess(1)

    assert result["game_over"] is True
    assert result["won"] is False
    assert player.data["games_lost"] == 1


def test_public_state_does_not_contain_secret():
    """The public state should NEVER contain the secret number."""
    player = make_player()
    session = make_session(player, "normal")

    state = session.get_public_state()

    assert "secret_number" not in state
    assert "secret" not in state


# ============================================================
# REWARD TESTS
# ============================================================

def test_reward_base():
    """Base reward should be correct."""
    player = make_player()
    session = make_session(player, "normal")
    session.secret_number = 500
    session.attempts = 5  # Simulate 5 attempts used

    reward = session.calculate_reward()

    # Base 50 + (10-5)*2 = 10 attempts bonus = 60, streak mult 1.0
    assert reward == 60


def test_reward_perfect_game():
    """Perfect game (1 attempt) should include the perfect bonus."""
    player = make_player()
    session = make_session(player, "normal")
    session.secret_number = 500
    session.attempts = 1

    reward = session.calculate_reward()

    # Base 50 + (10-1)*2 = 18 attempts bonus + 25 perfect bonus = 93, streak mult 1.0
    assert reward == 93


def test_reward_streak_multiplier():
    """Streak multiplier should increase the reward."""
    player = make_player()
    player.data["win_streak"] = 4  # 4 wins -> multiplier 1.2
    session = make_session(player, "normal")
    session.secret_number = 500
    session.attempts = 5

    reward = session.calculate_reward()

    # (50 + 10) * 1.2 = 72
    assert reward == 72


def test_reward_double():
    """Double Reward item should double the total."""
    player = make_player()
    session = make_session(player, "normal")
    session.secret_number = 500
    session.attempts = 5
    session.double_reward_active = True

    reward = session.calculate_reward()

    # (50 + 10) * 1.0 * 2 = 120
    assert reward == 120


# ============================================================
# ITEM TESTS
# ============================================================

def test_use_hint():
    """Using a Hint should consume it and return hint text."""
    player = make_player()
    player.data["inventory"]["hint"] = 1
    session = make_session(player, "normal")

    result = session.use_item("hint")

    assert result["success"] is True
    assert result["item"] == "hint"
    assert "hint_text" in result
    assert player.data["inventory"]["hint"] == 0
    assert player.data["items_used"] == 1


def test_use_free_guess():
    """Using a Free Guess should set free_guess_pending."""
    player = make_player()
    player.data["inventory"]["free_guess"] = 1
    session = make_session(player, "normal")

    result = session.use_item("free_guess")

    assert result["success"] is True
    assert session.free_guess_pending is True
    assert player.data["inventory"]["free_guess"] == 0


def test_free_guess_does_not_consume_attempt():
    """A guess after using Free Guess should not consume an attempt."""
    player = make_player()
    player.data["inventory"]["free_guess"] = 1
    session = make_session(player, "baby")
    session.secret_number = 5

    # Use the free guess
    session.use_item("free_guess")

    # Make a wrong guess (should be free)
    result = session.make_guess(1)

    assert result["success"] is True
    assert session.attempts == 0  # No attempt consumed!


def test_use_reveal_digit():
    """Using Reveal Digit should return a digit pattern."""
    player = make_player()
    player.data["inventory"]["reveal_digit"] = 1
    session = make_session(player, "normal")
    session.secret_number = 1234

    result = session.use_item("reveal_digit")

    assert result["success"] is True
    assert result["item"] == "reveal_digit"
    assert "revealed" in result
    # The revealed pattern should have exactly one digit visible
    assert result["revealed"].count("_") == 3
    assert player.data["inventory"]["reveal_digit"] == 0


def test_use_double_reward():
    """Using Double Reward should activate it."""
    player = make_player()
    player.data["inventory"]["double_reward"] = 1
    session = make_session(player, "normal")

    result = session.use_item("double_reward")

    assert result["success"] is True
    assert session.double_reward_active is True
    assert player.data["inventory"]["double_reward"] == 0


def test_use_lucky_guess():
    """Using Lucky Guess should auto-guess."""
    player = make_player()
    player.data["inventory"]["lucky_guess"] = 1
    session = make_session(player, "baby")

    result = session.use_item("lucky_guess")

    assert result["success"] is True
    assert "lucky_guess_value" in result
    assert player.data["inventory"]["lucky_guess"] == 0


def test_use_streak_shield():
    """Using Streak Shield should activate it."""
    player = make_player()
    player.data["inventory"]["streak_shield"] = 1
    session = make_session(player, "normal")

    result = session.use_item("streak_shield")

    assert result["success"] is True
    assert session.streak_shield_active is True
    assert player.data["inventory"]["streak_shield"] == 0


def test_use_item_not_owned():
    """Using an item you don't own should fail."""
    player = make_player()
    session = make_session(player, "normal")

    result = session.use_item("hint")

    assert result["success"] is False
    assert "don't have" in result["error"]


def test_use_invalid_item():
    """Using a non-existent item should fail."""
    player = make_player()
    session = make_session(player, "normal")

    result = session.use_item("not_an_item")

    assert result["success"] is False


def test_streak_shield_protects_streak():
    """Streak Shield should protect the win streak on a loss."""
    player = make_player()
    player.data["win_streak"] = 5
    player.data["inventory"]["streak_shield"] = 1
    session = make_session(player, "baby")
    session.secret_number = 10

    # Use the shield
    session.use_item("streak_shield")

    # Lose the game
    for i in range(10):
        result = session.make_guess(1)

    assert result["game_over"] is True
    assert result["won"] is False
    assert result["streak_shield_active"] is True
    assert player.data["win_streak"] == 5  # Streak preserved!


# ============================================================
# SHOP TESTS
# ============================================================

def test_buy_item():
    """Buying an item should deduct coins and add to inventory."""
    player = make_player()
    initial_coins = player.data["coins"]

    success, message = player.buy_item("hint")

    assert success is True
    assert player.data["coins"] == initial_coins - 50
    assert player.data["inventory"]["hint"] == 1


def test_buy_item_insufficient_coins():
    """Buying an item without enough coins should fail."""
    player = make_player()
    player.data["coins"] = 10

    success, message = player.buy_item("hint")

    assert success is False
    assert "Not enough coins" in message
    assert player.data["inventory"]["hint"] == 0


def test_buy_invalid_item():
    """Buying a non-existent item should fail."""
    player = make_player()

    success, message = player.buy_item("not_an_item")

    assert success is False


# ============================================================
# ACHIEVEMENT TESTS
# ============================================================

def test_first_blood_achievement():
    """Winning a game should unlock First Blood."""
    player = make_player()
    session = make_session(player, "baby")
    session.secret_number = 5

    session.make_guess(5)

    assert "first_blood" in player.data["achievements"]


def test_perfectionist_achievement():
    """Winning on the first attempt should unlock Perfectionist."""
    player = make_player()
    session = make_session(player, "baby")
    session.secret_number = 5

    session.make_guess(5)

    assert "perfectionist" in player.data["achievements"]


def test_getting_started_achievement():
    """Winning 10 games should unlock Getting Started."""
    player = make_player()

    # Simulate 10 wins
    for i in range(10):
        session = make_session(player, "baby")
        session.secret_number = 5
        session.make_guess(5)

    assert "getting_started" in player.data["achievements"]


def test_impossible_winner_achievement():
    """Winning on Impossible should unlock the achievement."""
    player = make_player()
    session = make_session(player, "impossible")
    session.secret_number = 500.5

    session.make_guess(500.5)

    assert "impossible_winner" in player.data["achievements"]


def test_insanity_achievement():
    """Winning Impossible without items should unlock Insanity."""
    player = make_player()
    session = make_session(player, "impossible")
    session.secret_number = 500.5

    session.make_guess(500.5)

    assert "insanity" in player.data["achievements"]


def test_survivor_achievement():
    """Winning with Streak Shield should unlock Survivor."""
    player = make_player()
    player.data["inventory"]["streak_shield"] = 1
    session = make_session(player, "baby")
    session.secret_number = 5

    session.use_item("streak_shield")
    session.make_guess(5)

    assert "survivor" in player.data["achievements"]


def test_gambler_achievement():
    """Winning with Lucky Guess should unlock Gambler."""
    player = make_player()
    player.data["inventory"]["lucky_guess"] = 1
    session = make_session(player, "baby")

    # Force the lucky guess to be correct
    session.secret_number = 5
    # Monkey-patch random to make lucky guess always pick 5
    import random
    original_randint = random.randint
    random.randint = lambda a, b: 5

    try:
        result = session.use_item("lucky_guess")
    finally:
        random.randint = original_randint

    assert result.get("lucky_guess_correct") is True
    assert "gambler" in player.data["achievements"]


# ============================================================
# PERSISTENCE TESTS
# ============================================================

def test_player_save_load():
    """Player data should survive a save/load cycle.

    The autouse isolated_database fixture redirects all persistence
    to a temporary SQLite file, so the real local players.db file is
    never modified by this test.
    """
    player = make_player()
    player.data["coins"] = 999
    player.save()

    # Create a new player instance (simulates restarting the server)
    player2 = Player()

    assert player2.data["coins"] == 999


def test_default_player_values():
    """A new player should start with the correct values."""
    player = make_player()

    assert player.data["coins"] == 250
    assert player.data["games_won"] == 0
    assert player.data["games_lost"] == 0
    assert player.data["win_streak"] == 0
    assert player.data["highest_streak"] == 0
    assert player.data["items_used"] == 0
    assert player.data["perfect_games"] == 0
    assert player.data["inventory"] == {
        "hint": 0,
        "free_guess": 0,
        "reveal_digit": 0,
        "double_reward": 0,
        "lucky_guess": 0,
        "streak_shield": 0
    }
    assert player.data["achievements"] == []
    assert player.data["difficulty_wins"] == {}