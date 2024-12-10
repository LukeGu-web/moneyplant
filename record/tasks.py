from celery import shared_task
from django.utils.timezone import now
from .models import ScheduledRecord, Record


@shared_task
def generate_scheduled_records():
    current_time = now()
    due_records = ScheduledRecord.objects.filter(
        next_occurrence__lte=current_time)

    for scheduled_record in due_records:
        # Create a new Record based on ScheduledRecord
        Record.objects.create(
            book=scheduled_record.book,
            asset=scheduled_record.asset,
            type=scheduled_record.type,
            category=scheduled_record.category,
            subcategory=scheduled_record.subcategory,
            is_marked_tax_return=scheduled_record.is_marked_tax_return,
            note=scheduled_record.note,
            amount=scheduled_record.amount,
            date=scheduled_record.next_occurrence,
        )

        # Update next_occurrence
        scheduled_record.next_occurrence = scheduled_record._calculate_next_occurrence(
            scheduled_record.next_occurrence
        )
        scheduled_record.save()
