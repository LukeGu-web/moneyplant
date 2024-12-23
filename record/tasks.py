from celery import shared_task
from django.utils import timezone
from django.db import transaction
import json
from .models import Record, ScheduledRecord
from .utils import send_push_message

@shared_task
def process_scheduled_record(record_id):
    try:
        with transaction.atomic():
            record = ScheduledRecord.objects.select_for_update().get(pk=record_id)
            
            # Create the new record
            new_record = Record.objects.create(
                book=record.book,
                asset=record.asset,
                type=record.type,
                category=record.category,
                subcategory=record.subcategory,
                amount=record.amount,
                note=record.note,
                is_marked_tax_return=record.is_marked_tax_return,
                date=record.next_occurrence
            )

            # Update the scheduled record
            record.last_run = timezone.now()
            record.next_occurrence = record._calculate_next_occurrence(record.next_occurrence)
            record.save()

            # Send push notification if token exists
            try:
                account = record.book.user.account
                if account.expo_push_token:
                    abs_amount = abs(float(record.amount))
                    action = "costs" if record.type == "expense" else "earns"
                    message = f'{record.frequency.capitalize()} record: {record.category} {action} ${abs_amount:.2f}'
                    
                    send_push_message(
                        token=account.expo_push_token,
                        message=message,
                        extra={
                            "type": "SCHEDULED_RECORD",
                            "recordId": new_record.id,
                            "bookId": record.book.id,
                            "category": record.category,
                            "amount": str(record.amount)
                        }
                    )
            except Exception as e:
                # Log the error but don't stop the process
                print(f"Failed to send push notification: {str(e)}")

        return True
    except Exception as e:
        print(f"Error processing scheduled record {record_id}: {str(e)}")
        raise

@shared_task
def check_due_records():
    """
    Periodic task to check and process all due records.
    This task will be scheduled to run frequently (e.g., every minute)
    to check for any records that need processing.
    """
    now = timezone.now()
    due_records = ScheduledRecord.objects.filter(
        status='active',
        next_occurrence__lte=now
    )

    for record in due_records:
        # Schedule the processing task
        process_scheduled_record.delay(record.id)

    return f"Checked {due_records.count()} due records"


def create_crontab_schedule(record):
    """
    Create or retrieve a CrontabSchedule based on the ScheduledRecord's attributes.
    """
    from django_celery_beat.models import CrontabSchedule
    if record.frequency == 'weekly':
        if not record.week_days:
            raise ValueError(
                "Week days must be specified for weekly schedules.")
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=0,
            day_of_week=','.join(map(str, record.week_days)),
            day_of_month='*',
            month_of_year='*',
        )
    elif record.frequency == 'monthly':
        if not record.month_day:
            raise ValueError(
                "Month day must be specified for monthly schedules.")
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=0,
            day_of_week='*',
            day_of_month=str(record.month_day),
            month_of_year='*',
        )
    else:
        raise ValueError(f"Unsupported crontab frequency: {record.frequency}")
    return schedule


def create_or_update_periodic_task(record):
    """
    Create or update a periodic task for the given ScheduledRecord.
    """
    from django_celery_beat.models import PeriodicTask
    task_name = f"process_record_{record.id}"

    # Remove existing task with the same name
    PeriodicTask.objects.filter(name=task_name).delete()

    # If the record is not active, do not create a new task
    if record.status != 'active':
        return

    # Prepare task arguments
    task_kwargs = {
        'name': task_name,
        'task': 'your_app.tasks.process_scheduled_record',
        'args': json.dumps([record.id]),
        'start_time': record.start_date,
        'enabled': True,
    }

    # Add schedule based on frequency
    if record.frequency in ['weekly', 'monthly']:
        schedule = create_crontab_schedule(record)
        task_kwargs['crontab'] = schedule
    elif record.frequency in ['daily']:
        schedule = create_interval_schedule(record.frequency)
        task_kwargs['interval'] = schedule
    else:
        raise ValueError(f"Unsupported frequency: {record.frequency}")

    # Set expiration if end_date exists
    if record.end_date:
        task_kwargs['expires'] = record.end_date

    # Create the PeriodicTask
    PeriodicTask.objects.create(**task_kwargs)


def create_interval_schedule(frequency, record=None):
    """
    Create or get a schedule based on the frequency.

    Args:
        frequency (str): The frequency type ('daily', 'weekly', 'monthly', 'annually')
        record (ScheduledRecord): The scheduled record instance (needed for weekly/monthly schedules)
    """
    from django_celery_beat.models import IntervalSchedule, CrontabSchedule
    if frequency == 'daily':
        return IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )[0]
    elif frequency == 'weekly' and record and record.week_days:
        days_of_week = ','.join(str(day) for day in record.week_days)
        return CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_week=days_of_week,
        )[0]
    elif frequency == 'monthly' and record and record.month_day:
        return CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_month=str(record.month_day),
        )[0]
    elif frequency == 'annually':
        return IntervalSchedule.objects.get_or_create(
            every=365,
            period=IntervalSchedule.DAYS,
        )[0]


@shared_task
def cleanup_expired_schedules():
    now = timezone.now()
    expired_records = ScheduledRecord.objects.filter(
        status='active',
        end_date__lte=now
    )

    for record in expired_records:
        record.status = 'completed'
        record.save()

    return f"Cleaned up {expired_records.count()} expired schedules"
