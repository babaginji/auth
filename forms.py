from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from flask_wtf.file import FileAllowed


class RegisterForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("メールアドレス", validators=[DataRequired(), Email()])
    password = PasswordField("パスワード", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("パスワード確認", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("登録")


class LoginForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("ログイン")


class EditProfileForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired(), Length(min=2, max=20)])
    bio = TextAreaField(
        "自己紹介",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "自己紹介を入力してください"},
    )
    icon = FileField(
        "アイコン画像をアップロード", validators=[FileAllowed(["jpg", "jpeg", "png"], "画像ファイルのみ！")]
    )
    submit = SubmitField("変更を保存")
