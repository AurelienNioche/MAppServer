""" Send an email upon account creation """
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

import pandas as pd
import numpy as np
from pytz import timezone
import MAppServer.credentials as credentials
from smtplib import SMTP_SSL


def get_credentials() -> dict:
    """Get email username and password"""
    return {
        "host": credentials.EMAIL_HOST_USER,
        "passwrd": credentials.EMAIL_HOST_PASSWORD}


def make_email_addr(local_part: str, domain_name: str) -> str:
    """Make a email-like string"""
    return f"{local_part}@{domain_name}"


# def make_pin(seed) -> str:
#     """Give a 4-digit PIN"""
#     np.random.seed(seed)
#     return str(np.random.randint(0, 9999)).rjust(4, "0")
def get_password(user_row):
    return str(int(user_row["app_pwd"])).rjust(4, "0")


def set_first_session(start_date, session_time):

    day, month, year = start_date.split(".")
    hour, minute = session_time.split(":")

    hour = f"{int(hour):02d}"
    minute = f"{int(minute):02d}"

    day = f"{int(day):02d}"
    month = f"{int(month):02d}"

    first_session_string = f"{year}-{month}-{day} {hour}:{minute}"
    first_session = datetime.datetime.fromisoformat(first_session_string)
    first_session = timezone("Europe/Helsinki").localize(first_session)
    first_session = first_session.astimezone(timezone('UTC'))

    return first_session


def main_email(contact_email, app_email, app_pwd, date, time):

    # Working to send plain text email
    # If you check internet to make the html version, filter results by date
    email_credentials = get_credentials()
    address_from = email_credentials["host"]
    address_to = (contact_email,)

    text = f"""
    Dear participant,
    Your account has been created!
    You can connect to:
    http://activeteaching.research.comnet.aalto.fi/
    id: {app_email}
    pwd: {app_pwd}
    Your first session is on {date} at {time}.
    Training plan: 2 sessions per day, for 7 days.
    Don't hesitate to reach me if you have any questions or concerns!
    Good luck!
    Best,
    Aurelien
    --
    Aurelien Nioche, PhD
    Finnish Center for Artificial Intelligence (FCAI)
    Aalto University
    Department of Communications and Networking
    Computer Science Building - Office B235
    Konemiehentie 2
    02150 Espoo, Finland
    phone: (FI) +358 (0) 5 04 75 83 05, (FR) +33 (0) 6 86 55 02 55
    mail: nioche.aurelien@gmail.com
    """

    subject = "Account Created!"
    message = \
        f"""From: {email_credentials["host"]}\n""" \
        f"""To: {", ".join(address_to)}\n""" \
        f"""Subject: {subject}\n\n{text}"""

    with SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(email_credentials["host"], email_credentials["passwrd"])
        s.sendmail(address_from, address_to, message)


def main():

    csv = "<>"

    contact_email = input("Contact email:")

    users_df = pd.read_csv(csv, index_col=0)

    idx = users_df.index[users_df['Email'] == contact_email][0]
    user_row = users_df.loc[idx]

    app_email = user_row["app_email"]
    contact_email = user_row["Email"]
    start_date = user_row["StartDate"]
    session_time = user_row["SessionTime"]
    app_pwd = get_password(user_row)

    print("Mailing user...")
    main_email(contact_email=contact_email,
               app_email=app_email,
               app_pwd=app_pwd,
               date=start_date,
               time=session_time)


if __name__ == "__main__":
    main()
