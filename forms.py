from flask_wtf import FlaskForm
from wtforms import StringField,IntegerField,SelectField,SubmitField,PasswordField,BooleanField
from wtforms.validators import DataRequired,NumberRange,InputRequired,Length


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=80)])
    remember = BooleanField('remember me')

allroles=[('SUPERADMIN','SUPERADMIN'),('Admin','Admin'),('Cashier','Cashier'),('Nurse','Nurse'),('Doctor','Doctor'),('Labtech','Labtech'),('Pharmacist','Pharmacist')]
class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=80)])
    memberrole = SelectField('Select Role',choices=allroles)
    submit = SubmitField('Add User')

class changepassForm(FlaskForm):
    editusername = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    editpassword = PasswordField('password', validators=[InputRequired(), Length(min=4, max=80)])
    editmemberrole = SelectField('Select Role',choices=allroles)
    submit = SubmitField('save')



