# Generated by Django 3.2.8 on 2021-11-17 10:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_auto_20211117_0958'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderproduct',
            old_name='is_ordered',
            new_name='ordered',
        ),
    ]
