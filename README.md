# Pocket Pal 

A Tamagotchi style virtual pet game. Each user gets one pet that they feed,
play with, and put to sleep. Stats decay over real elapsed time, so the pet
keeps living even while you're logged out. Users can add friends, visit
their friends' pets and give them a treat, buy items in a shop, send gifts
to friends, and earn coins through a daily care streak and a couple of quick mini games for you to enjoy as well while earning coins simultaneously!

## Stack
Flask (Python)
SQLAlchemy ORM. 
SQLite 
Postgres
Flask-Login 
Jinja2 
CSS/JS

## Running it locally

```bash
python -m venv venv
source venv/bin/activate       
pip install -r requirements.txt
python seed.py                 
python run.py                 
```

## Live Deployment
Deployed Pocket Pal using Railway

Live app URL: pocketpal.up.railway.app

The deployed version uses:
- Railway for hosting
- PostgreSQL for the production database
- Gunicorn as the production server

## Environment Variables

The app uses the following environment variables in production:

```txt
SECRET_KEY=your-secret-key
DATABASE_URL=your-postgres-database-url
