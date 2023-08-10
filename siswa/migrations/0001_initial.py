# Generated by Django 4.2.2 on 2023-06-08 01:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sekolah', '0003_ekskul_jurusan_kelas_kkm_matapelajaran_rapor'),
    ]

    operations = [
        migrations.CreateModel(
            name='Siswa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=255, verbose_name='Nama Siswa')),
                ('nisn', models.CharField(max_length=10)),
                ('nis', models.CharField(max_length=9)),
                ('email', models.EmailField(max_length=254)),
                ('tempat_lahir', models.CharField(max_length=255)),
                ('tanggal_lahir', models.DateField()),
                ('gender', models.CharField(choices=[('P', 'Pria'), ('W', 'Wanita')], default='P', max_length=1, verbose_name='Jenis Kelamin')),
                ('agama', models.CharField(max_length=255)),
                ('alamat', models.CharField(max_length=255)),
                ('sekolah_asal', models.CharField(max_length=255)),
                ('diterima_di_tingkat', models.CharField(choices=[('10', '10'), ('11', '11'), ('12', '12')], max_length=3)),
                ('nama_ayah', models.CharField(max_length=255)),
                ('nama_ibu', models.CharField(max_length=255)),
                ('nama_wali', models.CharField(blank=True, max_length=255, null=True)),
                ('kelas', models.ManyToManyField(blank=True, related_name='siswa', to='sekolah.kelas')),
            ],
        ),
        migrations.CreateModel(
            name='NilaiEkskul',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nilai', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C')], max_length=1)),
                ('ekskul', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nilai', to='sekolah.ekskul')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nilai_ekskul', to='sekolah.semester')),
                ('siswa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ekskul', to='siswa.siswa')),
            ],
        ),
        migrations.CreateModel(
            name='Nilai',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pengetahuan', models.PositiveSmallIntegerField()),
                ('keterampilan', models.PositiveSmallIntegerField()),
                ('matapelajaran', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nilai', to='sekolah.matapelajaran')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nilai', to='sekolah.semester')),
                ('siswa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nilai', to='siswa.siswa')),
            ],
        ),
        migrations.CreateModel(
            name='Absensi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('izin', models.PositiveSmallIntegerField(default=0)),
                ('sakit', models.PositiveSmallIntegerField(default=0)),
                ('bolos', models.PositiveSmallIntegerField(default=0)),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='absensi', to='sekolah.semester')),
                ('siswa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='absensi', to='siswa.siswa')),
            ],
        ),
    ]