""" Send an email upon account creation """
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

import MAppServer.credentials as credentials
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.header import Header

# # def make_pin(seed) -> str:
# #     """Give a 4-digit PIN"""
# #     np.random.seed(seed)
# #     return str(np.random.randint(0, 9999)).rjust(4, "0")
# def get_password(user_row):
#     return str(int(user_row["app_pwd"])).rjust(4, "0")


def main_email(contact_email, user_id, link_to_the_store):

    address_to = (contact_email,)

    message = f"""
    Dear participant,
    Your account has been created!
    Here is a link to the app: {link_to_the_store}
    To login, you'll be asked an ID. Here is yours: {user_id}.
    Don't hesitate to reach me if you have any questions or concerns!
    Good luck!
    Best wishes,
    Aurélien
    --
    Aurélien Nioche, PhD
    
    University of Glasgow
    School of Computing Science - Room F161
    16 Lilybank Gardens, Glasgow G12 8QQ
    
    phone: (UK) +447450221861
    mail: nioche.aurelien@gmail.com
    """

    subject = "Account Created!"
    msg = MIMEText(message, _charset="UTF-8")
    msg['To'] = ", ".join(address_to)
    msg['FROM'] = credentials.EMAIL_HOST_USER
    msg['Subject'] = Header(subject, "utf-8")

    with SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(credentials.EMAIL_HOST_USER, credentials.EMAIL_HOST_PASSWORD)
        s.sendmail(credentials.EMAIL_HOST_USER, address_to, msg.as_string())


def main():

    contact_email = 'nioche.aurelien@gmail.com' # input("Contact email:")
    user_id = '<user_id>'  # input("User id:")
    link_to_the_store = '<to be announced>'  # input("Link to the store:")

    # csv = "<>"
    # users_df = pd.read_csv(csv, index_col=0)
    # idx = users_df.index[users_df['Email'] == contact_email][0]
    # user_row = users_df.loc[idx]
    # contact_email = user_row["email"]
    # user_id = user_row["user_id"]

    print("Mailing user...")
    main_email(contact_email=contact_email, user_id=user_id, link_to_the_store=link_to_the_store)


if __name__ == "__main__":
    main()
