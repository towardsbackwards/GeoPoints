import requests
from django.core.management import BaseCommand
from django.db import transaction
from django.contrib.gis.geos import Point as GeoPoint
from GeoPoints.settings import JSON_LOCAL_PATH
from mainapp.models import Point, Line
import json

json_path = 'https://datum-test-task.firebaseio.com/api/lines-points.json'


def get_json(path):
    """Получение JSON-данных для БД и сохранение их на диск"""
    local_path = JSON_LOCAL_PATH
    if requests.get(path).status_code == 200:
        json_data = requests.get(path).json()
        with open(local_path, 'w') as outfile:  # сохранение на всякий случай
            json.dump(json_data, outfile, indent=4)  # сохранение на всякий случай
        return json_data
    else:
        print(f'JSON request error {requests.get(path).status_code}')
        return None


json_data = get_json(json_path)


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        """Наполняет базу с нуля, использовать:
        python manage.py fill_db"""
        if json_data:
            for point in json_data['points']:
                new_point = Point(
                    pk=point['obj_id'],
                    geom=GeoPoint(point['lon'], point['lat']),
                    score=point['score']
                )
                new_point.save()
            for num, line in enumerate(json_data['lines']):
                new_line = Line(
                    pk=(num + 1),
                    from_point=Point.objects.get(pk=line['from_obj']),
                    to_point=Point.objects.get(pk=line['to_obj'])
                )
                new_line.save()
            print('Database objects created!')
        else:
            print('Database fill error. JSON data is empty!')
