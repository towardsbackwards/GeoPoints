from rest_framework import serializers
from django.core.serializers import serialize
from rest_framework_gis.serializers import GeometryField


class SerializerPointFields(GeometryField):
    def to_representation(self, value):
        value = super(
            SerializerPointFields, self).to_representation(value)
        # change to compatible with google map
        data = {
            'lat (y)': value['coordinates'][1],
            'lon (x)': value['coordinates'][0]
        }
        return data


class PointsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    geom = SerializerPointFields()  # X is longitude and Y is latitude
    score = serializers.IntegerField()
