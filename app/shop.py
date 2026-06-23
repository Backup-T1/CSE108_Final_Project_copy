from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user

from app.models import db, Item, InventoryItem, Gift, User, Friendship
from app.utils import can_play_minigame, play_minigame, minigame_plays_used_today
from sqlalchemy import or_, and_

shop_bp = Blueprint("shop", __name__, url_prefix="/shop")


@shop_bp.route("/")
@login_required
def shop_home():
    items = Item.query.all()

    accepted = Friendship.query.filter(
        Friendship.status == "accepted",
        or_(Friendship.requester_id == current_user.id, Friendship.addressee_id == current_user.id),
    ).all()
    friends = [f.addressee if f.requester_id == current_user.id else f.requester for f in accepted]

    return render_template(
        "shop/shop.html",
        items=items,
        friends=friends,
        can_play=can_play_minigame(current_user),
    )


@shop_bp.route("/buy/<int:item_id>", methods=["POST"])
@login_required
def buy(item_id):
    item = Item.query.get_or_404(item_id)
    if current_user.coins < item.cost:
        flash("Not enough coins for that.", "error")
        return redirect(url_for("shop.shop_home"))

    current_user.coins -= item.cost
    inv = InventoryItem.query.filter_by(user_id=current_user.id, item_id=item.id).first()
    if inv:
        inv.quantity += 1
    else:
        db.session.add(InventoryItem(user_id=current_user.id, item_id=item.id, quantity=1))

    db.session.commit()
    flash(f"Bought {item.emoji} {item.name} for {item.cost} coins.", "success")
    return redirect(url_for("shop.shop_home"))


@shop_bp.route("/gift/send", methods=["POST"])
@login_required
def send_gift():
    friend_id = request.form.get("friend_id", type=int)
    item_id = request.form.get("item_id", type=int)
    message = request.form.get("message", "").strip()[:200]

    friend = User.query.get_or_404(friend_id)
    item = Item.query.get_or_404(item_id)

    is_friend = Friendship.query.filter(
        Friendship.status == "accepted",
        or_(
            and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == friend.id),
            and_(Friendship.requester_id == friend.id, Friendship.addressee_id == current_user.id),
        ),
    ).first()
    if not is_friend:
        flash("You can only send gifts to friends.", "error")
        return redirect(url_for("shop.shop_home"))

    if current_user.coins < item.cost:
        flash("Not enough coins to send that gift.", "error")
        return redirect(url_for("shop.shop_home"))

    current_user.coins -= item.cost
    gift = Gift(sender_id=current_user.id, receiver_id=friend.id, item_id=item.id, message=message)
    db.session.add(gift)
    db.session.commit()

    flash(f"Sent {item.emoji} {item.name} to {friend.username}!", "success")
    return redirect(url_for("shop.shop_home"))


@shop_bp.route("/gifts")
@login_required
def gift_inbox():
    unopened = Gift.query.filter_by(receiver_id=current_user.id, opened=False).order_by(Gift.sent_at.desc()).all()
    opened = Gift.query.filter_by(receiver_id=current_user.id, opened=True).order_by(Gift.sent_at.desc()).limit(20).all()
    sent = Gift.query.filter_by(sender_id=current_user.id).order_by(Gift.sent_at.desc()).limit(20).all()
    return render_template("shop/gifts.html", unopened=unopened, opened=opened, sent=sent)


@shop_bp.route("/gifts/<int:gift_id>/open", methods=["POST"])
@login_required
def open_gift(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    if gift.receiver_id != current_user.id:
        flash("That's not your gift to open.", "error")
        return redirect(url_for("shop.gift_inbox"))
    if gift.opened:
        return redirect(url_for("shop.gift_inbox"))

    gift.opened = True
    inv = InventoryItem.query.filter_by(user_id=current_user.id, item_id=gift.item_id).first()
    if inv:
        inv.quantity += 1
    else:
        db.session.add(InventoryItem(user_id=current_user.id, item_id=gift.item_id, quantity=1))

    db.session.commit()
    flash(f"You opened a gift from {gift.sender.username}: {gift.item.emoji} {gift.item.name}!", "success")
    return redirect(url_for("shop.gift_inbox"))


@shop_bp.route("/minigame/play", methods=["POST"])
@login_required
def minigame_play():
    """Called via fetch() from the click-the-target mini-game in the dashboard."""
    payout = play_minigame(current_user)
    db.session.commit()

    plays_used = minigame_plays_used_today(current_user)
    max_plays = current_app.config["MINIGAME_PLAYS_PER_DAY"]

    if payout is None:
        return jsonify({
            "ok": False,
            "message": "No plays left today. Come back tomorrow!",
            "plays_used": plays_used,
            "max_plays": max_plays,
        }), 400

    return jsonify({
        "ok": True,
        "payout": payout,
        "coins": current_user.coins,
        "plays_used": plays_used,
        "max_plays": max_plays,
    })
