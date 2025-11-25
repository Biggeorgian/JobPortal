import os
import logging
from flask import render_template, url_for, flash, redirect, request, abort, current_app
from app import application, db
from app.forms import RegistrationForm, LoginForm, CompanyForm, JobForm, UpdateAccountForm
from app.models import User, Company, Job
from flask_login import login_user, current_user, logout_user, login_required
from app.utils import save_picture, generate_random_string
import requests

# დავაიმპორტოთ კატეგორიების სია
from app.constants import CATEGORY_NAMES
@application.context_processor
def inject_categories():
    return dict(category_names=CATEGORY_NAMES)

# მოვამზადოთ ლოგი
logging.basicConfig(filename='app.log', level=logging.INFO, encoding='utf-8',
                    format='%(asctime)s %(levelname)s: %(message)s')

# დავუკავშირდეთ ორ API-ის და შემოვიტანოთ ამინდი, ვალუტის კურსი და ბიტკოინის ფასი
def get_api_data():
    data = {'weather': 'N/A', 'usd': 'N/A', 'eur': 'N/A', 'btc': 'N/A'}
    try:
        # წამოვიღეთ ამინდი
        weather_res = requests.get(
            'https://api.open-meteo.com/v1/forecast?latitude=41.71&longitude=44.82&current_weather=true')
        if weather_res.status_code == 200:
            data['weather'] = weather_res.json()['current_weather']['temperature']

        # წამოვიღეთ ბიტკოინის ფასი
        crypto_res = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
        if crypto_res.status_code == 200:
            data['btc'] = crypto_res.json()['bitcoin']['usd']

        # წამოვიღთ NBG-ის დოლარის და ევროს კურსი
        nbg_res = requests.get('https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/ka/json')
        if nbg_res.status_code == 200:
            currencies = nbg_res.json()[0]['currencies']
            for cur in currencies:
                if cur['code'] == 'USD':
                    data['usd'] = cur['rate']
                elif cur['code'] == 'EUR':
                    data['eur'] = cur['rate']

    except Exception as e:
        logging.error(f"API შეცდომა: {e}")

    return data

# დავიწყოთ როუტების გაწერა
# მთავარი გვერდის ლოგიკა
@application.route("/")
@application.route("/home")
def home():
    # შემოვიტანოთ api მონაცემები
    api_data = get_api_data()
    # შემოვიტანოთ ყველაფერი დანარჩენი
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category')
    company_filter = request.args.get('company_id', type=int)
    location_filter = request.args.get('location')

    # მოვამზადოთ რექვესტი - მხოლოდ გამოქვეყნებული ვაკანსიები!
    query = Job.query.filter_by(is_published=True)

    # თუ მომხმარებელი აირჩევს რამე კატეგორიას
    if category_filter:
        query = query.filter_by(category=category_filter)
    # თუ მომხმარებელი აირჩევს კონკრეტულ კომპანიას
    if company_filter:
        query = query.filter_by(company_id=company_filter)
    # თუ მომხმარებელი აირჩევს კონკრეტულ ქალაქს
    if location_filter:
        query = query.filter_by(location=location_filter)

    # გავანაწილოთ გვერდებზე ე.წ. პაგინაციის მეთოდით
    jobs = query.order_by(Job.date_posted.desc()).paginate(page=page, per_page=5)

    # გვერდით სვეტში გამოვიტანოთ აქტიური კატეგორიები და ქალაქები (მხოლოდ გამოქვეყნებული ვაკანსიებიდან)
    # აქ ვიყენებთ filter_by(is_published=True)-ს, რომ ცარიელი კატეგორიები არ გამოჩნდეს
    active_categories = [r[0] for r in db.session.query(Job.category).filter_by(is_published=True).distinct()]
    active_locations = [r[0] for r in db.session.query(Job.location).filter_by(is_published=True).distinct()]

    # გადავცეთ ყველა ცვლადი შაბლონს
    return render_template('home.html',
                           jobs=jobs,
                           api_data=api_data,
                           current_category=category_filter,
                           current_company=company_filter,
                           current_location=location_filter,
                           active_categories=active_categories,
                           active_locations=active_locations)

# ჩვენ შესახებ
@application.route("/about", methods=['GET', 'POST'])
def about():
    # შემოვიტანოთ api მონაცემები
    api_data = get_api_data()

    return render_template('about.html', title='ჩვენ შესახებ', api_data=api_data,)

