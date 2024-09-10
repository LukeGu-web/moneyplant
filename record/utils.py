from itertools import groupby
from decimal import Decimal


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
