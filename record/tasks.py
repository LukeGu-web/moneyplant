# your_app/tasks.py
from celery import shared_task
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json
from .models import ScheduledRecord


@shared_task
def process_scheduled_record(record_id):
    """
    Process a single scheduled record.
    This is the main task that will be executed according to the schedule.
    """
    try:
        record = ScheduledRecord.objects.get(id=record_id)

        if not record.is_due:
            return f"Record {record_id} is not due yet or is inactive"

        # Here you would implement your actual record processing logic
        # For example:
        # - Send notifications
        # - Generate reports
        # - Process data
        # - etc.

        # After processing, update the next occurrence
        record.update_next_occurrence()

        return f"Successfully processed record {record_id}"

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
    """
    Create or update the periodic task for a scheduled record.
    This function manages the Celery Beat schedule for each record.
    """
    task_name = f"process_record_{record.id}"

    # Delete existing periodic task if it exists
    PeriodicTask.objects.filter(name=task_name).delete()

    if record.status != 'active':
        return

    # Create interval schedule based on record frequency
    interval_schedule = create_interval_schedule(record.frequency)

    # Create the periodic task
    PeriodicTask.objects.create(
        name=task_name,
        task='your_app.tasks.process_scheduled_record',
        interval=interval_schedule,
        args=json.dumps([record.id]),
        start_time=record.start_date,
        enabled=True
    )


def create_interval_schedule(frequency):
    """
    Create or get an interval schedule based on the frequency.
    """
    if frequency == 'daily':
        return IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )[0]
    elif frequency == 'weekly':
        return IntervalSchedule.objects.get_or_create(
            every=7,
            period=IntervalSchedule.DAYS,
        )[0]
    elif frequency == 'monthly':
        return IntervalSchedule.objects.get_or_create(
            every=30,
            period=IntervalSchedule.DAYS,
        )[0]
    elif frequency == 'annually':
        return IntervalSchedule.objects.get_or_create(
            every=365,
            period=IntervalSchedule.DAYS,
        )[0]
