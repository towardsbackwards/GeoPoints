import json

from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from mainapp.models import Point, Line
from mainapp.serializers import PointsSerializer
from django.core.serializers import serialize

from mainapp.algorithm import min_length


class MinLength(APIView):

    def get(self, request, **kwargs):
        point_from = self.kwargs['from']
        point_to = self.kwargs['to']
        result = min_length(point_from, point_to)
        print(result)

        geojson_answer = json.loads(
            serialize('geojson', Point.objects.filter(Q(id=self.kwargs['from']) | Q(id=self.kwargs['to'])),
                      geometry_field='geom',
                      fields=('score', 'geom')))
        return Response({"points": geojson_answer, "result": result})


class MinScore(APIView):
    pass


class PointsView(APIView):
    def get(self, request):
        geojson_answer = serialize('geojson', Point.objects.all(),
                                   geometry_field='geom',
                                   fields=('score',))
        return Response({"points": geojson_answer})
