from django.core.mail import BadHeaderError
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from user.utils import Util


@api_view(http_method_names=["POST"])
def tax_return_view(request):
    if request.method == "POST":
        try:
            Util.send_email({
                "email_subject": 'With attachment',
                "email_body": 'Hello world',
                "to_email": 'mythnan@gmail.com',
                'email_attachment': 'doc/new.pdf'
            })
        except BadHeaderError:
            return Response({"error": "Invalid header found."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"details": "Send successfully."}, status=status.HTTP_200_OK)

    if request.method == "POST":
        try:
            Util.send_email({
                "email_subject": 'No attachment',
                "email_body": 'Hello world',
                "to_email": 'mythnan@gmail.com',
            })
        except BadHeaderError:
            return Response({"error": "Invalid header found."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"details": "Send successfully."}, status=status.HTTP_200_OK)


@api_view(http_method_names=["POST"])
def fill_pdf_view(request):
    if request.method == "POST":
        try:
            Util.fill_pdf()
        except BadHeaderError:
            return Response({"error": "Invalid file."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"details": "Send successfully."}, status=status.HTTP_200_OK)
