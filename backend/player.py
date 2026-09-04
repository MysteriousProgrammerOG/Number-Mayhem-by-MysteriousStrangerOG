# player.py
# Player class for Number Mayhem.
# Handles player data, persistence, shop purchases, and achievements.
# The game logic in game.py uses this class to track player state.

from .constants import ACHIEVEMENTS, SHOP_ITEMS, default_player
from .database import load_player_data, save_player_data


class Player:
    """Represents the player and all their data."""

    def __init__(self):
        """Load player data from the database, or create a new player."""
        data = load_player_data()
        if data is None:
            self.data = default_player()
        else:
            # Merge with defaults in case new fields were added in updates
            self.data = default_player()
            for key in self.data:
                if key in data:
                    self.data[key] = data[key]

    # ============================================================
    # PERSISTENCE
    # ============================================================

    def save(self):
        """Save player data to the database."""
        save_player_data(self.data)

    # ============================================================
    # GETTERS (for API responses)
    # ============================================================

    def get_public_data(self):
        """Return player data safe to send to the browser.
        This includes everything EXCEPT the secret number
        (which is stored in GameSession, not here).
        """
        return self.data

    def get_inventory(self):
        """Return the player's inventory."""
        return self.data["inventory"]

    def get_achievements(self):
        """Return the list of unlocked achievement IDs."""
        return self.data["achievements"]

    # ============================================================
    # SHOP
    # ============================================================

    def buy_item(self, item_id):
        """Purchase an item from the shop.
        Returns (success, message).
        """
        if item_id not in SHOP_ITEMS:
            return False, "Item does not exist."

        item = SHOP_ITEMS[item_id]
        cost = item["cost"]

        if self.data["coins"] < cost:
            return False, f"Not enough coins! You need {cost} but only have {self.data['coins']}."

        # Deduct coins and add item to inventory
        self.data["coins"] -= cost
        self.data["inventory"][item_id] += 1
        self.save()
        return True, f"Purchased {item['icon']} {item['name']}!"

    # ============================================================
    # ACHIEVEMENTS
    # ============================================================

    def check_achievements(self):
        """Check all achievements and unlock any new ones.
        Returns a list of newly unlocked achievement IDs.
        """
        newly_unlocked = []
        for ach_id, ach in ACHIEVEMENTS.items():
            if ach_id not in self.data["achievements"] and ach["condition"](self.data):
                self.data["achievements"].append(ach_id)
                newly_unlocked.append(ach_id)

        if newly_unlocked:
            self.save()

        return newly_unlocked

    def get_all_achievements(self):
        """Return all achievements with their unlocked status.
        Used by the frontend to display the achievements panel.
        """
        result = []
        for ach_id, ach in ACHIEVEMENTS.items():
            result.append({
                "id": ach_id,
                "name": ach["name"],
                "icon": ach["icon"],
                "description": ach["description"],
                "unlocked": ach_id in self.data["achievements"]
            })
        return result