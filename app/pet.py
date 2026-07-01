from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.models import db, InventoryItem
from app.utils import tick_pet, register_care_action, can_play_minigame, minigame_plays_used_today

pet_bp = Blueprint("pet", __name__)


ALLOWED_REACTIONS = {"feed", "play", "sleep"}


@pet_bp.route("/")
@login_required
def dashboard():
    pet = current_user.pet
    tick_pet(pet)
    db.session.commit()

    inventory = (
        InventoryItem.query.filter_by(user_id=current_user.id)
        .filter(InventoryItem.quantity > 0)
        .all()
    )

    reaction = request.args.get("reacted", "")
    if reaction not in ALLOWED_REACTIONS:
        reaction = ""

    # Species default colors (used when pet.color is None)
    if pet.species == "dino":
        default_color = "#7FD694"
        default_color_name = "Green"
    elif pet.species == "kitty":
        default_color = "#ECE9F4"
        default_color_name = "White"
    elif pet.species == "blob":
        default_color = "#F7B8D2"
        default_color_name = "Pink"


    return render_template(
        "pet/dashboard.html",
        pet=pet,
        default_color=default_color,
        default_color_name=default_color_name,
        inventory=inventory,
        reaction=reaction,
        minigame_plays_used=minigame_plays_used_today(current_user),
        minigame_can_play=can_play_minigame(current_user),
        minigame_max_plays=current_app.config["MINIGAME_PLAYS_PER_DAY"],
    )

@pet_bp.route("/customize", methods=["GET", "POST"])
@login_required
def customize():
    pet = current_user.pet

    # Species default colors (used when pet.color is None)
    if pet.species == "dino":
        default_color = "#7FD694"
        default_color_name = "Green"
    elif pet.species == "kitty":
        default_color = "#ECE9F4"
        default_color_name = "White"
    elif pet.species == "blob":
        default_color = "#F7B8D2"
        default_color_name = "Pink"

    if request.method == "POST":
        chosen_color = request.form.get("color")

        # Default → species color
        if chosen_color == "":
            pet.color = None
        else:
            pet.color = chosen_color

        pet.accessory = request.form.get("accessory", pet.accessory)
        pet.background = request.form.get("background", pet.background)

        db.session.commit()
        flash("Your pet's look has been updated!", "success")
        return redirect(url_for("pet.dashboard"))

    return render_template(
        "pet/customize.html",
        pet=pet,
        default_color=default_color,
        default_color_name=default_color_name
    )

@pet_bp.route("/care/<action>", methods=["POST"])
@login_required
def care(action):
    if action not in {"feed", "play", "sleep"}:
        flash("Unknown action.", "error")
        return redirect(url_for("pet.dashboard"))

    pet = current_user.pet
    tick_pet(pet)

    cost = current_app.config["CARE_ACTION_COSTS"].get(action, 0)
    if cost and current_user.coins < cost:
        flash(f"You need {cost} coins to feed {pet.name}. Try the shop or the coin game.", "error")
        return redirect(url_for("pet.dashboard"))

    if action == "feed":
        pet.hunger = min(100.0, pet.hunger + 20)
    elif action == "play":
        pet.happiness = min(100.0, pet.happiness + 20)
        pet.energy = max(0.0, pet.energy - 5)  # playing costs a little energy
    elif action == "sleep":
        pet.energy = min(100.0, pet.energy + 30)

    if cost:
        current_user.coins -= cost

    bonus = register_care_action(pet)
    db.session.commit()

    if cost and bonus:
        flash(f"Fed {pet.name} for {cost} coins. Day {pet.streak_days} care streak! +{bonus} coins.", "success")
    elif cost:
        flash(f"Fed {pet.name} for {cost} coins.", "success")
    elif bonus:
        flash(f"Day {pet.streak_days} care streak! +{bonus} coins.", "success")

    return redirect(url_for("pet.dashboard", reacted=action))


@pet_bp.route("/use-item/<int:item_id>", methods=["POST"])
@login_required
def use_item(item_id):
    pet = current_user.pet
    tick_pet(pet)

    inv = InventoryItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if not inv or inv.quantity <= 0:
        flash("You don't have that item.", "error")
        return redirect(url_for("pet.dashboard"))

    item = inv.item
    pet.hunger = min(100.0, pet.hunger + item.hunger_effect)
    pet.happiness = min(100.0, pet.happiness + item.happiness_effect)
    pet.energy = min(100.0, pet.energy + item.energy_effect)

    # Whichever stat the item boosts the most decides which reaction animation plays.
    effect_to_reaction = {
        "feed": item.hunger_effect,
        "play": item.happiness_effect,
        "sleep": item.energy_effect,
    }
    reaction = max(effect_to_reaction, key=effect_to_reaction.get)

    inv.quantity -= 1
    bonus = register_care_action(pet)
    db.session.commit()

    msg = f"Used {item.name} on {pet.name}."
    if bonus:
        msg += f" Day {pet.streak_days} care streak! +{bonus} coins."
    flash(msg, "success")
    return redirect(url_for("pet.dashboard", reacted=reaction))


@pet_bp.route("/rename", methods=["POST"])
@login_required
def rename():
    new_name = request.form.get("name", "").strip()
    if new_name:
        current_user.pet.name = new_name[:50]
        db.session.commit()
        flash("Name updated.", "success")
    return redirect(url_for("pet.dashboard"))
