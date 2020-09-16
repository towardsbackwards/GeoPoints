from django.contrib.gis.db import models


class Point(models.Model):
    geom = models.PointField(null=True)  # X is longitude and Y is latitude
    score = models.IntegerField(null=True)
    address = models.TextField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return f'{self.geom[0]} {self.geom[1]}, score {self.score}'


class Line(models.Model):
    from_point = models.ForeignKey(Point, on_delete=models.CASCADE, related_name='from_point', null=True)
    to_point = models.ForeignKey(Point, on_delete=models.CASCADE, related_name='to_point', null=True)

    def __str__(self):
        return f'From {self.from_point.geom} (score={self.from_point.score}) ' \
               f'to {self.to_point.geom} (score={self.to_point.score})'

