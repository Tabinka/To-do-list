from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired
from sqlalchemy.ext.declarative import declarative_base
from flask_fontawesome import FontAwesome

app = Flask(__name__)
app.config["SECRET_KEY"] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
fa = FontAwesome(app)

dictionary_tasks = {}
x = 0


# WTF FORM
class NewTask(FlaskForm):
    task_name = StringField("Task name", validators=[DataRequired()], render_kw={"placeholder": "Task Name"})
    date_time = DateField("Date")
    tag_name = StringField("Tag", render_kw={"placeholder": "Tag Name"})
    submit = SubmitField("Add task")


class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    register = SubmitField("Register")


class LoginForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Login")


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///tasks.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
Base = declarative_base()


# CONFIGURE TABLES
class User(UserMixin, db.Model, Base):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250))
    password = db.Column(db.String(250))
    task = relationship("Task", back_populates="user")


class Task(db.Model, Base):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'))
    task_name = db.Column(db.String(250))
    tag = db.Column(db.String(250))
    date = db.Column(db.String(250))
    user = relationship("User", back_populates="task")


db.create_all()


def add_to_db():
    global dictionary_tasks
    for key, value in dictionary_tasks.items():
        new_task = Task(
            task_name=value["name"],
            user_id=current_user.get_id(),
            tag=value["tag"],
            date=value["date"]
        )
        db.session.add(new_task)
    db.session.commit()
    dictionary_tasks = {}


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def logged_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route("/", methods=["POST", "GET"])
def home():
    global x
    db_tasks = None
    form = NewTask()
    register_form = UserForm()
    login_form = LoginForm()
    if form.submit.data and form.validate():
        if current_user.is_authenticated:
            new_task = Task(
                task_name=form.task_name.data,
                user_id=1,
                tag=form.tag_name.data,
                date=str(form.date_time.data)
            )
            db.session.add(new_task)
            db.session.commit()
        else:
            dictionary_tasks[x] = {"name": form.task_name.data, "tag": form.tag_name.data,
                                   "date": str(form.date_time.data)}
            x += 1
        return redirect(url_for("home"))
    elif login_form.login.data and login_form.validate():
        if User.query.filter_by(username=request.form['name']).first():
            user = User.query.filter_by(username=request.form['name']).first()
            if check_password_hash(user.password, request.form['password']):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Wrong password.")
        else:
            flash("User does not exist.")
    elif register_form.register.data and register_form.validate():
        new_user = User(
            username=register_form.name.data,
            password=generate_password_hash(password=request.form["password"], method='pbkdf2:sha256',
                                            salt_length=8)
        )
        flash("User registered.")
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))
    if current_user.is_authenticated:
        if dictionary_tasks:
            add_to_db()
        db_tasks = Task.query.all()
    return render_template("index.html", form=form, local_tasks=dictionary_tasks, db_tasks=db_tasks,
                           registere_form=register_form,
                           login_form=login_form, logged_user=current_user.is_authenticated)


@app.route("/delete/<int:task_id>", methods=["POST", "GET"])
def delete(task_id):
    if current_user.is_authenticated:
        task_to_delete = Task.query.get(task_id)
        db.session.delete(task_to_delete)
        db.session.commit()
    else:
        del dictionary_tasks[task_id]
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
