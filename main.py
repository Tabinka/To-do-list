from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config["SECRET_KEY"] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

dictionary_tasks = {}
x = 0


# WTF FORM
class NewTask(FlaskForm):
    task_name = StringField("Task name", validators=[DataRequired()])
    date_time = DateField("Date")
    tag_name = StringField("Tag")
    submit = SubmitField("Add task")


class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///tasks.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CONFIGURE TABLES
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250))
    password = db.Column(db.String(250))
    task = relationship("Task", back_populates="user")


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'))
    task_name = db.Column(db.String(250))
    tag = db.Column(db.String(250))
    date = db.Column(db.String(250))
    user = relationship("User", back_populates="task")


db.create_all()


@app.route("/", methods=["POST", "GET"])
def home():
    global x
    form = NewTask()
    register_form = UserForm()
    if form.validate_on_submit():
        dictionary_tasks[x] = {"name": form.task_name.data, "tag": form.tag_name.data, "date": str(form.date_time.data)}
        print(dictionary_tasks)
        x += 1
        return redirect(url_for("home"))
    elif register_form.validate_on_submit() and request.method == "POST":
        new_user = User(
            username=register_form.name.data,
            password=generate_password_hash(password=request.form["password"], method='pbkdf2:sha256',
                                            salt_length=8)
        )
        print("user created")
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("index.html", form=form, tasks=dictionary_tasks, registere_form=register_form)


@app.route("/add", methods=["POST", "GET"])
def add_to_db():
    for key, value in dictionary_tasks.items():
        new_task = Task(
            task_name=value["name"],
            user_id=1,
            tag=value["tag"],
            date=value["date"]
        )
        db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/delete/<int:task_id>", methods=["POST", "GET"])
def delete(task_id):
    del dictionary_tasks[task_id]
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
