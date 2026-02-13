# JobTrack Automate

A Django web application for tracking job applications across South African job boards, with optional Selenium automation for applying to positions on PNet, Careers24, LinkedIn and Indeed.

Built for job seekers in South Africa who want to stay on top of their applications without losing track of where they have applied.

## What It Does

- **Dashboard** with application stats, charts and upcoming reminders
- **Application tracking** with a proper status workflow (draft, applied, screening, interview, assessment, offer, accepted, rejected, withdrawn)
- **Company database** to keep tabs on where you have applied and their Glassdoor ratings
- **Document storage** for CVs, cover letters and certificates with versioning
- **Cover letter templates** with placeholders you can reuse
- **Analytics** showing response rates, interview rates, monthly trends and top companies
- **CSV export** for your records or to share with a recruiter
- **REST API** with JWT authentication for mobile apps or a Chrome extension
- **Selenium automation** (optional) for auto-applying on SA job boards
- **Email reminders** via Celery for follow-ups, interviews and deadlines
- **POPIA compliant** with explicit automation consent per user

## Tech Stack

- Python 3.11+
- Django 4.2
- Django REST Framework with JWT authentication
- PostgreSQL (SQLite available for testing)
- Celery + Redis for background tasks
- Selenium 4 with Chrome WebDriver
- Bootstrap 5.3 and Chart.js for the frontend
- Docker Compose for easy deployment

## Getting Started

### Prerequisites

You will need:
- Python 3.11 or later
- PostgreSQL 14+ (or use SQLite for development)
- Redis (for Celery tasks)
- Google Chrome (for Selenium automation)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/jobtrack-automate.git
cd jobtrack-automate
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Copy the environment file and fill in your details:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials, secret key and email settings.

4. Run the database migrations:

```bash
cd job_tracker
python manage.py migrate
```

5. Create a superuser account:

```bash
python manage.py createsuperuser
```

6. Collect static files:

```bash
python manage.py collectstatic --noinput
```

7. Start the development server:

```bash
python manage.py runserver
```

Open your browser and go to `http://localhost:8000`.

### Using Docker

If you prefer Docker, the whole stack is configured in `docker-compose.yml`:

```bash
docker-compose up --build
```

This starts PostgreSQL, Redis, the Django web server, a Celery worker and the Celery beat scheduler.

### Running Celery (for reminders and automation)

In a separate terminal:

```bash
cd job_tracker
celery -A config worker --loglevel=info
```

And for scheduled tasks:

```bash
celery -A config beat --loglevel=info
```

## Running Tests

Tests are written with pytest-django and factory-boy:

```bash
cd job_tracker
pytest
```

For a coverage report:

```bash
pytest --cov=applications --cov=accounts --cov=documents --cov-report=html
```

The test suite covers models, views, services, automation (with mocked Selenium) and the API.

## Project Structure

```
jobtrack-automate/
    requirements.txt
    docker-compose.yml
    .env.example
    job_tracker/
        manage.py
        config/             # Django settings, urls, celery config
        applications/       # Main app: models, views, services
            automation/     # Selenium browser automation
            services/       # Business logic (analytics, status tracking)
            api/            # REST API endpoints
            utils/          # CV parser, email handler, validators
            tests/          # pytest test suite
        accounts/           # User profiles and authentication
        documents/          # CV and cover letter management
        tasks/              # Celery background tasks
        templates/          # HTML templates (Bootstrap 5)
        static/             # CSS and JavaScript
        media/              # Uploaded files (CVs, cover letters)
```

## Automation

The Selenium automation is optional. It supports:

- **PNet** - login, search and apply
- **Careers24** - login, search and apply
- **LinkedIn** - login, search and Easy Apply
- **Indeed SA** - login, search and apply

Set up automation rules in the dashboard or through the API. The system checks for CAPTCHA and waits for manual solving. It also includes random delays and rotating user agents to avoid detection.

**Important:** Automation requires your explicit consent (POPIA compliance). You can toggle it in your profile settings.

### Daily Limits

The system enforces a configurable daily application limit per automation rule to avoid spamming job boards. The default is 5 applications per day per rule.

## API Endpoints

The REST API is available at `/api/v1/` with JWT authentication:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/token/` | POST | Get JWT access and refresh tokens |
| `/api/v1/token/refresh/` | POST | Refresh an expired access token |
| `/api/v1/applications/` | GET, POST | List or create applications |
| `/api/v1/applications/{id}/` | GET, PUT, DELETE | Application detail |
| `/api/v1/applications/{id}/update-status/` | POST | Update application status |
| `/api/v1/companies/` | GET, POST | List or create companies |
| `/api/v1/jobs/` | GET | List jobs |
| `/api/v1/dashboard/` | GET | Dashboard statistics |
| `/api/v1/reminders/` | GET, POST | List or create reminders |
| `/api/v1/automation/apply/` | POST | Trigger automated application |
| `/api/v1/automation/search/` | POST | Trigger automated job search |
| `/api/v1/documents/upload/` | POST | Upload a document |

## Environment Variables

See `.env.example` for the full list. The key ones:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | (required) |
| `DEBUG` | Debug mode | True |
| `DATABASE_URL` | PostgreSQL connection string | (required for production) |
| `REDIS_URL` | Redis connection for Celery | redis://localhost:6379/0 |
| `USE_SQLITE` | Use SQLite instead of PostgreSQL | False |
| `EMAIL_HOST` | SMTP server for reminders | localhost |
| `SELENIUM_HEADLESS` | Run browser in headless mode | True |

## Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/something-lekker`)
3. Commit your changes (`git commit -m 'Add something useful'`)
4. Push to the branch (`git push origin feature/something-lekker`)
5. Open a Pull Request

## Licence

This project is licensed under the MIT Licence. See the [LICENSE](LICENSE) file for details.
