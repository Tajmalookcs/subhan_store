# Phase 2 — Setup Instructions

## 1. Create Virtual Environment & Install Dependencies

```bash
cd subhan_store
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

## 2. Configure Environment

Copy `.env` and fill in values (already created — just update `SECRET_KEY`):
```bash
# Generate a strong secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 3. Run Migrations

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

## 4. Create Superuser

```bash
python manage.py createsuperuser
# Set role to 'superadmin' via Django admin after creation
```

## 5. Run Development Server

```bash
python manage.py runserver
```

## 6. Access Points

| URL | Description |
|---|---|
| http://127.0.0.1:8000/ | Home (redirects to login or dashboard) |
| http://127.0.0.1:8000/auth/login/ | Login |
| http://127.0.0.1:8000/auth/register/ | Customer Registration |
| http://127.0.0.1:8000/auth/password/reset/ | Password Reset |
| http://127.0.0.1:8000/dashboard/ | Admin Dashboard |
| http://127.0.0.1:8000/account/ | Customer Portal |
| http://127.0.0.1:8000/django-admin/ | Django Admin Panel |

## 7. Fix Superuser Role (via Django Admin)

1. Go to http://127.0.0.1:8000/django-admin/
2. Login with your superuser credentials
3. Go to Accounts → Users → your user
4. Set Role to `superadmin`
5. Save

## File Structure Created

```
subhan_store/
├── manage.py
├── db.sqlite3          ← auto-created on first migrate
├── requirements.txt
├── .env
├── .gitignore
├── PHASE2_SETUP.md
├── config/
│   ├── settings/base.py | development.py | production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   └── accounts/
│       ├── models.py       ← CustomUser model
│       ├── views.py        ← All auth views
│       ├── forms.py        ← Login, Register, Profile, Password forms
│       ├── admin.py
│       ├── permissions.py  ← Role mixins
│       ├── apps.py
│       ├── migrations/
│       └── urls/
│           ├── auth.py     ← /auth/
│           ├── customer.py ← /account/
│           ├── dashboard.py← /dashboard/
│           └── home.py     ← /
└── templates/
    ├── base.html
    ├── base_admin.html
    ├── partials/navbar | sidebar | footer
    └── accounts/
        ├── login.html
        ├── register.html
        ├── profile.html
        ├── dashboard.html
        ├── customer_dashboard.html
        ├── staff_list.html
        ├── staff_create.html
        ├── password_reset*.html
        └── emails/
```

## Next: Phase 3 — Product & Category Management
