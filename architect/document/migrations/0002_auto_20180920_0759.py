# Generated by Django 2.1.1 on 2018-09-20 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='engine',
            field=models.CharField(default='dashboard', max_length=32, verbose_name='Engine'),
        ),
        migrations.AlterField(
            model_name='document',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Document name'),
        ),
        migrations.AlterField(
            model_name='document',
            name='status',
            field=models.CharField(default='active', max_length=32, verbose_name='Status'),
        ),
    ]
