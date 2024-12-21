from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from record.models import ScheduledRecord
from record.serializers import ScheduledRecordSerializer
from record.tasks import process_scheduled_record


class ScheduledRecordList(generics.ListCreateAPIView):
    queryset = ScheduledRecord.objects.all()
    serializer_class = ScheduledRecordSerializer

    def get_queryset(self):
        queryset = ScheduledRecord.objects.all().order_by('-created_at')

        # Filter parameters
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

    def perform_create(self, serializer):
        # Save and create celery task
        instance = serializer.save()
        from record.tasks import create_or_update_periodic_task
        create_or_update_periodic_task(instance)


class ScheduledRecordDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScheduledRecord.objects.all()
    serializer_class = ScheduledRecordSerializer

    def perform_update(self, serializer):
        # Update the record and recreate celery task
        instance = serializer.save()
        from record.tasks import create_or_update_periodic_task
        create_or_update_periodic_task(instance)

    def perform_destroy(self, instance):
        # Clean up celery task before deleting
        from django_celery_beat.models import PeriodicTask
        PeriodicTask.objects.filter(name=f"process_record_{
                                    instance.id}").delete()
        instance.delete()


class ScheduledRecordPause(APIView):
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


class ScheduledRecordExecute(APIView):
    def post(self, request, pk):
        try:
            record = ScheduledRecord.objects.get(pk=pk)
            if record.status != 'active':
                return Response(
                    {'error': f'Cannot execute schedule with status: {record.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not record.is_due:
                return Response(
                    {'error': 'Schedule is not due for execution'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            task = process_scheduled_record.delay(record.id)

            return Response({
                'status': 'success',
                'message': f'Schedule {pk} execution triggered',
                'task_id': task.id,
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
