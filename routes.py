import os
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

# ----------------------
# Flask設定
# ----------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "icons")

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# DB作成
with app.app_context():
    db.create_all()
    # アイコン保存フォルダ作成（存在しない場合）
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ----------------------
# ユーザーロード
# ----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ----------------------
# 登録
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
# ログイン
# ----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("ログイン成功！")
            return redirect(url_for("profile"))
        flash("メールアドレスまたはパスワードが間違っています。")
    return render_template("login.html", form=form)


# ----------------------
# ログアウト
# ----------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("ログアウトしました。")
    return redirect(url_for("login"))


# ----------------------
# プロフィール表示
# ----------------------
@app.route("/profile")
@login_required
def profile():
    icon_url = url_for("static", filename=f"icons/{current_user.icon}")
    return render_template("profile.html", user=current_user, icon_url=icon_url)


# ----------------------
# プロフィール編集
# ----------------------
@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # ユーザー名と自己紹介を更新
        current_user.username = form.username.data
        current_user.bio = form.bio.data if hasattr(form, "bio") else current_user.bio

        # アイコン画像のアップロード
        if form.icon.data:
            filename = secure_filename(form.icon.data.filename)
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            form.icon.data.save(file_path)
            current_user.icon = filename

        db.session.commit()
        flash("プロフィールを更新しました！")
        return redirect(url_for("profile"))

    # GETリクエスト時：フォーム初期値セット
    form.username.data = current_user.username
    form.bio.data = getattr(current_user, "bio", "")
    return render_template("edit_profile.html", form=form)


# ----------------------
# メイン
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
