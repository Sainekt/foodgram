gunicorn --bind "0.0.0.0:8000" "foodgram_backend.wsgi"
python manage.py makemigrations
python manage.py migrate