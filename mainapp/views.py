import json

from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from mainapp.models import Point, Line
from mainapp.serializers import PointsSerializer
from django.core.serializers import serialize

from mainapp.algorithm import best_path_by


class MinLength(APIView):

    def get(self, request, **kwargs):
        point_from = self.kwargs['from']
        point_to = self.kwargs['to']
        result_km = best_path_by(point_from, point_to, Line, Point)
        result_score = best_path_by(point_from, point_to, Line, Point, eval_type='by_score')
        print(result_km)
        print(result_score)
        geojson_answer = json.loads(
            serialize('geojson', Point.objects.filter(id__in=result_km['path']),
                      geometry_field='geom',
                      fields=['pk', 'score', 'geom']))
        return Response({"points": geojson_answer})


class MinScore(APIView):
    pass


class PointsView(APIView):
    def get(self, request):
        geojson_answer = serialize('geojson', Point.objects.all(),
                                   geometry_field='geom',
                                   fields=('score',))
        return Response({"points": geojson_answer})
