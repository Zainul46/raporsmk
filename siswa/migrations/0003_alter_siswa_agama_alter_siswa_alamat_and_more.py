# Generated by Django 4.2.2 on 2023-07-11 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('siswa', '0002_alter_siswa_nis'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siswa',
            name='agama',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='siswa',
            name='alamat',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='siswa',
            name='nama',
            field=models.CharField(max_length=50, verbose_name='Nama Siswa'),
        ),
        migrations.AlterField(
            model_name='siswa',
            name='nama_ayah',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='siswa',
            name='nama_ibu',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='siswa',
            name='nama_wali',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='siswa',
            name='sekolah_asal',
            field=models.CharField(max_length=25),
        ),
        migrations.AlterField(
            model_name='siswa',
            name='tempat_lahir',
            field=models.CharField(max_length=20),
        ),
    ]