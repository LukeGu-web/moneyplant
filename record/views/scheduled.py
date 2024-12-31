from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Prefetch
from django.db import transaction
from record.models import ScheduledRecord, Record
from record.serializers import ScheduledRecordSerializer
from record.permissions import IsOwner


class ScheduledRecordList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ScheduledRecordSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['is_list_view'] = True
        return context

    def get_queryset(self):
        queryset = ScheduledRecord.objects.filter(
            book__user=self.request.user
        ).order_by('-created_at')

        # Apply additional filters
        status = self.request.query_params.get('status')
        frequency = self.request.query_params.get('frequency')
        book_id = self.request.query_params.get('book')
        start_date_after = self.request.query_params.get('start_date_after')
        start_date_before = self.request.query_params.get('start_date_before')

        if status:
            queryset = queryset.filter(status=status)
        if frequency:
            queryset = queryset.filter(frequency=frequency)
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        if start_date_after:
            queryset = queryset.filter(start_date__gte=start_date_after)
        if start_date_before:
            queryset = queryset.filter(start_date__lte=start_date_before)

        return queryset
    
    
class ScheduledRecordDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwner]
    serializer_class = ScheduledRecordSerializer

    def get_queryset(self):
        return ScheduledRecord.objects.prefetch_related(
            Prefetch(
                'generated_records',
                queryset=Record.objects.order_by('-date')
            ).order_by('-created_at')
        )

    def perform_update(self, serializer):
        # Update the record and recreate celery task
        old_month_day = serializer.instance.month_day
        instance = serializer.save()
        if ('month_day' in serializer.validated_data and 
            instance.frequency == 'monthly' and 
            old_month_day != instance.month_day):
            instance.next_occurrence = instance._calculate_next_occurrence(instance.next_occurrence)
            instance.save(update_fields=['next_occurrence'])

    def perform_destroy(self, instance):
        # Clean up celery task before deleting
        from django_celery_beat.models import PeriodicTask
        PeriodicTask.objects.filter(name=f"process_record_{instance.id}").delete()
        try:
            instance.delete()
        except Exception as e:
            raise serializers.ValidationError({
                "detail": f"Failed to delete scheduled record: {str(e)}"
            })


class ScheduledRecordPause(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request, pk):
        try:
            record = ScheduledRecord.objects.get(pk=pk)
            if record.status == 'paused':
                return Response(
                    {'error': 'Schedule is already paused'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            record.pause()
            return Response({
                'status': 'success',
                'message': f'Schedule {pk} paused successfully',
                'next_occurrence': record.next_occurrence
            })
        except ScheduledRecord.DoesNotExist:
            return Response(
                {'error': 'Schedule not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ScheduledRecordResume(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request, pk):
        try:
            record = ScheduledRecord.objects.get(pk=pk)
            if record.status == 'active':
                return Response(
                    {'error': 'Schedule is already active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if record.status == 'completed':
                return Response(
                    {'error': 'Cannot resume completed schedule'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            record.resume()
            return Response({
                'status': 'success',
                'message': f'Schedule {pk} resumed successfully',
                'next_occurrence': record.next_occurrence
            })
        except ScheduledRecord.DoesNotExist:
            return Response(
                {'error': 'Schedule not found'},
                status=status.HTTP_404_NOT_FOUND
            )

# API won't let you execute a scheduled task before its scheduled time
class ScheduledRecordExecute(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request, pk):
        from record.tasks import process_record_immediately
        try:
            with transaction.atomic():
                # Get record with select_for_update to prevent race conditions
                record = ScheduledRecord.objects.select_for_update().get(pk=pk)
                
                # Check status
                if record.status != 'active':
                    return Response(
                        {'error': f'Cannot execute schedule with status: {record.status}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Check if due
                if not record.is_due:
                    return Response(
                        {'error': 'Schedule is not due for execution'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Process the record immediately
                try:
                    process_record_immediately(record)
                except Exception as e:
                    return Response(
                        {'error': f'Error processing record: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                return Response({
                    'status': 'success',
                    'message': f'Schedule {pk} executed successfully',
                    'next_occurrence': record.next_occurrence
                })

        except ScheduledRecord.DoesNotExist:
            return Response(
                {'error': 'Schedule not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )