# Generated by Django 3.2.8 on 2021-11-17 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_auto_20211112_1335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='amount_paid',
            field=models.CharField(max_length=50),
        ),
    ]