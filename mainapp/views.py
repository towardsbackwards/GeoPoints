import json
import requests
from .API import YA_GEOCODER_API_KEY
from rest_framework.response import Response
from rest_framework.views import APIView
from mainapp.models import Point, Line
from django.core.serializers import serialize

from mainapp.algorithm import best_path_by

answer_blank = {"type": "FeatureCollection",
                "features": [
                    {"type": "Feature",
                     "geometry": {
                         "type": "LineString",
                     },
                     "properties": {
                     }
                     },
                ]
                }


def get_address(point):
    """&geocode = <долгота, широта>"""

    long = Point.objects.get(id=point).geom.x
    lat = Point.objects.get(id=point).geom.y
    request = (requests.get(f'https://geocode-maps.yandex.ru/1.x/?format=json&apikey={YA_GEOCODER_API_KEY}'
                           f'&geocode={long},{lat}')).json()
    address = request['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
    return address


class MinLength(APIView):

    def get(self, request, **kwargs):
        point_from = self.kwargs['from']
        point_to = self.kwargs['to']
        result_km = best_path_by(point_from, point_to, Line, Point)
        print(result_km)
        geojson_coords = answer_blank['features'][0]['geometry']['coordinates'] = []
        for i in Point.objects.filter(id__in=result_km['path']):
            geojson_coords.append([i.geom[0], i.geom[1]])
            answer_blank['features'][0]['properties']['address'] = get_address(i.id)
        answer_blank['features'][0]['properties']['name'] = 'Shortest path'

        return Response({"answer": answer_blank})


class MinScore(APIView):

    def get(self, request, **kwargs):
        point_from = self.kwargs['from']
        point_to = self.kwargs['to']
        result_score = best_path_by(point_from, point_to, Line, Point, eval_type='by_score')
        print(result_score)
        geojson_coords = answer_blank['features'][0]['geometry']['score_points'] = []
        for i in Point.objects.filter(id__in=result_score['path']):
            geojson_coords.append([i.score])
        answer_blank['features'][0]['properties']['name'] = 'Cheapest path'
        return Response({"answer": answer_blank})


class PointsView(APIView):

    def get(self, request):
        geojson_answer = json.loads(serialize('geojson', Point.objects.all(),
                                              geometry_field='geom',
                                              fields=('score', 'pk')))
        return Response({"points": geojson_answer})
