from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """
    A registered player. Passwords are never stored in plain text.
    werkzeug.security.generate_password_hash uses PBKDF2-SHA256 with a
    random per-user salt baked into the resulting string, so two users
    with the same password get completely different hashes.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    coins = db.Column(db.Integer, default=100, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    last_daily_bonus = db.Column(db.Date, nullable=True)
    last_minigame_date = db.Column(db.Date, nullable=True)
    minigame_plays_today = db.Column(db.Integer, default=0)

    pet = db.relationship("Pet", backref="owner", uselist=False, cascade="all, delete-orphan")
    inventory_items = db.relationship("InventoryItem", backref="owner", cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class Pet(db.Model):
    """One pet per user. Stats decay over real elapsed time - see app/utils.py:tick_pet"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)

    name = db.Column(db.String(50), default="Bud")
    species = db.Column(db.String(30), default="blob")  # blob, dino, kitty - drives CSS art variant

    hunger = db.Column(db.Float, default=100.0)
    happiness = db.Column(db.Float, default=100.0)
    energy = db.Column(db.Float, default=100.0)

    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    streak_days = db.Column(db.Integer, default=0)
    last_care_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def stage(self):
        if self.streak_days >= 10:
            return "adult"
        if self.streak_days >= 4:
            return "teen"
        return "baby"

    @property
    def mood(self):
        """A simple derived state the templates use to pick a face/expression."""
        avg = (self.hunger + self.happiness + self.energy) / 3
        if min(self.hunger, self.happiness, self.energy) <= 15:
            return "critical"
        if avg >= 70:
            return "happy"
        if avg >= 40:
            return "neutral"
        return "sad"


class Friendship(db.Model):
    """
    One row per friend relationship. requester sends the request;
    status is 'pending' until the other user accepts, then 'accepted'.
    """

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending | accepted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requester = db.relationship("User", foreign_keys=[requester_id])
    addressee = db.relationship("User", foreign_keys=[addressee_id])

    __table_args__ = (db.UniqueConstraint("requester_id", "addressee_id", name="uq_friend_pair"),)


class Item(db.Model):
    """Shop catalog. Seeded once by seed.py - see that file to add more items."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    emoji = db.Column(db.String(10), default="🎁")
    item_type = db.Column(db.String(20), default="food")  # food | toy | rest | decoration
    cost = db.Column(db.Integer, default=10)
    hunger_effect = db.Column(db.Float, default=0)
    happiness_effect = db.Column(db.Float, default=0)
    energy_effect = db.Column(db.Float, default=0)


class InventoryItem(db.Model):
    """Items a user owns (bought themselves, or received and opened as a gift)."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    quantity = db.Column(db.Integer, default=0)

    item = db.relationship("Item")

    __table_args__ = (db.UniqueConstraint("user_id", "item_id", name="uq_user_item"),)


class Gift(db.Model):
    """A gift sent from one user to a friend. Sits unopened until the receiver opens it."""

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    message = db.Column(db.String(200), default="")
    opened = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])
    item = db.relationship("Item")


class VisitTreat(db.Model):
    """
    Tracks 'I gave my friend's pet a treat today' so one visitor can't
    spam a friend's pet with unlimited free happiness boosts.
    """

    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    visit_date = db.Column(db.Date, default=date.today)

    __table_args__ = (db.UniqueConstraint("visitor_id", "host_id", "visit_date", name="uq_visit_per_day"),)
