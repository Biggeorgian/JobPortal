import os
import secrets
import string
from PIL import Image
from flask import current_app

# ვაგენერირებთ შემთხვევით სტრიქონს ფოლდერების და ფაილების სახელებისთვის
def generate_random_string(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

# ატვირთულ ფოტოებს ვუცვლით სახელს, ვაპატარავებთ და ვინახავთ მომხმარებლის საქაღალდეში
def save_picture(form_picture, user_folder_name, output_size=(200, 200)):
    random_name = generate_random_string(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_name + ".jpg"
    directory_path = os.path.join(current_app.root_path, 'static/uploads', user_folder_name)

    # ვამოწმებთ და თუ საქაღალდე არ არსებობს, ვქმნით ახალს
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    picture_path = os.path.join(directory_path, picture_fn)

    # გადავაკონვერტიროთ სურათი, რომ პნგ და გიფების გამჭვირვალობა გავაქროთ
    i = Image.open(form_picture)
    if i.mode != 'RGB':
        i = i.convert('RGB')
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn