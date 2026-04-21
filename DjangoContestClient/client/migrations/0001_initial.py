from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CourseSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("course", models.CharField(max_length=255, unique=True)),
                ("rating_1_count", models.PositiveIntegerField(default=1)),
                ("rating_2_count", models.PositiveIntegerField(default=0)),
                ("rating_3_count", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ("course",)},
        ),
    ]
