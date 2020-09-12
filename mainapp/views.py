import collections

from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from mainapp.models import Point, Line
from mainapp.serializers import PointsSerializer
from django.core.serializers import serialize

from mainapp.tests import astar


edges = {1: [2, 8, 9],
         2: [1, 10, 3],
         8: [1, 7, 12, 9],
         9: [1, 8, 12, 10],
         10: [2, 3, 4, 12, 11, 9],
         3: [2, 10, 4],
         4: [3, 10, 5, 11],
         5: [4, 6],
         11: [4, 6, 10],
         6: [5, 11, 13, 7],
         13: [6, 7, 12],
         7: [6, 13, 8],
         12: [8, 13, 9, 10]}


def distance_eval(a, b):
    return Point.objects.get(id=a).geom.distance(Point.objects.get(id=b).geom) * 100


def heuristic_eval(pos):
    return Point.objects.get(id=pos).geom.distance(Point.objects.get(id=13).geom) * 100


def neighbors(node):
    return edges[node]


def goal(pos):
    if pos == 5:
        return True
    else:
        return False


def min_length(point_from, point_to):
    depend_nodes = collections.defaultdict(list)
    for line in Line.objects.all():
        point_from = line.from_point.id
        point_to = line.to_point.id
        depend_nodes[point_from].append(point_to)
        depend_nodes[point_to].append(point_from)
    path = astar(1, neighbors, goal, 0, distance_eval, heuristic_eval)
    print(path)
    pass


class PointsView(APIView):
    def get(self, request):
        geojson_answer = serialize('geojson', Point.objects.all(),
                                   geometry_field='geom',
                                   fields=('score',))
        return Response({"points": geojson_answer})


class MinLength(APIView):

    def get(self, request, **kwargs):
        point_from = self.kwargs['from']
        point_to = self.kwargs['to']
        min_length(point_from, point_to)
        geojson_answer = serialize('geojson', Point.objects.filter(Q(id=self.kwargs['from']) | Q(id=self.kwargs['to'])),
                                   geometry_field='geom',
                                   fields=('score', 'geom'))
        return Response({"points": geojson_answer})


class MinScore(APIView):
    pass
