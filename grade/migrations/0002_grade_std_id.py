# Generated by Django 4.1.5 on 2023-01-19 04:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grade', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='grade',
            name='std_id',
            field=models.CharField(default=232131231, max_length=15),
            preserve_default=False,
        ),
    ]
