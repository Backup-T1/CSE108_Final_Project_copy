from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_

from app.models import db, User, Friendship, VisitTreat
from app.utils import tick_pet
from config import Config

social_bp = Blueprint("social", __name__, url_prefix="/friends")


def _friendship_between(user_id_a, user_id_b):
    return Friendship.query.filter(
        or_(
            and_(Friendship.requester_id == user_id_a, Friendship.addressee_id == user_id_b),
            and_(Friendship.requester_id == user_id_b, Friendship.addressee_id == user_id_a),
        )
    ).first()


@social_bp.route("/")
@login_required
def friends_list():
    accepted = Friendship.query.filter(
        Friendship.status == "accepted",
        or_(Friendship.requester_id == current_user.id, Friendship.addressee_id == current_user.id),
    ).all()

    friends = []
    for f in accepted:
        friend = f.addressee if f.requester_id == current_user.id else f.requester
        friend_pet = friend.pet
        if friend_pet:
            tick_pet(friend_pet)
        friends.append(friend)
    db.session.commit()

    incoming = Friendship.query.filter_by(addressee_id=current_user.id, status="pending").all()

    return render_template("social/friends.html", friends=friends, incoming=incoming)


@social_bp.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    results = []
    if q:
        results = (
            User.query.filter(User.username.ilike(f"%{q}%"), User.id != current_user.id)
            .limit(20)
            .all()
        )
    return render_template("social/friends.html", search_query=q, results=results,
                            friends=[], incoming=Friendship.query.filter_by(
                                addressee_id=current_user.id, status="pending").all())


@social_bp.route("/request/<int:user_id>", methods=["POST"])
@login_required
def send_request(user_id):
    if user_id == current_user.id:
        flash("You can't friend yourself.", "error")
        return redirect(url_for("social.friends_list"))

    target = User.query.get_or_404(user_id)
    existing = _friendship_between(current_user.id, target.id)
    if existing:
        flash("There's already a friend request or friendship with that user.", "error")
        return redirect(url_for("social.friends_list"))

    fr = Friendship(requester_id=current_user.id, addressee_id=target.id, status="pending")
    db.session.add(fr)
    db.session.commit()
    flash(f"Friend request sent to {target.username}.", "success")
    return redirect(url_for("social.friends_list"))


@social_bp.route("/respond/<int:friendship_id>/<action>", methods=["POST"])
@login_required
def respond(friendship_id, action):
    fr = Friendship.query.get_or_404(friendship_id)
    if fr.addressee_id != current_user.id:
        flash("That request isn't yours to respond to.", "error")
        return redirect(url_for("social.friends_list"))

    if action == "accept":
        fr.status = "accepted"
        db.session.commit()
        flash(f"You and {fr.requester.username} are now friends!", "success")
    elif action == "decline":
        db.session.delete(fr)
        db.session.commit()
        flash("Request declined.", "info")

    return redirect(url_for("social.friends_list"))


@social_bp.route("/visit/<int:user_id>")
@login_required
def visit(user_id):
    host = User.query.get_or_404(user_id)
    fr = _friendship_between(current_user.id, host.id)
    if not fr or fr.status != "accepted":
        flash("You can only visit friends.", "error")
        return redirect(url_for("social.friends_list"))

    pet = host.pet
    tick_pet(pet)
    db.session.commit()

    already_treated_today = VisitTreat.query.filter_by(
        visitor_id=current_user.id, host_id=host.id, visit_date=date.today()
    ).first() is not None

    reaction = request.args.get("reacted", "")
    if reaction not in {"feed", "play", "sleep"}:
        reaction = ""

    return render_template(
        "social/visit.html", host=host, pet=pet,
        already_treated_today=already_treated_today, reaction=reaction,
    )


@social_bp.route("/visit/<int:user_id>/treat", methods=["POST"])
@login_required
def give_treat(user_id):
    host = User.query.get_or_404(user_id)
    fr = _friendship_between(current_user.id, host.id)
    if not fr or fr.status != "accepted":
        flash("You can only visit friends.", "error")
        return redirect(url_for("social.friends_list"))

    already = VisitTreat.query.filter_by(
        visitor_id=current_user.id, host_id=host.id, visit_date=date.today()
    ).first()
    if already:
        flash("You already gave this pet a treat today. Come back tomorrow!", "info")
        return redirect(url_for("social.visit", user_id=user_id))

    pet = host.pet
    tick_pet(pet)
    pet.happiness = min(100.0, pet.happiness + Config.VISIT_TREAT_HAPPINESS)
    current_user.coins += Config.VISIT_TREAT_VISITOR_REWARD

    db.session.add(VisitTreat(visitor_id=current_user.id, host_id=host.id))
    db.session.commit()

    flash(
        f"You gave {pet.name} a treat! (+{Config.VISIT_TREAT_HAPPINESS} happiness for them, "
        f"+{Config.VISIT_TREAT_VISITOR_REWARD} coins for you)",
        "success",
    )
    return redirect(url_for("social.visit", user_id=user_id, reacted="play"))
