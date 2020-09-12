import collections
from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from mainapp.models import Point, Line
from mainapp.serializers import PointsSerializer
from django.core.serializers import serialize

from mainapp.tests import astar


def min_length(_from, _to):
    depend_nodes = collections.defaultdict(list)
    for line in Line.objects.all():
        # формируем словарь узел (int) - связи (list)
        n_from = line.from_point.id
        n_to = line.to_point.id
        depend_nodes[n_from].append(n_to)
        depend_nodes[n_to].append(n_from)

    def distance_eval(a, b):
        """Расчет дистанции между a & b в километрах"""
        return Point.objects.get(id=a).geom.distance(Point.objects.get(id=b).geom) * 100

    def heuristic_eval(pos):
        """Расчет эвристики конечная точка эвристики - последний узел (собственная длина)"""
        s_length = len(Point.objects.all())
        return Point.objects.get(id=pos).geom.distance(Point.objects.get(id=s_length).geom) * 100

    def goal(pos):
        """Функция, возвращающая True при достижении цели и False в противном случае"""
        if pos == _to:
            return True
        else:
            return False

    def neighbors(node):
        """Функция, возвращающая всех соседей точки (pos): function > returns list"""
        return depend_nodes[node]

    def path_in_km(path_list):
        distance = 0
        for i in range(len(path_list)):
            if len(path[i:i + 2]) == 2:
                section = path_list[i:i + 2]
                distance += distance_eval(section[0], section[1])
        return distance

    path = astar(_from, neighbors, goal, 0, distance_eval, heuristic_eval)
    #  тут вернуть geojson?
    return f'Кратчайший путь от {_from} до {_to} проходит через ' \
           f'точки: {path}, общая длина этого пути: {path_in_km(path)} км'


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