# OnBoardHub

An HR onboarding portal built with Django.

## Features
- HR can create candidates and send login credentials via email
- Candidates upload required documents (Aadhaar, PAN, Resume, etc.)
- HR can approve or reject each document with remarks

## Tech Stack
- Python / Django
- SQLite
- Bootstrap 5
- Gmail SMTP

## Setup
1. Clone the repo
2. Create a virtual environment and install dependencies
3. Add your `.env` file with email credentials
4. Run `python manage.py migrate`
5. Run `python manage.py createsuperuser`
6. Run `python manage.py runserver`
