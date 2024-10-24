from django.core.mail import EmailMessage
import threading
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int
import six
from fillpdf import fillpdfs
from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage, PushServerError, PushTicketError
from requests.exceptions import ConnectionError, HTTPError
from book.models import Book
from asset.models import AssetGroup


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Util:
    """Helper function to create a default book with 3 groups for new users"""
    def create_default_book_with_groups(user):
        # Create default book
        book_data = {
            "name": "Daily Life",
            "note": "Welcome to your first book!",
        }

        # Create book instance
        book = Book.objects.create(user=user, **book_data)

        # Create three default groups
        default_groups = [
            {"name": 'Saving'},
            {"name": 'Credit'},
            {"name": 'Investment'},
        ]

        groups = []
        for group_data in default_groups:
            group = AssetGroup.objects.create(book=book, **group_data)
            groups.append(group)

        return book, groups

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

    def send_push_message(token, message, extra=None):
        try:
            response = PushClient().publish(
                PushMessage(to=token,
                            body=message,
                            data=extra))
        except PushServerError as exc:
            print(f"Push server error: {exc}")
        except (ConnectionError, HTTPError) as exc:
            print(f"Connection or HTTP error: {exc}")
        except DeviceNotRegisteredError:
            print(f"Device not registered")
        except PushTicketError as exc:
            print(f"Push ticket error: {exc}")


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
