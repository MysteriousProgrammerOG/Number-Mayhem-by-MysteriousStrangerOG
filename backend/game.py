# game.py
# GameSession class - the core game logic for Number Mayhem.
# This class was extracted from the original terminal game's play_game() function.
# It handles:
#   - Generating the secret number (server-side only)
#   - Validating guesses
#   - Tracking attempts
#   - Using items
#   - Calculating rewards
#   - Updating player stats
#
# IMPORTANT: The secret number is NEVER exposed through get_public_state().
# The browser can only see what the original terminal game would show.

import random

from .constants import DIFFICULTIES, SHOP_ITEMS


class GameSession:
    """A single round of Number Mayhem."""

    def __init__(self, player, difficulty_id):
        """Start a new game session.
        player: the Player object
        difficulty_id: one of "baby", "easy", "normal", "hard", "extreme", "impossible"
        """
        if difficulty_id not in DIFFICULTIES:
            raise ValueError(f"Unknown difficulty: {difficulty_id}")

        self.player = player
        self.difficulty_id = difficulty_id
        self.diff = DIFFICULTIES[difficulty_id]

        self.low = self.diff["low"]
        self.high = self.diff["high"]
        self.max_attempts = self.diff["attempts"]
        self.decimals = self.diff["decimals"]

        # Generate the secret number (stays on the server!)
        if self.decimals:
            self.secret_number = round(random.uniform(self.low, self.high), 1)
        else:
            self.secret_number = random.randint(self.low, self.high)

        # Game state
        self.attempts = 0
        self.items_used_this_game = 0
        self.double_reward_active = False
        self.streak_shield_active = False
        self.lucky_guess_used = False
        self.free_guess_pending = False  # True when a Free Guess item is used
        self.game_over = False
        self.won = False

    # ============================================================
    # PUBLIC STATE (safe to send to the browser)
    # ============================================================

    def get_public_state(self):
        """Return game state that is safe to show the player.
        The secret number is NEVER included here.
        """
        return {
            "difficulty_id": self.difficulty_id,
            "difficulty_name": self.diff["name"],
            "difficulty_icon": self.diff["icon"],
            "low": self.low,
            "high": self.high,
            "max_attempts": self.max_attempts,
            "attempts": self.attempts,
            "decimals": self.decimals,
            "game_over": self.game_over,
            "won": self.won,
            "double_reward_active": self.double_reward_active,
            "streak_shield_active": self.streak_shield_active,
            "free_guess_pending": self.free_guess_pending,
            "streak_multiplier": self._streak_multiplier(),
            "current_streak": self.player.data["win_streak"]
        }

    def _streak_multiplier(self):
        """Calculate the current streak multiplier.
        Formula: 1.0 + 0.1 per 2 wins, capped at 2.0
        """
        return min(1.0 + (self.player.data["win_streak"] // 2) * 0.1, 2.0)

    # ============================================================
    # GUESSING
    # ============================================================

    def validate_guess(self, guess):
        """Check if a guess is valid for this difficulty.
        Returns (is_valid, error_message).
        """
        if self.game_over:
            return False, "The game is already over. Start a new game."

        # Check type
        if isinstance(guess, bool) or not isinstance(guess, (int, float)):
            return False, "Please enter a valid number."

        # Check decimals rule
        if not self.decimals:
            if isinstance(guess, float) and guess != int(guess):
                return False, "Please enter a whole number."
            guess = int(guess)

        # Check range
        if guess < self.low or guess > self.high:
            return False, f"Please enter a number between {self.low} and {self.high}."

        return True, ""

    def make_guess(self, guess):
        """Process a player's guess.
        Returns a result dictionary with everything the frontend needs.
        """
        # Validate the guess
        is_valid, error = self.validate_guess(guess)
        if not is_valid:
            return {
                "success": False,
                "error": error,
                "game_over": self.game_over,
                "state": self.get_public_state()
            }

        # Consume an attempt (unless a Free Guess is pending)
        if not self.free_guess_pending:
            self.attempts += 1
        self.free_guess_pending = False

        # Check if the guess is correct
        if abs(guess - self.secret_number) < 0.0001:
            return self._handle_win()
        else:
            # Wrong guess - give feedback
            if guess < self.secret_number:
                feedback = "too_low"
                message = "Too Low! Try something Higher!"
            else:
                feedback = "too_high"
                message = "Too High! Try something Lower!"

            # Check if attempts are exhausted
            if self.attempts >= self.max_attempts:
                return self._handle_loss()

            return {
                "success": True,
                "correct": False,
                "feedback": feedback,
                "message": message,
                "game_over": False,
                "state": self.get_public_state()
            }

    # ============================================================
    # WIN / LOSE HANDLING
    # ============================================================

    def _handle_win(self):
        """Process a winning guess. Updates player stats and calculates reward."""
        self.game_over = True
        self.won = True

        p = self.player.data

        # Update stats
        p["games_won"] += 1
        p["win_streak"] += 1
        if p["win_streak"] > p["highest_streak"]:
            p["highest_streak"] = p["win_streak"]

        # Track difficulty wins
        p["difficulty_wins"][self.difficulty_id] = p["difficulty_wins"].get(self.difficulty_id, 0) + 1

        # Track special conditions
        if self.streak_shield_active:
            p["streak_shield_wins"] += 1
        if self.lucky_guess_used:
            p["lucky_guess_wins"] += 1
        if self.difficulty_id == "impossible" and self.items_used_this_game == 0:
            p["impossible_no_items"] = True
        if self.attempts == 1:
            p["perfect_games"] += 1

        # Calculate reward
        reward = self.calculate_reward()
        p["coins"] += reward
        p["total_coins_earned"] += reward

        # Check achievements
        new_achievements = self.player.check_achievements()

        # Save player data
        self.player.save()

        return {
            "success": True,
            "correct": True,
            "game_over": True,
            "won": True,
            "secret_number": self.secret_number,  # Revealed only after the game ends
            "attempts_used": self.attempts,
            "reward": reward,
            "reward_breakdown": self.get_reward_breakdown(),
            "new_achievements": new_achievements,
            "state": self.get_public_state()
        }

    def _handle_loss(self):
        """Process running out of attempts."""
        self.game_over = True
        self.won = False

        p = self.player.data
        p["games_lost"] += 1

        # Streak handling
        if self.streak_shield_active:
            # Shield protects the streak
            streak_lost = False
        else:
            if p["win_streak"] > 0:
                streak_lost = True
                p["win_streak"] = 0
            else:
                streak_lost = False

        self.player.save()

        return {
            "success": True,
            "correct": False,
            "game_over": True,
            "won": False,
            "secret_number": self.secret_number,  # Revealed only after the game ends
            "attempts_used": self.attempts,
            "streak_lost": streak_lost,
            "streak_shield_active": self.streak_shield_active,
            "state": self.get_public_state()
        }

    # ============================================================
    # REWARD CALCULATION
    # ============================================================

    def calculate_reward(self):
        """Calculate the reward for a win using the original formula:
        (Base + AttemptsBonus + PerfectBonus) x StreakMultiplier x DoubleReward
        """
        base = self.diff["base_reward"]

        # Remaining attempts bonus: +2 coins per unused attempt
        remaining = self.max_attempts - self.attempts
        attempts_bonus = remaining * 2

        # Streak multiplier: 1.0 + 0.1 per 2 wins, capped at 2.0
        streak_mult = self._streak_multiplier()

        # Perfect game bonus: +50% of base
        perfect_bonus = 0
        if self.attempts == 1:
            perfect_bonus = base // 2

        subtotal = base + attempts_bonus + perfect_bonus
        total = int(subtotal * streak_mult)

        # Double reward item
        if self.double_reward_active:
            total *= 2

        return total

    def get_reward_breakdown(self):
        """Return the reward breakdown for display."""
        base = self.diff["base_reward"]
        remaining = self.max_attempts - self.attempts
        attempts_bonus = remaining * 2
        streak_mult = self._streak_multiplier()
        perfect_bonus = base // 2 if self.attempts == 1 else 0

        return {
            "base_reward": base,
            "attempts_bonus": attempts_bonus,
            "perfect_bonus": perfect_bonus,
            "streak_multiplier": streak_mult,
            "double_reward": self.double_reward_active,
            "total": self.calculate_reward()
        }

    # ============================================================
    # ITEMS
    # ============================================================

    def use_item(self, item_id):
        """Use an item during the game.
        Returns a result dictionary.
        """
        if self.game_over:
            return {"success": False, "error": "The game is already over."}

        if item_id not in SHOP_ITEMS:
            return {"success": False, "error": "Item does not exist."}

        # Check the player actually owns the item
        if self.player.data["inventory"].get(item_id, 0) <= 0:
            return {"success": False, "error": f"You don't have any {SHOP_ITEMS[item_id]['name']}s!"}

        # Consume the item
        self.player.data["inventory"][item_id] -= 1
        self.player.data["items_used"] += 1
        self.items_used_this_game += 1

        # Handle each item type
        if item_id == "hint":
            result = self._use_hint()

        elif item_id == "free_guess":
            self.free_guess_pending = True
            result = {
                "success": True,
                "item": "free_guess",
                "message": "FREE GUESS! Your next guess won't cost an attempt!"
            }

        elif item_id == "reveal_digit":
            result = self._use_reveal_digit()

        elif item_id == "double_reward":
            self.double_reward_active = True
            result = {
                "success": True,
                "item": "double_reward",
                "message": "DOUBLE REWARD ACTIVATED! Your next win pays double!"
            }

        elif item_id == "lucky_guess":
            result = self._use_lucky_guess()

        elif item_id == "streak_shield":
            self.streak_shield_active = True
            result = {
                "success": True,
                "item": "streak_shield",
                "message": "STREAK SHIELD ACTIVATED! Your win streak is protected!"
            }

        # Save player data (inventory changed)
        self.player.save()

        # Add current state to the result
        result["state"] = self.get_public_state()
        return result

    def _use_hint(self):
        """Generate a hint about the secret number.
        Returns the same hint types as the original game:
        parity, range, or digit.
        """
        hint_type = random.choice(["parity", "range", "digit"])

        if hint_type == "parity":
            if self.decimals:
                int_part = int(self.secret_number)
                if int_part % 2 == 0:
                    text = "HINT: The integer part of the number is EVEN."
                else:
                    text = "HINT: The integer part of the number is ODD."
            else:
                if self.secret_number % 2 == 0:
                    text = "HINT: The number is EVEN."
                else:
                    text = "HINT: The number is ODD."

        elif hint_type == "range":
            mid = (self.low + self.high) / 2
            if self.decimals:
                if self.secret_number <= mid:
                    text = f"HINT: The number is between {self.low} and {mid:.1f}."
                else:
                    text = f"HINT: The number is between {mid:.1f} and {self.high}."
            else:
                if self.secret_number <= mid:
                    text = f"HINT: The number is between {self.low} and {int(mid)}."
                else:
                    text = f"HINT: The number is between {int(mid) + 1} and {self.high}."

        else:  # digit
            if self.decimals:
                num_str = f"{self.secret_number:.1f}"
            else:
                num_str = str(self.secret_number)

            digit_positions = [i for i, ch in enumerate(num_str) if ch.isdigit()]
            if digit_positions:
                pos = random.choice(digit_positions)
                display = []
                for i, ch in enumerate(num_str):
                    if i == pos:
                        display.append(ch)
                    elif ch == '.':
                        display.append('.')
                    else:
                        display.append('_')
                text = f"HINT: The number looks like: {''.join(display)}"
            else:
                text = "HINT: The number is... mysterious!"

        return {
            "success": True,
            "item": "hint",
            "hint_text": text
        }

    def _use_reveal_digit(self):
        """Reveal one digit of the secret number."""
        if self.decimals:
            num_str = f"{self.secret_number:.1f}"
        else:
            num_str = str(self.secret_number)

        digit_positions = [i for i, ch in enumerate(num_str) if ch.isdigit()]
        if not digit_positions:
            return {"success": True, "item": "reveal_digit", "revealed": "Could not reveal a digit!"}

        pos = random.choice(digit_positions)
        display = []
        for i, ch in enumerate(num_str):
            if i == pos:
                display.append(ch)
            elif ch == '.':
                display.append('.')
            else:
                display.append('_')

        return {
            "success": True,
            "item": "reveal_digit",
            "revealed": ''.join(display)
        }

    def _use_lucky_guess(self):
        """Auto-guess a random number. 50% chance to be correct."""
        self.lucky_guess_used = True

        if self.decimals:
            guess = round(random.uniform(self.low, self.high), 1)
        else:
            guess = random.randint(self.low, self.high)

        if abs(guess - self.secret_number) < 0.0001:
            # Lucky! The auto-guess was correct
            win_result = self._handle_win()
            win_result["lucky_guess_value"] = guess
            win_result["lucky_guess_correct"] = True
            return win_result
        else:
            # Unlucky - the auto-guess was wrong. Consumes an attempt.
            self.attempts += 1

            # Check if attempts are exhausted
            if self.attempts >= self.max_attempts:
                loss_result = self._handle_loss()
                loss_result["lucky_guess_value"] = guess
                loss_result["lucky_guess_correct"] = False
                return loss_result

            return {
                "success": True,
                "item": "lucky_guess",
                "lucky_guess_value": guess,
                "lucky_guess_correct": False,
                "message": f"Lucky Guess picked: {guess}. Unlucky! That guess was wrong."
            }