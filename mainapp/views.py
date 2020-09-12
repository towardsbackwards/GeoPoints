
from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from mainapp.models import Point, Line
from mainapp.serializers import PointsSerializer
from django.core.serializers import serialize

from mainapp.tests import min_length


class MinLength(APIView):

    def get(self, request, **kwargs):
        point_from = self.kwargs['from']
        point_to = self.kwargs['to']
        print(min_length(point_from, point_to))

        geojson_answer = serialize('geojson', Point.objects.filter(Q(id=self.kwargs['from']) | Q(id=self.kwargs['to'])),
                                   geometry_field='geom',
                                   fields=('score', 'geom'))
        return Response({"points": geojson_answer})


class MinScore(APIView):
    pass


class PointsView(APIView):
    def get(self, request):
        geojson_answer = serialize('geojson', Point.objects.all(),
                                   geometry_field='geom',
                                   fields=('score',))
        return Response({"points": geojson_answer})