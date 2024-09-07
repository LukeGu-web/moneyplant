from django.core.mail import EmailMessage
import threading
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int
import six
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


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )

    def check_token(self, user, token):
        # Check the token as per the base class implementation
        if not super().check_token(user, token):
            return False

        # Check token expiration (30 minutes)
        try:
            ts_b36, _ = token.split('-')
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Token should be within the last 30 minutes
        current_timestamp = self._num_seconds(self._now())
        if (current_timestamp - ts) > 1800:  # 1800 seconds = 30 minutes
            return False

        return True
