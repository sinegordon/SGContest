from django.db import models


class CourseSettings(models.Model):
    course = models.CharField(max_length=255, unique=True)
    rating_1_count = models.PositiveIntegerField(default=1)
    rating_2_count = models.PositiveIntegerField(default=0)
    rating_3_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("course",)

    def __str__(self):
        return self.course

    @property
    def problem_counts(self):
        return {
            1: self.rating_1_count,
            2: self.rating_2_count,
            3: self.rating_3_count,
        }
