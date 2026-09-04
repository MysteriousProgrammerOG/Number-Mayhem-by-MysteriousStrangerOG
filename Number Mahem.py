# Number Mahem.py - The Ultimate Number Guessing Game (Terminal Version)
# A complete terminal game with economy, inventory, achievements, and save data.
#
# This version has been REFACTORED to use the shared game logic modules
# in the backend/ folder. The terminal UI is preserved, but the game logic
# now comes from:
#   - backend/constants.py  (difficulties, shop items, achievements)
#   - backend/player.py     (player data + SQLite persistence)
#   - backend/game.py       (GameSession - core game engine)
#
# HOW TO PLAY:
# - Guess the secret number within the attempt limit
# - Win games to earn coins
# - Spend coins in the shop on helpful items
# - Use items during games to gain an edge
# - Build win streaks for bigger rewards
# - Unlock achievements as you progress
# - Your progress is saved automatically to SQLite

import os
import re
import sys
import time

from backend.constants import ACHIEVEMENTS, DIFFICULTIES, SHOP_ITEMS
from backend.game import GameSession
from backend.player import Player

# ============================================================
# SECTION 1: COLOR & UI HELPERS
# ============================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GOLD = "\033[93m"


def c(text, color):
    """Wrap text in a color code."""
    return f"{color}{text}{Colors.RESET}"


def strip_ansi(text):
    """Remove ANSI color codes from text (for width calculations)."""
    return re.sub(r'\033\[\d+(;\d+)*m', '', text)


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def typewriter(text, delay=0.03):
    """Print text with a typewriter effect."""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def print_banner():
    """Print the game title banner."""
    banner = r"""
╔══════════════════════════════════════════════╗
║                                              ║
║          N U M B E R   M A Y H E M           ║
║        The Ultimate Guessing Game            ║
║                                              ║
╚══════════════════════════════════════════════╝
"""
    print(c(banner, Colors.CYAN))


def print_box(title, lines):
    """Print a boxed menu with a title and list of lines."""
    if not lines:
        lines = [""]
    clean_lines = [strip_ansi(line) for line in lines]
    width = max(len(title) + 4, max(len(line) for line in clean_lines) + 4)
    width = max(width, 20)  # Minimum width

    print(c("╔" + "═" * (width - 2) + "╗", Colors.CYAN))
    print(c("║ " + title.center(width - 4) + " ║", Colors.CYAN))
    print(c("╠" + "═" * (width - 2) + "╣", Colors.CYAN))
    for line, clean in zip(lines, clean_lines):
        padding = width - 4 - len(clean)
        print(c("║ ", Colors.CYAN) + line + " " * padding + c(" ║", Colors.CYAN))
    print(c("╚" + "═" * (width - 2) + "╝", Colors.CYAN))


def get_int_input(prompt, min_val=None, max_val=None):
    """Get a validated integer input from the user."""
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(c(f"Please enter a number at least {min_val}.", Colors.RED))
                continue
            if max_val is not None and value > max_val:
                print(c(f"Please enter a number at most {max_val}.", Colors.RED))
                continue
            return value
        except ValueError:
            print(c("Please enter a valid integer!", Colors.RED))


def press_enter():
    """Wait for the user to press Enter."""
    input(c("\nPress Enter to continue...", Colors.DIM))


# ============================================================
# SECTION 2: SHOP SYSTEM
# ============================================================

def show_shop(player):
    """Display the shop and handle purchases."""
    while True:
        clear_screen()
        print_banner()
        print_box("SHOP", [
            c(f"Coins: {player.data['coins']} 🪙", Colors.GOLD),
            ""
        ])

        for i, (item_id, item) in enumerate(SHOP_ITEMS.items(), 1):
            print(c(f"  [{i}] {item['icon']} {item['name']}", Colors.WHITE))
            print(c(f"      Cost: {item['cost']} 🪙", Colors.GOLD))
            print(c(f"      {item['description']}", Colors.DIM))
            print()

        print(c("  [0] Leave Shop", Colors.WHITE))
        print()

        choice = get_int_input("Purchase: ", 0, len(SHOP_ITEMS))

        if choice == 0:
            player.save()
            return

        item_id = list(SHOP_ITEMS.keys())[choice - 1]
        success, message = player.buy_item(item_id)

        if success:
            print(c(message, Colors.GREEN))
        else:
            print(c(message, Colors.RED))
        press_enter()


# ============================================================
# SECTION 3: INVENTORY SYSTEM
# ============================================================

