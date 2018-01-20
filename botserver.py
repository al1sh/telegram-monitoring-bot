from flask import Flask
from flask import flash, request, redirect, url_for, render_template
from flask_mail import Message, Mail
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, TextAreaField, validators, ValidationError

from werkzeug import secure_filename

import os
# from dbhelper import DBHelper
from telegram import handle_update
import json

mail = Mail()



class ContactForm(FlaskForm):
  name = StringField("Name", [validators.DataRequired("Please enter your name.")])
  email = StringField("Email", [validators.DataRequired(), validators.Email("Please enter your email.")])
  subject = StringField("Subject", [validators.DataRequired("Please enter subject.")])
  message = TextAreaField("Message", [validators.DataRequired("Please enter your message text.")])
  answer = IntegerField("Antispam question: 7 + 5 = ?", [validators.DataRequired("Please enter your answer."),
                                                         validators.NumberRange(min=11, max=13,
                                                                                message="Incorrect answer")

])
  submit = SubmitField("Send", [validators.DataRequired()])

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'Uploads/')
ALLOWED_EXTENSIONS = set(['txt', 'jpg', 'jpeg'])

app = Flask(__name__)
app.secret_key = 'development key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'firstrestrest@gmail.com'
app.config["MAIL_PASSWORD"] = 'your-password'

mail.init_app(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
@app.route('/index')
def index():
    # return "Hello {}".format("python executed code here")
    return render_template('index.html')


@app.route('/skills')
def skills():
    return render_template('skills.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()

    if request.method == 'POST':
        if not form.validate():
            flash('All fields are required.')
            return render_template('contact.html', form=form)
        else:


            # msg = Message(form.subject.data, sender='contact@example.com', recipients=['your_email@example.com'])
            # msg.body = """
            #       From: %s <%s>
            #       %s
            #       """ % (form.name.data, form.email.data, form.message.data)
            # mail.send(msg)

            return render_template('contact.html', form=form, success=True)

    elif request.method == 'GET':
        return render_template('contact.html', form=form)


@app.route('/blog')
def blog():
    return render_template('blog.html')

# ***************** PROJECTS ****************
@app.route("/cryptobot")
def cryptobot():
    return render_template("cryptobot.html")

@app.route("/opengl_physics")
def opengl_physics():
    return render_template("opengl_physics.html")

@app.route("/encryptor")
def encryptor():
    return render_template("encryptor.html")

@app.route("/server")
def server():
    return render_template("server.html")

@app.route("/parser")
def parser():
    return render_template("parser.html")

@app.route("/chatapp")
def chatapp():
    return render_template("chatapp.html")



@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print("incoming post request")
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print(app.config['UPLOAD_FOLDER'])
            print(filename)
            file.save(filename)
            # os.path.join(app.config['UPLOAD_FOLDER'], filename)
            return 'File uploaded'
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''



# @app.route('/upload')
# def upload_file_render():
#    return render_template('upload.html')
#
# @app.route('/uploader', methods = ['GET', 'POST'])
# def upload_file():
#    if request.method == 'POST':
#       f = request.files['file']
#       f.save(secure_filename(f.filename))
#       return 'file uploaded successfully'

@app.route("/bot", methods=["POST","GET"])
def server_response():
    update = request.data.decode("utf8")
    if len(update) == 0:
        return "No update"
    update = json.loads(update)
    handle_update(update)
    return ""


if __name__ == "__main__":
    app.run(host='0.0.0.0')
