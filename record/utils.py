from itertools import groupby
from decimal import Decimal
from requests.exceptions import ConnectionError, HTTPError
from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage, PushServerError, PushTicketError

def string_to_color(string):
    hash_value = 0
    for char in string:
        hash_value = ord(char) + ((hash_value << 5) - hash_value)
    color = '#'
    for i in range(3):
        value = (hash_value >> (i * 8)) & 0xff
        color += f'{value:02x}'
    return color


def group_records_by_date(records):
    grouped_data = []
    for date, group in groupby(records, key=lambda x: x['date'].split('T')[0]):
        sum_of_income = Decimal('0.00')
        sum_of_expense = Decimal('0.00')
        records_by_day = []
        for record in group:
            if record['type'] == 'income':
                sum_of_income += Decimal(record['amount'])
            elif record['type'] == 'expense':
                sum_of_expense += Decimal(record['amount'])
            records_by_day.append(record)
        grouped_data.append({
            'date': date,
            'records': records_by_day,
            'sum_of_income': sum_of_income,
            'sum_of_expense': sum_of_expense
        })
    return grouped_data


@staticmethod
def send_push_message(token, message, extra=None):
    """
    Send push notification to a specific Expo push token
    """
    try:
        response = PushClient().publish(
            PushMessage(to=token,
                        body=message,
                        data=extra if extra else {}))
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        print(f"Push Server Error: {exc.errors} {exc.response_data}")
    except (ConnectionError, HTTPError) as exc:
        # Encountered some Connection or HTTP error - retry a few times in
        # production
        print(f"Connection Error: {exc}")
    except DeviceNotRegisteredError:
        # Mark the push token as inactive
        # You might want to remove the token from your database
        print(f"Device not registered: {token}")
    except PushTicketError as exc:
        # Encountered some other per-notification error.
        print(f"Push Response Error: {exc}")