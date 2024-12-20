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
        queryset = ScheduledRecord.objects.all()
        status = self.request.query_params.get('status', None)
        frequency = self.request.query_params.get('frequency', None)

        if status:
            queryset = queryset.filter(status=status)
        if frequency:
            queryset = queryset.filter(frequency=frequency)

        return queryset


class ScheduledRecordDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScheduledRecord.objects.all()
    serializer_class = ScheduledRecordSerializer


class ScheduledRecordPause(APIView):
    def post(self, request, pk):
        try:
            record = ScheduledRecord.objects.get(pk=pk)
            record.pause()
            return Response({
                'status': 'success',
                'message': f'Schedule {pk} paused successfully'
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
            record.resume()
            return Response({
                'status': 'success',
                'message': f'Schedule {pk} resumed successfully'
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
                    {'error': 'Cannot execute inactive schedule'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            task = process_scheduled_record.delay(record.id)
            return Response({
                'status': 'success',
                'message': f'Schedule {pk} execution triggered',
                'task_id': task.id
            })
        except ScheduledRecord.DoesNotExist:
            return Response(
                {'error': 'Schedule not found'},
                status=status.HTTP_404_NOT_FOUND
            )