# მომხმარებლების რეგისტრაცია
@application.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        random_folder = generate_random_string(8)
        full_path = os.path.join(current_app.root_path, 'static/uploads', random_folder)
        if not os.path.exists(full_path):
            os.makedirs(full_path)

        avatar_file = 'default.jpg'
        if form.avatar.data:
            avatar_file = save_picture(form.avatar.data, random_folder)

        # მოვამზადოთ ცვლადები
        user = User(username=form.username.data,
                    email=form.email.data,
                    avatar=avatar_file,
                    user_folder=random_folder)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # დავლოგოთ და გამოვიტანოთ flash შეტყობინება
        logging.info(f'დარეგისტრირდა მომხმარებელი: {user.username}')
        flash('გილოცავთ! თქვენი ანგარიში უკვე შეიქმნა! გთხოვთ გაიაროთ ავტორიზაცია.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='მომხმარებლის რეგისტრაცია', form=form)

# მომხმარებლის ავტორიზაცია
@application.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            logging.info(f'წარმატებული ავტორიზაცია: {user.username}')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            # ვლოგავთ შეცდომას და გამოგვაქვს flash შეტყობინება
            logging.warning(f'ავტორიზაცია ვერ მოხერხდა, მომხმარებელი: {form.email.data}')
            flash('სამწუხაროდ ავტორიზაცია ვერ მოხერხდა. შეამოწმეთ ელფოსტა და პაროლი', 'success')

    return render_template('login.html', title='მომხმარებლის ავტორიზაცია', form=form)

# სისტემიდან გამოსვლა
@application.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# მომხმარებლის პროფილის გვერდი
@application.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateAccountForm()

    if form.validate_on_submit():
        # განვაახლოთ მომხმარებლის ავატარი
        if form.avatar.data:
            picture_file = save_picture(form.avatar.data, current_user.user_folder)
            current_user.avatar = picture_file

        # განვაახლოთ ტექსტური ველები
        current_user.username = form.username.data
        current_user.email = form.email.data

        # პაროლი შევცვალოთ მხოლოდ მაშინ, თუ ეს ველი შეავსო
        if form.password.data:
            current_user.set_password(form.password.data)

        db.session.commit()
        flash('თქვენი პროფილი წარმატებით განახლდა!', 'success')
        return redirect(url_for('profile'))

    elif request.method == 'GET':
        # შევავსოთ გამოძახებული ფორმა არსებული მონაცემებით
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('profile.html', title='მომხმარებლის პროფილი', form=form)

# შევქმნათ კომპანია
@application.route("/company/new", methods=['GET', 'POST'])
@login_required
def new_company():
    form = CompanyForm()
    if form.validate_on_submit():
        logo_file = 'default_company.jpg'
        if form.logo.data:
            logo_file = save_picture(form.logo.data, current_user.user_folder)

        # ამოვიკითხოთ შევსებული ფორმა
        company = Company(name=form.name.data,
                          address=form.address.data,
                          phone=form.phone.data,
                          email=form.email.data,
                          logo=logo_file,
                          owner=current_user)
        db.session.add(company)
        db.session.commit()
        flash('გილოცავთ! კომპანია წარმატებით შეიქმნა', 'success')
        return redirect(url_for('home'))
    return render_template('create_company.html', title='კომპანიის დამატება', form=form)

# დავამატოთ ვაკანსია
@application.route("/job/new", methods=['GET', 'POST'])
@login_required
def new_job():
    if not current_user.companies:
        flash('ვაკანსიის დამატებამდე აუცილებელია დამსაქმებელი კომპანიის შექმნა!', 'warning')
        return redirect(url_for('new_company'))

    form = JobForm()
    form.company.choices = [(c.id, c.name) for c in current_user.companies]

    if form.validate_on_submit():
        job = Job(title=form.title.data,
                  short_description=form.short_description.data,
                  full_description=form.full_description.data,
                  category=form.category.data,
                  location=form.location.data,
                  salary_min=form.salary_min.data,
                  salary_max=form.salary_max.data,
                  company_id=form.company.data,
                  is_published=form.is_published.data)  # ახალი ველი: სტატუსი
        db.session.add(job)
        db.session.commit()

        # ლოგირების ტექსტი ოდნავ განვაახლოთ, რომ ჩანდეს სტატუსი
        status_text = "გამოქვეყნდა" if form.is_published.data else "შეინახა და ელოდება გამოქვეყნებას"
        logging.info(f'დაემატა ვაკანსია ({status_text}): {job.title}, ავტორი: {current_user.username}')

        flash(f'გილოცავთ, თქვენი ვაკანსია {status_text}!', 'success')
        return redirect(url_for('home'))

    # დეფოლტად მონიშნული იყოს გამოქვეყნება
    if request.method == 'GET':
        form.is_published.data = True

    return render_template('create_job.html', title='ვაკანსიის დამატება', form=form, legend='ახალი ვაკანსია')

# ვაკანსიის სრული ტექსტის ნახვა
@application.route("/job/<int:job_id>")
def job_post(job_id):
    job = db.get_or_404(Job, job_id)
    # თუ ვაკანსია დამალულია და მნახველი არ არის მისი ავტორი, ვაჩვენებთ 403-ს
    if not job.is_published:
        if not current_user.is_authenticated or job.company.owner != current_user:
            abort(403)

    api_data = get_api_data()
    return render_template('job_post.html', title=job.title, job=job, api_data=api_data)

# შევასწოროთ ვაკანსიის დეტალები
@application.route("/job/<int:job_id>/update", methods=['GET', 'POST'])
@login_required
def update_job(job_id):
    job = db.get_or_404(Job, job_id)
    if job.company.owner != current_user:
        abort(403)

    form = JobForm()
    form.company.choices = [(c.id, c.name) for c in current_user.companies]

    if form.validate_on_submit():
        job.title = form.title.data
        job.short_description = form.short_description.data
        job.full_description = form.full_description.data
        job.category = form.category.data
        job.location = form.location.data
        job.salary_min = form.salary_min.data
        job.salary_max = form.salary_max.data
        job.company_id = form.company.data
        job.is_published = form.is_published.data  # ახალი ველი: სტატუსი

        db.session.commit()
        logging.info(f'ვაკანსია განახლდა: {job.id}, განაახლა: {current_user.username}')
        flash('გილოცავთ! ვაკანსია განახლდა!', 'success')
        return redirect(url_for('job_post', job_id=job.id))

    elif request.method == 'GET':
        form.title.data = job.title
        form.short_description.data = job.short_description
        form.full_description.data = job.full_description
        form.category.data = job.category
        form.location.data = job.location
        form.salary_min.data = job.salary_min
        form.salary_max.data = job.salary_max
        form.company.data = job.company_id
        form.is_published.data = job.is_published  # ახალი ველი: სტატუსი

    return render_template('create_job.html', title='ვაკანსიის რედაქტირება', form=form, legend='რედაქტირება')

# წავშალოთ ვაკანსია
@application.route("/job/<int:job_id>/delete", methods=['POST'])
@login_required
def delete_job(job_id):
    job = db.get_or_404(Job, job_id)
    if job.company.owner != current_user:
        abort(403)

    db.session.delete(job)
    db.session.commit()
    logging.info(f'ვაკანსია წაშლილია: {job_id} წაიშალა {current_user.username} მიერ')
    flash('ვაკანსია წაშლილია!', 'success')
    return redirect(url_for('home'))

# შევასწოროთ კომპანია
@application.route("/company/<int:company_id>/update", methods=['GET', 'POST'])
@login_required
def update_company(company_id):
    company = db.get_or_404(Company, company_id)
    if company.owner != current_user:
        abort(403)

    form = CompanyForm()
    if form.validate_on_submit():
        if form.logo.data:
            # შევამოწმოთ, რა აქვს ლოგოდ. თუ ნაგულისხმევი ფოტოა, ვტიებთ, თუ თავისი ატვირთულია, წავშლით სერვერიდან
            if company.logo != 'default_company.jpg':
                old_file_path = os.path.join(current_app.root_path, 'static/uploads', current_user.user_folder,
                                             company.logo)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            company.logo = save_picture(form.logo.data, current_user.user_folder)

        company.name = form.name.data
        company.address = form.address.data
        company.phone = form.phone.data
        company.email = form.email.data

        db.session.commit()
        flash('კომპანიის მონაცემები განახლდა!', 'success')
        return redirect(url_for('profile'))

    elif request.method == 'GET':
        form.name.data = company.name
        form.address.data = company.address
        form.phone.data = company.phone
        form.email.data = company.email

    return render_template('create_company.html', title='კომპანიის რედაქტირება', form=form)

# წავშალოთ კომპანია
@application.route("/company/<int:company_id>/delete", methods=['POST'])
@login_required
def delete_company(company_id):
    company = db.get_or_404(Company, company_id)
    if company.owner != current_user:
        abort(403)

    # შევამოწმოთ რა აყენია ლოგოდ. თუ ნაგულისხმევი ფოტოა დავტოვებთ, თუ თავისი ატვირთულია, წავშლით
    if company.logo != 'default_company.jpg':
        # გავიგოთ სად გვაქვს შენახული ფაილი და შევამოწმოთ არის თუ არა ის თავის ადგილზე
        file_path = os.path.join(current_app.root_path, 'static/uploads', current_user.user_folder, company.logo)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(company)
    db.session.commit()

    flash('კომპანია და მისი ყველა ვაკანსია წარმატებით წაიშალა!', 'success')
    return redirect(url_for('profile'))

# 404 შეცდომის გვერდი
@application.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404

# 500 შეცდომის გვერდი
@application.errorhandler(500)
def error_500(error):
    return render_template('500.html'), 500