def show_inventory(player):
    """Display the player's inventory."""
    clear_screen()
    print_banner()
    print_box("INVENTORY", [
        c(f"Coins: {player.data['coins']} 🪙", Colors.GOLD),
        ""
    ])

    has_items = False
    for item_id, item in SHOP_ITEMS.items():
        count = player.data["inventory"].get(item_id, 0)
        if count > 0:
            has_items = True
            print(c(f"  {item['icon']} {item['name']} × {count}", Colors.WHITE))
            print(c(f"      {item['description']}", Colors.DIM))
            print()

    if not has_items:
        print(c("  Your inventory is empty! Visit the shop to buy items.", Colors.DIM))

    print()
    press_enter()


# ============================================================
# SECTION 4: GAME ENGINE (uses GameSession from backend/game.py)
# ============================================================

def get_guess_input(low, high, decimals):
    """Get a validated guess from the user."""
    while True:
        try:
            raw = input(f"Guess a number ({low} - {high}): ").strip()
            if decimals:
                guess = float(raw)
            else:
                guess = float(raw)
                if guess != int(guess):
                    print(c("Please enter a whole number!", Colors.RED))
                    continue
                guess = int(guess)

            if guess < low or guess > high:
                print(c(f"Please enter a number between {low} and {high}.", Colors.RED))
                continue
            return guess
        except ValueError:
            print(c("Please enter a valid number!", Colors.RED))


def play_game(player, difficulty_id):
    """Play a round of the guessing game using the shared GameSession class."""
    session = GameSession(player, difficulty_id)
    diff = session.diff
    low = session.low
    high = session.high
    max_attempts = session.max_attempts
    decimals = session.decimals

    clear_screen()
    print_banner()
    print_box(f"{diff['icon']} {diff['name'].upper()} DIFFICULTY", [
        c(f"Range: {low} - {high}", Colors.WHITE),
        c(f"Attempts: {max_attempts}", Colors.WHITE),
        c(f"Reward: {diff['base_reward']} 🪙", Colors.GOLD),
        c(f"Decimals: {'ON' if decimals else 'OFF'}", Colors.YELLOW if decimals else Colors.DIM),
        ""
    ])

    # Show current streak multiplier
    streak_mult = session._streak_multiplier()
    if player.data["win_streak"] > 0:
        print(c(f"Current Streak: {player.data['win_streak']} 🔥 (×{streak_mult:.1f} reward)", Colors.YELLOW))

    if decimals:
        print(c(f"I'm thinking of a number between {low} and {high} (decimals included).", Colors.CYAN))
    else:
        print(c(f"I'm thinking of a number between {low} and {high}.", Colors.CYAN))

    while not session.game_over:
        print(c(f"\nAttempts: {session.attempts}/{max_attempts}", Colors.DIM))

        # Check if player has items available
        has_items = any(player.data["inventory"][item_id] > 0 for item_id in SHOP_ITEMS)

        if has_items:
            print(c("\n[1] Use Hint", Colors.MAGENTA))
            print(c("[2] Use Free Guess", Colors.MAGENTA))
            print(c("[3] Use Reveal Digit", Colors.MAGENTA))
            print(c("[4] Use Double Reward", Colors.MAGENTA))
            print(c("[5] Use Lucky Guess", Colors.MAGENTA))
            print(c("[6] Use Streak Shield", Colors.MAGENTA))
            print(c("[7] Continue Guessing", Colors.WHITE))

            action = get_int_input("\nChoice: ", 1, 7)

            if action == 7:
                pass  # Continue to guessing
            else:
                item_id = list(SHOP_ITEMS.keys())[action - 1]
                result = session.use_item(item_id)

                if not result["success"]:
                    print(c(result["error"], Colors.RED))
                    continue

                # Display item results
                if result.get("item") == "hint":
                    print(c(f"🔮 {result['hint_text']}", Colors.MAGENTA))
                elif result.get("item") == "free_guess":
                    print(c(f"🎟️ {result['message']}", Colors.GREEN))
                elif result.get("item") == "reveal_digit":
                    print(c(f"🔍 REVEALED: {result['revealed']}", Colors.MAGENTA))
                elif result.get("item") == "double_reward":
                    print(c(f"💰 {result['message']}", Colors.GOLD))
                elif result.get("item") == "lucky_guess":
                    if result.get("lucky_guess_correct"):
                        print(c(f"🎲 Lucky Guess picked: {result['lucky_guess_value']}", Colors.MAGENTA))
                        print(c("🎲 LUCKY! That's the number!", Colors.GREEN))
                    else:
                        print(c(f"🎲 Lucky Guess picked: {result['lucky_guess_value']}", Colors.MAGENTA))
                        print(c("🎲 Unlucky! That guess was wrong.", Colors.RED))
                        if result.get("game_over"):
                            break
                elif result.get("item") == "streak_shield":
                    print(c(f"🛡️ {result['message']}", Colors.GREEN))

                # If lucky guess ended the game, break out
                if result.get("game_over"):
                    break
                continue

        # Normal guess
        guess = get_guess_input(low, high, decimals)
        result = session.make_guess(guess)

        if not result["success"]:
            print(c(result["error"], Colors.RED))
            continue

        if result.get("correct"):
            break
        else:
            print(c(result["message"], Colors.YELLOW))

    # ===== GAME RESULT =====
    if session.won:
        clear_screen()
        print_banner()
        typewriter(c("🎉 CONGRATULATIONS! YOU GUESSED IT! 🎉", Colors.GREEN), 0.02)
        print(c(f"\nThe number was: {session.secret_number}", Colors.CYAN))
        print(c(f"Attempts used: {session.attempts}/{max_attempts}", Colors.WHITE))

        # Show reward breakdown
        breakdown = session.get_reward_breakdown()
        print(c("\n═══════ REWARD BREAKDOWN ═══════", Colors.GOLD))
        print(c(f"  Base Reward:          {breakdown['base_reward']} 🪙", Colors.GOLD))
        if breakdown["attempts_bonus"] > 0:
            print(c(f"  Attempts Remaining:   +{breakdown['attempts_bonus']} 🪙", Colors.GOLD))
        if breakdown["perfect_bonus"] > 0:
            print(c(f"  Perfect Game:         +{breakdown['perfect_bonus']} 🪙", Colors.GOLD))
        print(c(f"  Win Streak:           ×{breakdown['streak_multiplier']:.1f}", Colors.GOLD))
        if breakdown["double_reward"]:
            print(c("  Double Reward:        ×2", Colors.GOLD))
        print(c("  ─────────────────────────────", Colors.GOLD))
        print(c(f"  TOTAL:                {breakdown['total']} 🪙", Colors.GOLD))
        print(c(f"\n  New coin balance: {player.data['coins']} 🪙", Colors.GOLD))

        # Show new achievements
        for ach_id in result.get("new_achievements", []):
            ach = ACHIEVEMENTS[ach_id]
            typewriter(c(f"\n🏆 ACHIEVEMENT UNLOCKED: {ach['icon']} {ach['name']}!", Colors.YELLOW), 0.02)
            print(c(f"   {ach['description']}", Colors.DIM))
            time.sleep(1)

    else:
        clear_screen()
        print_banner()
        typewriter(c("💀 OUT OF ATTEMPTS! 💀", Colors.RED), 0.02)
        print(c(f"\nThe number was: {session.secret_number}", Colors.CYAN))
        print(c(f"Attempts used: {session.attempts}/{max_attempts}", Colors.WHITE))

        if result.get("streak_shield_active"):
            print(c("\n🛡️ Your Streak Shield protected your win streak!", Colors.GREEN))
        elif result.get("streak_lost"):
            print(c(f"\n💥 STREAK LOST! Your streak has ended.", Colors.RED))

    press_enter()

    # Prompt to visit the shop after each game
    clear_screen()
    print_banner()
    print_box("GAME OVER", [
        c(f"Coins: {player.data['coins']} 🪙", Colors.GOLD),
        "",
        "[1] Visit the Shop",
        "[2] Back to Main Menu",
        ""
    ])
    post_game_choice = get_int_input("Choice: ", 1, 2)
    if post_game_choice == 1:
        show_shop(player)


