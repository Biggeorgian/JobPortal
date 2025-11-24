import unittest
# შესწორება: აქედან ამოვიღეთ bcrypt
from app import application, db
from app.models import User, Company, Job

class JobBoardTestCase(unittest.TestCase):
    def setUp(self):
        application.config['TESTING'] = True
        application.config['WTF_CSRF_ENABLED'] = False
        application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        self.app = application.test_client()
        with application.app_context():
            db.create_all()

    def tearDown(self):
        with application.app_context():
            db.session.remove()
            db.drop_all()
            # ეს ხაზი მოაშორებს ResourceWarning-ს:
            db.engine.dispose()

    # პირველი ტესტი: ვამოწმებთ მთავარ გვერდს
    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'JobBoard', response.data)

    # მეორე ტესტი: ვამოწმებთ რეგისტრაციას და ავტორიზაციას
    def test_login(self):
        with application.app_context():
            user = User(username='TestUser', email='test@test.com', user_folder='randfold')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

        response = self.app.post('/login', data=dict(
            email='test@test.com',
            password='password'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/logout', response.data)

    # მესამე ტესტი: ვამოწმებ, შეიძლება თუ არა სხვისი პოსტის წაშლა
    def test_permission_delete(self):
        with application.app_context():
            # შევქმნათ ორი მომხმარებელი და ვცადოთ პოსტის წაშლა
            owner = User(username='Owner', email='owner@test.com', user_folder='f1')
            owner.set_password('pass')
            attacker = User(username='Attacker', email='attacker@test.com', user_folder='f2')
            attacker.set_password('pass')
            db.session.add_all([owner, attacker])
            db.session.commit()

            # შევქმნათ კომპანია და მასტან დაკავშირებული ვაკანსია
            company = Company(name='Comp', address='Add', phone='123', email='c@c.com', user_id=owner.id)
            db.session.add(company)
            db.session.commit()
            job = Job(title='MyJob', short_description='s', full_description='f', category='it', location='loc',
                      company_id=company.id)
            db.session.add(job)
            db.session.commit()
            job_id = job.id

        # გავდივართ ავტორიზაციას არაუფლებამოსილი მომხმარებლით და ვცდილობთ ვაკანსიის წაშლას
        self.app.post('/login', data=dict(email='attacker@test.com', password='pass'), follow_redirects=True)
        response = self.app.post(f'/job/{job_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()