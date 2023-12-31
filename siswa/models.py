from django.db import models
from django.db.models.query_utils import Q
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.dispatch import receiver
from sekolah.models import Kelas, MataPelajaran, Semester, Ekskul

# Create your models here.
class Siswa(models.Model):
    GENDER_CHOICE = [
        ('P', 'Pria'),
        ('W', 'Wanita')
    ]
    TINGKAT_KELAS_CHOICE = [ 
            ('10', '10'),
            ('11', '11'),
            ('12', '12'),
    ]
    nama = models.CharField(max_length=50, verbose_name='Nama Siswa')
    nisn = models.CharField(max_length=10)
    nis = models.CharField(max_length=10)
    email = models.EmailField()
    tempat_lahir = models.CharField(max_length=50)
    tanggal_lahir = models.DateField()
    gender = models.CharField(verbose_name='Jenis Kelamin', max_length=1, choices=GENDER_CHOICE, default=GENDER_CHOICE[0][0])
    agama = models.CharField(max_length=10)
    alamat = models.CharField(max_length=20)
    sekolah_asal = models.CharField(max_length=30)
    diterima_di_tingkat = models.CharField(max_length=3, choices=TINGKAT_KELAS_CHOICE)
    nama_ayah = models.CharField(max_length=50)
    nama_ibu = models.CharField(max_length=50)
    nama_wali = models.CharField(max_length=50, null=True, blank=True)
    kelas = models.ManyToManyField(Kelas, related_name='siswa', blank=True)

    def __str__(self):
        return f'{self.nisn}/{self.nis}-{self.nama}'

@receiver(models.signals.pre_save, sender=Siswa)
def siswa_pre_save(sender, instance, **kwargs):
    try:
        siswa = Siswa.objects.filter(Q(nis=instance.nis) | Q(nisn=instance.nisn))
        if siswa and instance not in siswa:
            raise IntegrityError('NIS or NISN must be unique.')
    except ObjectDoesNotExist:
        pass
    
class Nilai(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name='nilai')
    matapelajaran = models.ForeignKey(MataPelajaran, on_delete=models.CASCADE, related_name='nilai')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='nilai')
    pengetahuan = models.PositiveSmallIntegerField()
    keterampilan = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.siswa}/{self.matapelajaran}/{self.semester}'

    def save(self, *args, **kwargs):
        if self.pengetahuan < 0: self.pengetahuan = 0
        if self.pengetahuan > 100: self.pengetahuan = 100
        if self.keterampilan < 0: self.keterampilan = 0
        if self.keterampilan > 100: self.keterampilan = 100

        super(Nilai, self).save(*args, **kwargs)

@receiver(models.signals.pre_save, sender=Nilai)
def unique_together_tp_mapel(sender, instance, **kwargs):
    try:
        nilai = Nilai.objects.filter(siswa=instance.siswa, matapelajaran=instance.matapelajaran, semester=instance.semester)
        if nilai and instance not in nilai:
            raise ValidationError('Nilai for that Siswa with that Mata Pelajaran in that Semester already exists')
    except ObjectDoesNotExist:
        pass


class Absensi(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name='absensi')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='absensi')
    izin = models.PositiveSmallIntegerField(default=0)
    sakit = models.PositiveSmallIntegerField(default=0)
    bolos = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'{self.siswa}/{self.semester}'

@receiver(models.signals.pre_save, sender=Absensi)
def unique_together_siswa_semester(sender, instance, **kwargs):
    try:
        absen = Absensi.objects.filter(siswa=instance.siswa, semester=instance.semester)
        if absen and instance not in absen:
            raise ValidationError('Absen for that siswa in that semester already exists')
    except ObjectDoesNotExist:
        pass


class NilaiEkskul(models.Model):
    NILAI_EKSKUL = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ]
    ekskul = models.ForeignKey(Ekskul, on_delete=models.CASCADE, related_name='nilai')
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name='ekskul')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='nilai_ekskul')
    nilai = models.CharField(max_length=1, choices=NILAI_EKSKUL)

    def __str__(self):
        return f'{self.siswa} - {self.ekskul} - {self.nilai}'

@receiver(models.signals.pre_save, sender=NilaiEkskul)
def unique_together_siswa_ekskul_semester(sender, instance, **kwargs):
    try:
        nileks = NilaiEkskul.objects.filter(siswa=instance.siswa, semester=instance.semester, ekskul=instance.ekskul)
        if nileks and instance not in nileks:
            raise ValidationError('Nilai Ekskul for that siswa in that semester already exists')
    except ObjectDoesNotExist:
        pass