# ============================================================
# SECTION 5: STATS & DIFFICULTY VIEW
# ============================================================

def show_stats(player):
    """Display all player stats and achievements."""
    p = player.data
    clear_screen()
    print_banner()
    print_box("PLAYER STATS", [
        c(f"Coins: {p['coins']} 🪙", Colors.GOLD),
        c(f"Total Coins Earned: {p['total_coins_earned']} 🪙", Colors.GOLD),
        c(f"Games Won: {p['games_won']}", Colors.GREEN),
        c(f"Games Lost: {p['games_lost']}", Colors.RED),
        c(f"Win Streak: {p['win_streak']} 🔥", Colors.YELLOW),
        c(f"Highest Streak: {p['highest_streak']} 🔥", Colors.YELLOW),
        c(f"Perfect Games: {p['perfect_games']} 🎯", Colors.CYAN),
        c(f"Items Used: {p['items_used']} 🧪", Colors.MAGENTA),
        ""
    ])

    # Difficulty wins
    print(c("  ── DIFFICULTY WINS ──", Colors.CYAN))
    for diff_id, diff in DIFFICULTIES.items():
        wins = p["difficulty_wins"].get(diff_id, 0)
        print(c(f"  {diff['icon']} {diff['name']}: {wins}", Colors.WHITE))

    # Achievements
    print(c("\n  ── ACHIEVEMENTS ──", Colors.CYAN))
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id in p["achievements"]:
            print(c(f"  ✅ {ach['icon']} {ach['name']}", Colors.GREEN))
        else:
            print(c(f"  ☐ {ach['icon']} {ach['name']}", Colors.DIM))
            print(c(f"      {ach['description']}", Colors.DIM))

    print()
    press_enter()


