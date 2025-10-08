from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import re

db = SQLAlchemy()

# -------------------------
# フォロー関係（中間テーブル）
# -------------------------
followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("users.id")),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    icon = db.Column(db.String(200), default="default.png")
    bio = db.Column(db.Text, default="")

    # -------------------------
    # フォロー関係
    # -------------------------
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    # -------------------------
    # コンストラクタ
    # -------------------------
    def __init__(self, username, email, password, icon="default.png", bio=""):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("メールアドレスの形式が不正です。")
        self.username = username
        self.email = email
        self.set_password(password)
        self.icon = icon
        self.bio = bio

    # -------------------------
    # パスワード関連
    # -------------------------
    def set_password(self, password: str):
        """パスワードをハッシュ化して保存"""
        if len(password) < 8:
            raise ValueError("パスワードは8文字以上にしてください。")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """パスワード検証"""
        return check_password_hash(self.password_hash, password)

    # -------------------------
    # フォロー関連メソッド
    # -------------------------
    def follow(self, user):
        """指定したユーザーをフォロー"""
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """フォロー解除"""
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user) -> bool:
        """フォロー中かどうかを判定"""
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_count(self) -> int:
        """フォローしている人数"""
        return self.followed.count()

    def followers_count(self) -> int:
        """フォロワーの人数"""
        return self.followers.count()

    def __repr__(self):
        return f"<User {self.username}>"
