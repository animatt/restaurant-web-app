# Generated by Django 2.1.3 on 2018-11-12 00:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0002_customers_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payments',
            name='customer',
        ),
        migrations.AddField(
            model_name='payments',
            name='employee',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='timeline.Employees'),
        ),
        migrations.AddField(
            model_name='payments',
            name='reservation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='timeline.Reservations'),
        ),
        migrations.AlterField(
            model_name='reservations',
            name='res_datetime',
            field=models.DateTimeField(verbose_name='date of reservation'),
        ),
    ]