def show_difficulties():
    """Display all difficulty information."""
    clear_screen()
    print_banner()
    print_box("DIFFICULTIES", [""])

    for diff_id, diff in DIFFICULTIES.items():
        print(c(f"  {diff['icon']} {diff['name']}", Colors.WHITE))
        print(c(f"      Range: {diff['low']} - {diff['high']}", Colors.CYAN))
        print(c(f"      Attempts: {diff['attempts']}", Colors.CYAN))
        print(c(f"      Reward: {diff['base_reward']} 🪙", Colors.GOLD))
        print(c(f"      Decimals: {'ON' if diff['decimals'] else 'OFF'}", Colors.YELLOW if diff['decimals'] else Colors.DIM))
        print()

    press_enter()


# ============================================================
# SECTION 6: MAIN MENU & GAME FLOW
# ============================================================

def show_main_menu(player):
    """Display the main menu."""
    p = player.data
    clear_screen()
    print_banner()

    print(c(f"  Coins: {p['coins']} 🪙", Colors.GOLD))
    print(c(f"  Games Won: {p['games_won']}", Colors.GREEN))
    print(c(f"  Games Lost: {p['games_lost']}", Colors.RED))
    if p["win_streak"] > 0:
        print(c(f"  Win Streak: {p['win_streak']} 🔥", Colors.YELLOW))
    print()

    print_box("MAIN MENU", [
        "[1] Play",
        "[2] Shop",
        "[3] Difficulty",
        "[4] Inventory",
        "[5] Stats",
        "[6] Exit",
        ""
    ])

    return get_int_input("Choose an option: ", 1, 6)


def select_difficulty():
    """Let the player select a difficulty."""
    clear_screen()
    print_banner()
    print_box("SELECT DIFFICULTY", [""])

    for i, (diff_id, diff) in enumerate(DIFFICULTIES.items(), 1):
        print(c(f"  [{i}] {diff['icon']} {diff['name']}", Colors.WHITE))
        print(c(f"      {diff['description']}", Colors.DIM))
        print(c(f"      Reward: {diff['base_reward']} 🪙", Colors.GOLD))
        print()

    choice = get_int_input("Select difficulty: ", 1, len(DIFFICULTIES))
    return list(DIFFICULTIES.keys())[choice - 1]


def main():
    """Main game loop."""
    player = Player()

    # Welcome message
    clear_screen()
    print_banner()
    if player.data["games_won"] > 0 or player.data["games_lost"] > 0:
        print(c("Welcome back, Player!", Colors.GREEN))
        print(c(f"Coins: {player.data['coins']} 🪙", Colors.GOLD))
        if player.data["win_streak"] > 0:
            print(c(f"Win Streak: {player.data['win_streak']} 🔥", Colors.YELLOW))
    else:
        print(c("Welcome, new Player!", Colors.GREEN))
        print(c("You start with 250 coins. Good luck!", Colors.GOLD))
        print()
        print(c("  HOW TO PLAY:", Colors.CYAN))
        print(c("  Guess the secret number within the attempt limit.", Colors.DIM))
        print(c("  Win games to earn coins. Spend coins in the shop.", Colors.DIM))
        print(c("  Use items during games to gain an edge!", Colors.DIM))
    press_enter()

    while True:
        choice = show_main_menu(player)

        if choice == 1:  # Play
            difficulty_id = select_difficulty()
            play_game(player, difficulty_id)

        elif choice == 2:  # Shop
            show_shop(player)

        elif choice == 3:  # Difficulty
            show_difficulties()

        elif choice == 4:  # Inventory
            show_inventory(player)

        elif choice == 5:  # Stats
            show_stats(player)

        elif choice == 6:  # Exit
            clear_screen()
            print_banner()
            typewriter(c("Saving player data...", Colors.CYAN), 0.02)
            player.save()
            typewriter(c("Game saved successfully!", Colors.GREEN), 0.02)
            typewriter(c("Thanks for playing NUMBER MAYHEM! 👋", Colors.CYAN), 0.02)
            time.sleep(1)
            break


# ============================================================
# SECTION 7: ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(c("\n\nGame interrupted. Goodbye!", Colors.YELLOW))
        sys.exit(0)