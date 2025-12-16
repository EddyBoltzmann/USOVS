# Setup

1. Create and activate a virtualenv
2. Install requirements: pip install -r requirements.txt
3. Set environment variables: DJANGO_SECRET_KEY, POSTGRES_*, FIREBASE_CREDENTIALS_JSON, FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN
4. Run migrations: python manage.py migrate
5. Create superuser: python manage.py createsuperuser
6. Run server: python manage.py runserver

Notes: Store Firebase credentials securely (secret manager) and do not commit them.
