# Generated by Django 4.2.2 on 2023-07-11 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guru', '0005_alter_guru_nama_gelar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guru',
            name='agama',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='guru',
            name='alamat',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='guru',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='guru',
            name='tempat_lahir',
            field=models.CharField(max_length=255, null=True),
        ),
    ]