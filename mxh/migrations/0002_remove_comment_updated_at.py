# Generated by Django 4.2.8 on 2024-12-02 10:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mxh', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='updated_at',
        ),
    ]
