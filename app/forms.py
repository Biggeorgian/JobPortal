from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

# დავაიმპორტოთ კატეგორიები
from app.constants import CATEGORIES

class RegistrationForm(FlaskForm):
    username = StringField('მომხმარებლის სახელი', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('ელფოსტა', validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    confirm_password = PasswordField('გაიმეორეთ პაროლი', validators=[DataRequired(), EqualTo('password')])
    avatar = FileField('ატვირთეთ ავატარი', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    submit = SubmitField('რეგისტრაცია')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('მომხმარებელი ამ ელფოსტით უკვე დარეგისტრირებულია.')

class LoginForm(FlaskForm):
    email = StringField('ელფოსტა', validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    remember = BooleanField('დამახსოვრება')
    submit = SubmitField('ავტორიზაცია')

class CompanyForm(FlaskForm):
    name = StringField('კომპანიის სახელი', validators=[DataRequired()])
    address = StringField('მისამართი', validators=[DataRequired()])
    phone = StringField('ტელეფონი', validators=[DataRequired()])
    email = StringField('კომპანიის ელფოსტა', validators=[DataRequired(), Email()])
    logo = FileField('კომპანიის ლოგო', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('შენახვა')

class JobForm(FlaskForm):
    title = StringField('ვაკანსიის სათაური', validators=[DataRequired()])
    company = SelectField('აირჩიეთ კომპანია', coerce=int, validators=[DataRequired()])
    category = SelectField('კატეგორია', choices=CATEGORIES, validators=[DataRequired()])
    location = StringField('ლოკაცია', validators=[DataRequired()])  # PDF მოთხოვნა
    salary_min = IntegerField('მინიმალური ხელფასი', validators=[DataRequired()])
    salary_max = IntegerField('მაქსიმალური ხელფასი', validators=[DataRequired()])
    short_description = TextAreaField('მოკლე აღწერა', validators=[DataRequired(), Length(max=200)])
    full_description = TextAreaField('სრული აღწერა (HTML)', validators=[DataRequired()])
    is_published = BooleanField('გამოქვეყნება (მონიშნეთ თუ გსურთ საიტზე გამოჩენა)')
    submit = SubmitField('გამოქვეყნება')

class UpdateAccountForm(FlaskForm):
    username = StringField('მომხმარებლის სახელი', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('ელფოსტა', validators=[DataRequired(), Email()])
    password = PasswordField('ახალი პაროლი (სურვილისამებრ)')
    confirm_password = PasswordField('გაიმეორეთ პაროლი', validators=[EqualTo('password')])
    avatar = FileField('ავატარის განახლება', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    submit = SubmitField('განახლება')

    def validate_email(self, email):
        # ვამოწმებთ მხოლოდ იმ შემთხვევაში, თუ ელფოსტა შეიცვალა
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('მომხმარებელი ამ ელფოსტით უკვე დარეგისტრირებულია.')