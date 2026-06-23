from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.models import db, User, Pet

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("pet.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if len(username) < 3:
            flash("Username needs to be at least 3 characters.", "error")
            return render_template("auth/signup.html")
        if len(password) < 6:
            flash("Password needs to be at least 6 characters.", "error")
            return render_template("auth/signup.html")
        if password != confirm:
            flash("Passwords don't match.", "error")
            return render_template("auth/signup.html")
        if User.query.filter_by(username=username).first():
            flash("That username is already taken.", "error")
            return render_template("auth/signup.html")

        user = User(username=username)
        user.set_password(password)  # hashed + salted, never stored in plain text
        db.session.add(user)
        db.session.flush()  # get user.id before creating the pet

        pet_name = request.form.get("pet_name", "").strip() or "Bud"
        species = request.form.get("species", "blob")
        pet = Pet(user_id=user.id, name=pet_name, species=species)
        db.session.add(pet)

        db.session.commit()

        login_user(user)
        flash(f"Welcome! {pet.name} is hatching and ready for you to take care of.", "success")
        return redirect(url_for("pet.dashboard"))

    return render_template("auth/signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("pet.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("pet.dashboard"))

        flash("Incorrect username or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
