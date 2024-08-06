from django.core.mail import EmailMessage
import threading
from fillpdf import fillpdfs


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
        if 'email_attachment' in data:
            email.attach_file(data['email_attachment'])
        EmailThread(email).start()

    @staticmethod
    def fill_pdf():
        data = {
            'name': 'Luke',
            'income': '1000',
            'expense': '20',
            'tax': '2'
        }
        fillpdfs.write_fillable_pdf(
            'doc/test_file.pdf', 'doc/new.pdf', data)
