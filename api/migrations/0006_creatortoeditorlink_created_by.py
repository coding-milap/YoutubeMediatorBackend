# Generated by Django 5.0.1 on 2024-02-14 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='creatortoeditorlink',
            name='created_by',
            field=models.CharField(default='null', max_length=200),
        ),
    ]
