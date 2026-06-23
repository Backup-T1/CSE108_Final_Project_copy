"""
Run this any time you change the shop catalog:

    python seed.py

Safe to run as many times as you want - it adds anything in STARTER_ITEMS
that's missing by name, and removes anything in DISCONTINUED_ITEMS that's
still in the database (along with any gifts/inventory referencing it, so it
won't crash on existing test accounts).
"""

from app import create_app
from app.models import db, Item, InventoryItem, Gift

STARTER_ITEMS = [
    # name, emoji, type, cost, hunger, happiness, energy
    ("Apple", "🍎", "food", 8, 15, 0, 0),
    ("Pizza Slice", "🍕", "food", 15, 30, 5, 0),
    ("Fancy Cake", "🍰", "food", 30, 25, 20, 0),
    ("Squeaky Toy", "🧸", "toy", 10, 0, 20, -5),
    ("Beach Ball", "🏖️", "toy", 18, 0, 25, -10),
    ("Warm Blanket", "🧣", "rest", 16, 0, 0, 40),
    ("AirPods", "🎧", "toy", 45, 0, 30, 10),
    ("Cheetos", "🧀", "food", 10, 25, 15, -5),
    ("Energy Drink", "🥤", "drink", 18, 0, 5, 40),
    # --- new ---
    ("Paint", "🎨", "toy", 14, 0, 18, -5),
    ("Noodles", "🍜", "food", 12, 28, 5, 0),
    # --- funny "dangerous" novelty items ---
    ("Ghost Pepper", "🌶️", "food", 14, 20, -10, 10),       # adrenaline rush, but rough on happiness
    ("Rocket Fuel Soda", "🚀", "drink", 20, -5, 5, 50),     # absurd energy spike, basically jet fuel
    ("Dynamite Candy", "🧨", "food", 16, 10, 25, 15),       # explosively sugary, not actually explosive
]

# Items that used to be in STARTER_ITEMS but have been removed from the shop.
DISCONTINUED_ITEMS = ["Cozy Pillow", "Party Hat"]

app = create_app()
with app.app_context():
    created = 0
    for name, emoji, item_type, cost, hunger, happy, energy in STARTER_ITEMS:
        if Item.query.filter_by(name=name).first():
            continue
        db.session.add(
            Item(
                name=name,
                emoji=emoji,
                item_type=item_type,
                cost=cost,
                hunger_effect=hunger,
                happiness_effect=happy,
                energy_effect=energy,
            )
        )
        created += 1

    removed = 0
    for name in DISCONTINUED_ITEMS:
        item = Item.query.filter_by(name=name).first()
        if not item:
            continue
        InventoryItem.query.filter_by(item_id=item.id).delete()
        Gift.query.filter_by(item_id=item.id).delete()
        db.session.delete(item)
        removed += 1

    db.session.commit()
    print(f"Added {created} new item(s), removed {removed} discontinued item(s).")
    print(f"Shop now has {Item.query.count()} item(s) total.")
