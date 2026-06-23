import random
from datetime import datetime, date

from flask import current_app

from app.models import db


def tick_pet(pet):
    """
    Apply stat decay based on how much real time has passed since we last
    touched this pet. Call this at the start of every route that reads or
    shows a pet, BEFORE you read its stats, so the numbers are always current
    even if the user (or their friend) hasn't opened the app in days.
    """
    now = datetime.utcnow()
    elapsed_hours = max(0.0, (now - pet.last_updated).total_seconds() / 3600.0)

    if elapsed_hours > 0:
        decay = current_app.config["DECAY_PER_HOUR"]
        pet.hunger = max(0.0, pet.hunger - decay["hunger"] * elapsed_hours)
        pet.happiness = max(0.0, pet.happiness - decay["happiness"] * elapsed_hours)
        pet.energy = max(0.0, pet.energy - decay["energy"] * elapsed_hours)
        pet.last_updated = now

    return pet


def register_care_action(pet):
    """
    Call this whenever the owner does ANY care action (feed/play/use item).
    Builds the daily streak that the coin bonus is based on.
    Returns the number of bonus coins earned (0 if today's streak bonus was
    already claimed).
    """
    today = date.today()
    if pet.last_care_date == today:
        return 0  # already counted today

    if pet.last_care_date and (today - pet.last_care_date).days == 1:
        pet.streak_days += 1
    elif pet.last_care_date != today:
        pet.streak_days = 1  # streak broken (or first ever action) - restart at 1

    pet.last_care_date = today

    bonus = (
        current_app.config["DAILY_BONUS_BASE"]
        + current_app.config["DAILY_BONUS_PER_STREAK_DAY"] * (pet.streak_days - 1)
    )
    pet.owner.coins += bonus
    return bonus


ITEM_ICON_MAP = {
    "Apple": "apple",
    "Pizza Slice": "pizza",
    "Fancy Cake": "cake",
    "Squeaky Toy": "squeaky-toy",
    "Beach Ball": "beach-ball",
    "Warm Blanket": "blanket",
    "AirPods": "earbuds",
    "Cheetos": "snack-puffs",
    "Energy Drink": "energy-drink",
    "Paint": "paint",
    "Noodles": "noodles",
    "Ghost Pepper": "ghost-pepper",
    "Rocket Fuel Soda": "rocket-fuel",
    "Dynamite Candy": "dynamite-candy",
}


def item_icon_key(item_name):
    """
    Maps a shop item's name to an <symbol> id in static/img/icons.svg.
    Falls back to a generic gift box icon for anything not in the map,
    so adding a new item to seed.py without an icon still looks fine.
    Add new items here as you add them to seed.py.
    """
    return ITEM_ICON_MAP.get(item_name, "gift")


def minigame_plays_used_today(user):
    """
    Read-only version of the daily reset logic in play_minigame(), used just
    for displaying the right number on page load. play_minigame() only resets
    minigame_plays_today in the database once the user actually plays, so
    without this, a page refresh on a new day would show yesterday's count
    until the next click.
    """
    if user.last_minigame_date != date.today():
        return 0
    return user.minigame_plays_today


def can_play_minigame(user):
    today = date.today()
    if user.last_minigame_date != today:
        return True
    return user.minigame_plays_today < current_app.config["MINIGAME_PLAYS_PER_DAY"]


def play_minigame(user):
    """Awards a random coin amount if the user has plays remaining today."""
    today = date.today()
    if user.last_minigame_date != today:
        user.last_minigame_date = today
        user.minigame_plays_today = 0

    if user.minigame_plays_today >= current_app.config["MINIGAME_PLAYS_PER_DAY"]:
        return None

    low, high = current_app.config["MINIGAME_COIN_RANGE"]
    payout = random.randint(low, high)
    user.coins += payout
    user.minigame_plays_today += 1
    return payout
