import os

os.system("python3 manage.py makemigrations user assistant")
os.system("python3 manage.py makemigrations user")
os.system("python3 manage.py migrate")