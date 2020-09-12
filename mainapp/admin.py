from django.contrib import admin
#  from django.contrib.gis.admin import GeoModelAdmin

from mainapp.models import Line, Point

admin.site.register(Line)
admin.site.register(Point)
