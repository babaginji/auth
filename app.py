import os
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, flash, request, current_app
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.utils import secure_filename
from models import db, User
from forms import RegisterForm, LoginForm, EditProfileForm
from flask_wtf import CSRFProtect
from flask_mail import Mail, Message
from email_utils import send_otp_email

# ----------------------
# Flask 設定
# ----------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "icons")

# メール設定（環境変数から取得）
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
mail = Mail(app)


# ----------------------
# 拡張機能初期化
# ----------------------
db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ----------------------
# ユーザーローダー
# ----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ----------------------
# ルート: ホーム
# ----------------------
@app.route("/")
def index():
    users = User.query.all()
    return render_template("index.html", users=users)


# ----------------------
# ルート: 登録
# ----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("このメールアドレスはすでに登録されています。")
            return redirect(url_for("register"))
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        db.session.add(user)
        db.session.commit()
        flash("登録完了！ログインしてください。")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


# ----------------------
# ルート: ログイン
# ----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("ログイン成功！")
            return redirect(url_for("my_profile"))
        flash("メールアドレスまたはパスワードが間違っています。")
    return render_template("login.html", form=form)


# ----------------------
# ルート: ログアウト
# ----------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("ログアウトしました。")
    return redirect(url_for("login"))


# ----------------------
# ルート: プロフィール表示
# ----------------------
@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    icon_url = url_for("static", filename=f"icons/{user.icon}")
    is_following = current_user.is_following(user) if user != current_user else None
    return render_template(
        "profile.html",
        user=user,
        icon_url=icon_url,
        is_following=is_following,
    )


@app.route("/profile")
@login_required
def my_profile():
    return redirect(url_for("profile", user_id=current_user.id))


# ----------------------
# ルート: プロフィール編集
# ----------------------
@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit() or request.method == "POST":
        current_user.username = form.username.data
        current_user.bio = (
            getattr(form, "bio", None)
            and form.bio.data
            or getattr(current_user, "bio", "")
        )
        cropped_file = request.files.get("cropped_icon")
        if cropped_file:
            filename = secure_filename(cropped_file.filename)
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            cropped_file.save(file_path)
            current_user.icon = filename
        db.session.commit()
        flash("プロフィールを更新しました！")
        return redirect(url_for("my_profile"))
    form.username.data = current_user.username
    form.bio.data = getattr(current_user, "bio", "")
    return render_template("edit_profile.html", form=form, user=current_user)


# ----------------------
# フォロー/解除
# ----------------------
@app.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user != current_user and not current_user.is_following(user):
        current_user.follow(user)
        db.session.commit()
        flash(f"{user.username} をフォローしました！")
    return redirect(url_for("profile", user_id=user_id))


@app.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    if user != current_user and current_user.is_following(user):
        current_user.unfollow(user)
        db.session.commit()
        flash(f"{user.username} のフォローを解除しました。")
    return redirect(url_for("profile", user_id=user_id))


# ----------------------
# フォロー一覧取得（モーダル用）
# ----------------------
@app.route("/followers/<int:user_id>")
@login_required
def followers(user_id):
    user = User.query.get_or_404(user_id)
    followers_list = [
        {"id": u.id, "username": u.username, "icon": u.icon} for u in user.followers
    ]
    return render_template("follow_list.html", title="フォロワー", users=followers_list)


@app.route("/following/<int:user_id>")
@login_required
def following(user_id):
    user = User.query.get_or_404(user_id)
    following_list = [
        {"id": u.id, "username": u.username, "icon": u.icon} for u in user.followed
    ]
    return render_template("follow_list.html", title="フォロー", users=following_list)


# ----------------------
# パスワード変更
# ----------------------
@app.route("/change_password", methods=["GET", "POST"])
@csrf.exempt
@login_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password")
        new_pw = request.form.get("new_password")
        confirm_pw = request.form.get("confirm_password")
        if not current_user.check_password(current_pw):
            flash("現在のパスワードが間違っています。", "danger")
        elif new_pw != confirm_pw:
            flash("新しいパスワードが一致しません。", "danger")
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash("パスワードを変更しました。", "success")
            return redirect(url_for("profile", user_id=current_user.id))
    return render_template("change_password.html")


# ----------------------
# アカウント設定（公開/非公開・通知・ダークモード）
# ----------------------
@app.route("/toggle_visibility")
@login_required
def toggle_visibility():
    current_user.is_public = not current_user.is_public
    db.session.commit()
    flash(f"アカウントを{'公開' if current_user.is_public else '非公開'}にしました。", "success")
    return redirect(url_for("my_profile"))


@app.route("/toggle_follow_notifications")
@login_required
def toggle_follow_notifications():
    current_user.follow_notify = not current_user.follow_notify
    db.session.commit()
    flash(f"フォロー通知を{'ON' if current_user.follow_notify else 'OFF'}にしました。", "success")
    return redirect(url_for("my_profile"))


@app.route("/toggle_comment_notifications")
@login_required
def toggle_comment_notifications():
    current_user.comment_notify = not current_user.comment_notify
    db.session.commit()
    flash(f"コメント通知を{'ON' if current_user.comment_notify else 'OFF'}にしました。", "success")
    return redirect(url_for("my_profile"))


@app.route("/toggle_dark_mode")
@login_required
def toggle_dark_mode():
    current_user.dark_mode = not current_user.dark_mode
    db.session.commit()
    flash(f"ダークモードを{'ON' if current_user.dark_mode else 'OFF'}にしました。", "success")
    return redirect(url_for("my_profile"))


# ----------------------
# ワンタイムパスワードによるパスワード再設定
# ----------------------
from email_utils import send_otp_email


@app.route("/reset", methods=["GET", "POST"])
@csrf.exempt
def reset_request():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if user:
            code = user.set_otp()
            db.session.commit()
            # 同期でメール送信
            send_otp_email(user, code)
            flash("確認コードをメールに送信しました。")
            return redirect(url_for("reset_verify", email=email))
        else:
            flash("メールアドレスが見つかりません。")
    return render_template("reset_request.html")


@app.route("/reset/verify", methods=["GET", "POST"])
@csrf.exempt
def reset_verify():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if request.method == "POST":
        code = request.form["code"]
        if user and user.verify_otp(code):
            flash("コード認証に成功しました。新しいパスワードを設定してください。")
            return redirect(url_for("reset_password", email=email))
        else:
            flash("コードが無効または期限切れです。")
    return render_template("reset_verify.html")


@app.route("/reset/password", methods=["GET", "POST"])
@csrf.exempt
def reset_password():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if request.method == "POST":
        new_password = request.form["password"]
        try:
            user.set_password(new_password)
            user.clear_otp()
            db.session.commit()
            flash("パスワードを更新しました。ログインしてください。")
            return redirect(url_for("login"))
        except ValueError as e:
            flash(str(e))
    return render_template("reset_password.html")


# DB初期化
# ----------------------
with app.app_context():
    db.create_all()
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ----------------------
# メイン
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
