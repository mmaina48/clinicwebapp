from flask_wtf import FlaskForm
from wtforms import StringField,IntegerField,SelectField,SubmitField,PasswordField,BooleanField
from wtforms.validators import DataRequired,NumberRange,InputRequired,Length


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=80)])
    submit = SubmitField('Add User')

class addproduct(FlaskForm):
    prodname = StringField('Product Name', validators=[DataRequired()])
    prodtype = StringField('Product Type', validators=[DataRequired()])
    sellprice=IntegerField('Sell Price', validators=[NumberRange(min=0, max=1000000),DataRequired()])
    reoderlevel=IntegerField('Reoder Level', validators=[NumberRange(min=0, max=1000000),DataRequired()])
    prodsubmit = SubmitField('Save Changes')



