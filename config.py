import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-this-in-production")

    # Render/Railway/Heroku give you a DATABASE_URL env var for Postgres.
    # If it's not set, we fall back to a local SQLite file so the app
    # runs fine on your laptop with zero setup.
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres://"):
        # SQLAlchemy needs "postgresql://", but most hosts still hand out "postgres://"
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or f"sqlite:///{os.path.join(basedir, 'instance', 'tamagotchi.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Game tuning constants - kept here so the whole team can find/tweak them
    DECAY_PER_HOUR = {
        "hunger": 4.0,
        "happiness": 3.0,
        "energy": 2.5,
    }
    DAILY_BONUS_BASE = 10
    DAILY_BONUS_PER_STREAK_DAY = 2
    MINIGAME_PLAYS_PER_DAY = 3
    MINIGAME_COIN_RANGE = (5, 15)
    VISIT_TREAT_HAPPINESS = 10
    VISIT_TREAT_VISITOR_REWARD = 2

    # Free-action costs. Play and Sleep stay free; Feed costs coins so food
    # isn't infinite - encourages actually using the shop/mini-game/streak loop.
    CARE_ACTION_COSTS = {
        "feed": 5,
        "play": 0,
        "sleep": 0,
    }
