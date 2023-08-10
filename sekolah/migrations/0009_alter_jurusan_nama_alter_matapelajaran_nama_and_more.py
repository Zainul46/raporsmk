# Generated by Django 4.2.2 on 2023-07-11 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sekolah', '0008_alter_jurusan_nama_alter_matapelajaran_nama_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jurusan',
            name='nama',
            field=models.CharField(max_length=255, verbose_name='Nama Lengkap'),
        ),
        migrations.AlterField(
            model_name='matapelajaran',
            name='nama',
            field=models.CharField(max_length=255, verbose_name='Nama Mata Pelajaran'),
        ),
        migrations.AlterField(
            model_name='semester',
            name='nama',
            field=models.CharField(editable=False, max_length=255, null=True),
        ),
    ]
