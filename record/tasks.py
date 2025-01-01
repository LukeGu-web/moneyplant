from celery import shared_task
from django.utils import timezone
from django.db import transaction
import json
from .models import Record, ScheduledRecord
from .utils import send_push_message
import logging
logger = logging.getLogger(__name__)


@shared_task
def check_due_records():
    """
    Periodic task to check and process all due records.
    """
    now = timezone.now()
    
    # Get all due records and lock them
    with transaction.atomic():
        due_records = ScheduledRecord.objects.select_for_update().filter(
            status='active',
            next_occurrence__lte=now,
            start_date__lte=now
        )

        for record in due_records:
            try:
                # Double-check the record is still due after getting lock
                if record.next_occurrence <= now:
                    process_record_immediately(record)
            except Exception as e:
                print(f"Error processing record {record.id}: {str(e)}")

    return f"Checked {due_records.count()} due records"


def process_record_immediately(record):
    """Process a record immediately without scheduling"""
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
        date=record.next_occurrence,
        created_by_schedule=record
    )

    # Update the scheduled record
    record.last_run = timezone.now()
    old_next = record.next_occurrence
    record.next_occurrence = record._calculate_next_occurrence(old_next)
    
    # Handle completion if needed
    if record.status == 'completed':
        try:
            account = record.book.user.account
            if account.expo_push_token:
                message = f'Scheduled record series completed: {record.category}'
                send_push_message(
                    token=account.expo_push_token,
                    message=message,
                    extra={
                        "type": "SCHEDULE_COMPLETED",
                        "scheduleId": record.id,
                        "bookId": record.book.id,
                        "category": record.category
                    }
                )
        except Exception as e:
            print(f"Failed to send completion notification: {str(e)}")
    
    record.save()

    # Send notification for new record
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
                    "amount": str(record.amount),
                    "scheduleId": record.id
                }
            )
    except Exception as e:
        print(f"Failed to send push notification: {str(e)}")



@shared_task
def cleanup_expired_schedules():
    """
    Periodic task to clean up expired schedules.
    """
    now = timezone.now()
    expired_records = ScheduledRecord.objects.filter(
        status='active',
        end_date__lte=now
    )

    for record in expired_records:
        record.status = 'completed'
        record.save()

    return f"Cleaned up {expired_records.count()} expired schedules"
