import os

class Config:
    # უსაფრთხოების გასაღები
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-puper-paroli-da-rame'

    # სად არისო მონაცემთა ბაზაო?
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app/database/site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ვუთითებთ სად აიტვირთოს მომხმარებლების ფაილები
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')