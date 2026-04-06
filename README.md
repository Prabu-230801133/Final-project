# 🗳️ VoteX — College Voting System

A full-stack secure college voting system built with **Django + MySQL + HTML/CSS/JS**.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Django 4.2 (Python 3.12) |
| Database | MySQL 8.0 |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Auth | Django Auth + Google OAuth 2.0 |
| Email | Gmail SMTP (Django backend) |
| Images | Cloudinary API / Local media |
| REST API | Django REST Framework |

---

## 🚀 Quick Start

### Step 1: Configure Environment

```bash
# Copy the env template
copy .env.example .env
```

Edit `.env` with your credentials:
```
DB_PASSWORD=your_mysql_root_password
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
```

### Step 2: Create Database & Migrate

```bash
# Option A: Use the setup script
python setup_db.py

# Option B: Manual steps
# 1. Open MySQL Workbench and run:
#    CREATE DATABASE college_db CHARACTER SET utf8mb4;
# 2. Run migrations:
python manage.py migrate
# 3. Load sample data:
python seed_data.py
```

### Step 3: Run the Server

```bash
python manage.py runserver
```

Visit: **http://localhost:8000**

---

## 👥 Default Accounts (after seeding)

| Role | URL | Username | Password |
|------|-----|----------|----------|
| Django Admin | /django-admin/ | admin | Admin@123 |
| Web Admin | /admin-dashboard/ | webadmin | WebAdmin@123 |
| Students | /accounts/login/ | student1-5 | Student@123 |

---

## 📁 Project Structure

```
college_election/
├── config/                    ← Django project settings
│   ├── settings.py
│   └── urls.py
├── accounts/                  ← Authentication & user management
│   ├── models.py              ← CustomUser with role field
│   ├── views.py               ← Login/logout/redirect
│   ├── admin.py               ← Auto-generate & email credentials
│   ├── decorators.py          ← Role-based access control
│   ├── utils.py               ← Email functions
│   └── pipeline.py            ← Google OAuth pipeline
├── voting/                    ← Core voting functionality
│   ├── models.py              ← Election, Position, Candidate, Vote
│   └── views.py               ← Home, dashboard, vote casting
├── web_admin/                 ← Custom admin dashboard
│   └── views.py               ← Election/candidate/results CRUD
├── api/                       ← REST API endpoints
│   ├── views.py
│   └── serializers.py
├── templates/                 ← HTML templates
├── static/                    ← CSS, JS, images
│   ├── css/style.css          ← Global design system
│   └── js/
│       ├── main.js            ← Global JS
│       └── countdown.js       ← Countdown timer component
├── seed_data.py               ← Sample data loader
└── setup_db.py               ← Database setup helper
```

---

## 🔌 API Integrations

1. **Google OAuth 2.0** — Social login via `social-auth-app-django`
2. **Gmail SMTP** — Credential & vote confirmation emails
3. **Cloudinary** — Candidate photo hosting (optional)

### REST API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/elections/ | List active elections |
| GET | /api/candidates/<id>/ | Candidates for election |
| GET | /api/results/<id>/ | Published results |
| GET | /api/my-votes/ | Authenticated user's votes |

---

## 🔒 Security Features

- ✅ One vote per student per position enforced at DB level (`unique_together`)
- ✅ CSRF protection on all forms (Django built-in)
- ✅ Password hashing (PBKDF2 + SHA256)
- ✅ Role-based access control via custom decorators
- ✅ `@login_required` on all protected views
- ✅ Assignment-based eligibility (students only see their elections)

---

## 📧 Email Setup (Gmail)

1. Enable 2FA on your Gmail account
2. Go to: Account → Security → App passwords
3. Generate an app password for "Mail"
4. Add to `.env`: `EMAIL_HOST_PASSWORD=your_16_char_app_password`

---

## 🌐 Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable "Google+ API" / "Google Identity"
3. Create OAuth 2.0 credentials
4. Add redirect URI: `http://localhost:8000/social-auth/complete/google-oauth2/`
5. Copy Client ID & Client Secret to `.env`

---

## ☁️ Cloudinary Setup (Optional)

1. Sign up at [cloudinary.com](https://cloudinary.com) (free tier)
2. Copy Cloud Name, API Key, Secret to `.env`
3. Candidate photos will upload to Cloudinary automatically

Without Cloudinary, photos are stored in `media/candidates/` locally.
