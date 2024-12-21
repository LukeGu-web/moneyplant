from celery import shared_task
from django.utils import timezone
import json
from .models import Record, ScheduledRecord


@shared_task
def process_scheduled_record(record_id):
    try:
        scheduled_record = ScheduledRecord.objects.get(id=record_id)

        if not scheduled_record.is_due:
            return f"Record {record_id} is not due yet or is inactive"

        # Create a new record based on the scheduled record
        new_record = Record.objects.create(
            book=scheduled_record.book,
            asset=scheduled_record.asset,
            type=scheduled_record.type,
            category=scheduled_record.category,
            subcategory=scheduled_record.subcategory,
            is_marked_tax_return=scheduled_record.is_marked_tax_return,
            note=scheduled_record.note,
            amount=scheduled_record.amount,
            date=scheduled_record.next_occurrence
        )

        # Update the next occurrence
        scheduled_record.update_next_occurrence()

        return f"Successfully created record {new_record.id} from scheduled record {record_id}"

    except ScheduledRecord.DoesNotExist:
        return f"Record {record_id} not found"
    except Exception as e:
        return f"Error processing record {record_id}: {str(e)}"


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


def create_or_update_periodic_task(record):
    from django_celery_beat.models import PeriodicTask
    task_name = f"process_record_{record.id}"
    PeriodicTask.objects.filter(name=task_name).delete()

    if record.status != 'active':
        return

    task_kwargs = {
        'name': task_name,
        'task': 'your_app.tasks.process_scheduled_record',
        'args': json.dumps([record.id]),
        'start_time': record.start_date,
        'enabled': True
    }

    if record.frequency in ['weekly', 'monthly']:
        schedule = create_interval_schedule(record.frequency)
        task_kwargs['crontab'] = schedule
    else:
        schedule = create_interval_schedule(record.frequency)
        task_kwargs['interval'] = schedule

    if record.end_date:
        task_kwargs['expires'] = record.end_date

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
