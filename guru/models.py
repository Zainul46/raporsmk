from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.dispatch import receiver
from raporsmk.settings import MEDIA_ROOT
import requests
import os

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, nip, nama, password=None):
        if not nip or not nama:
            raise ValueError("Data is not complete")        

        user = self.model(nip = nip, nama = nama)
        if user.is_superuser:
            user.is_admin = True
            user.is_staff = True            
            user.is_walikelas = True
            user.is_staftu = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nip, nama, password):
        user = self.create_user(nip = nip, password = password, nama = nama)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_walikelas = True
        user.is_staftu = True
        user.save(using=self._db)
        return user
    
class Guru(AbstractBaseUser):
    GENDER_CHOICE = [
        ('P', 'Pria'),
        ('W', 'Wanita')
    ]
    nip = models.CharField(verbose_name='Nomor Induk', unique=True, max_length=18)    
    nama = models.CharField(max_length=50)
    nama_gelar = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True)
    gender = models.CharField(verbose_name='Jenis Kelamin', max_length=1, choices=GENDER_CHOICE, default=GENDER_CHOICE[0][0])
    tempat_lahir = models.CharField(max_length=20, null=True)
    tanggal_lahir = models.DateField(null=True)
    agama = models.CharField(max_length=10, null=True)
    alamat = models.CharField(max_length=100, null=True)
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    first_login = models.BooleanField(default=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_walikelas = models.BooleanField(default=True, verbose_name='Walikelas')
    is_staftu = models.BooleanField(default=False, verbose_name='Staf TU')
    is_active = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatar/guru/', null=True, blank=True)

    USERNAME_FIELD = 'nip'
    REQUIRED_FIELDS = ['nama',]

    objects = UserManager()

    def __str__(self):
        return self.nama or ''

    def save(self, *args, **kwargs):
        try:
            self.nama_gelar = gelarize_nama_guru(self.nip)
        except Guru.DoesNotExist:
            pass
        return super(Guru, self).save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

@receiver(models.signals.pre_save, sender=Guru)
def guru_pre_save(sender, instance, **kwargs):
    try:
        old_file = sender.objects.get(pk=instance.pk).avatar.path
        new_file = instance.avatar
        if (old_file and not new_file) or (old_file and new_file and not old_file == new_file):
            if os.path.isfile(old_file):
                os.remove(old_file)
            
    except sender.DoesNotExist:
        return False
    except ValueError:
        return False
    except Exception as e:
        print(e)

def avatarAPI(subjek):
    if subjek.nip: 
        output_dir = f'{MEDIA_ROOT}avatar/guru'
        image_name = subjek.nip
    else: 
        output_dir = f'{MEDIA_ROOT}avatar/siswa'
        image_name = subjek.nis
    image = requests.get(f'https://ui-avatars.com/api/?name={subjek.nama}&background=random&size=100')
    if not os.path.isdir(output_dir): os.makedirs(output_dir)
    if image.status_code == 200:
        with open(f"{output_dir}/{image_name}.png", 'wb') as f:
            f.write(image.content)
        f.close()
        return f"{output_dir}/{image_name}.png"
    else:
        raise Exception

@receiver(models.signals.post_save, sender=Guru)
def guru_post_save(sender, instance, created, **kwargs):
    if not instance.avatar:
        instance.avatar = avatarAPI(instance)
        instance.save()

@receiver(models.signals.post_delete, sender=Guru)
def guru_post_delete(sender, instance, **kwargs):
    image = instance.avatar.path
    if image:
        if os.path.isfile(image):
            os.remove(image)

class Gelar(models.Model):
    TINGKAT_GELAR_CHOICE = [
        ('A.P.', 'Diploma 1'),
        ('A.Ma.', 'Diploma 2'),
        ('A.Md.', 'Diploma 3'),
        ('A.', 'Diploma 4'),
        ('S.', 'Sarjana'),
        ('M.', 'Magister'),
        ('Dr.', 'Doktor'),
    ]
    JURUSAN_GELAR_CHOICE = (
        ('Administrasi', (
                ('A.B.', 'Administrasi Bisnis'),
                ('Pn.', 'Administrasi Fiskal'),
                ('Adm.', 'Administrasi Negara'),
                ('A.P.', 'Administrasi Perkantoran'),
                ('I.P.', 'Ilmu Perpustakaan'),
            )
        ),
        ('Ekonomi', (
                ('Ak.', 'Akuntansi'),
                ('E.', 'Ilmu Ekonomi'),
                ('E.', 'Manajemen'),
            )
        ),
        ('Kesehatan', (
                ('Farm.', 'Farmasi'),
                ('Gz.', 'Ilmu Gizi'),
                ('Keb.', 'Kebidanan'),
                ('Ked.', 'Kedokteran'),
                ('K.G.', 'Kedokteran Gigi'),
                ('K.H.', 'Kedokteran Hewan'),
                ('Kep.', 'Keperawatan'),
                ('K.M.', 'Kesehatan Masyarakat'),
                ('Psi.', 'Psikologi'),
            )
        ),
        ('Kesenian', (
                ('Ds.', 'Desain Komunikasi Visual'),
                ('Ds.', 'Desain Produk'),
                ('Sn.', 'Seni Kriya'),
                ('Sn.', 'Seni Musik'),
                ('Sn.', 'Seni Rupa'),
                ('Sn.', 'Seni Tari'),
            )
        ),
        ('Ilmu Budaya', (
                ('Hum.', 'Humaniora'),
                ('Fil.', 'Filsafat'),
                ('Hum.', 'Ilmu Sejarah'),
                ('Par.', 'Pariwisata'),
                ('S.', 'Sastra'),
            )
        ),
    
        ('Matematika & IPA', (
                ('Si.', 'Astronomi'),
                ('Si.', 'Biologi'),
                ('Si.', 'Fisika'),
                ('Si.', 'Geofisika'),
                ('Si.', 'Geologi'),
                ('Si.', 'Kimia'),
                ('Si.', 'Matematika'),
                ('Stat.', 'Statistika'),
            )
        ),
        ('Pendidikan', (
                ('Pd.', 'Pendidikan Agama Islam'),
                ('Pd.', 'Bimbingan Konseling'),
                ('Pd.', 'Kebijakan Pendidikan'),
                ('Pd.', 'Manajemen Pendidikan'),
                ('Pd.', 'Pendidikan Luar Biasa'),
                ('Pd.', 'Pendidikan Luar Sekolah'),
                ('Pd.', 'PGPAUD'),
                ('Pd.', 'PGSD'),
                ('Pd.', 'Teknologi Pendidikan'),
            )
        ),
        ('Pertanian', (
                ('P.', 'Agribisnis'),
                ('P.', 'Agroteknologi'),
                ('P.', 'Ilmu Tanah'),
                ('Hut.', 'Kehutanan'),
                ('Pi.', 'Perikanan'),
                ('T.P.', 'Teknologi Hasil Pertanian'),
            )
        ),
        ('Sosial', (
                ('Ant.', 'Antropologi Sosial'),
                ('H.Int.', 'Hubungan Internasional'),
                ('H.', 'Hukum'),
                ('Si.', 'Geografi'),
                ('Sos.', 'Ilmu Kesejahteraan Sosial'),
                ('I.Kom.', 'Ilmu Komunikasi'),
                ('IP.', 'Ilmu Politik'),
                ('Sos.', 'Kriminologi'),
                ('Sos.', 'Sosiologi'),
            )
        ),
        ('Teknik', (
                ('Ars.', 'Arsitektur'),
                ('Kom.', 'Ilmu Komputer'),
                ('Kom.', 'Sistem Informasi'),
                ('Kom.', 'Teknik Informatika'),
                ('T.', 'Teknik Bioproses'),
                ('T.', 'Teknik Elektro'),
                ('T.', 'Teknik Elektronika'),
                ('T.', 'Teknik Fisika'),
                ('T.', 'Teknik Geodesi'),
                ('T.', 'Teknik Geofisika'),
                ('T.', 'Teknik Geologi'),
                ('T.', 'Teknik Industri'),
                ('T.', 'Teknik Kelautan'),
                ('T.', 'Teknik Kimia'),
                ('T.', 'Teknik Telekomunikasi'),
                ('T.', 'Teknik Lingkungan'),
                ('T.', 'Teknik Metalurgi'),
                ('T.', 'Teknik Mekatronika'),
                ('T.', 'Teknik Mesin'),
                ('T.', 'Teknik Nuklir'),
                ('T.', 'Teknik Otomotif'),
                ('T.', 'Teknik Permniyakan'),
                ('T.', 'Teknik Pertambangan'),
                ('T.', 'Teknik Sipil'),
                ('T.', 'Teknik Transportasi Laut'),
            )
        ),
    )
    guru = models.ForeignKey(Guru, on_delete=models.CASCADE)
    tingkat_gelar = models.CharField(choices=TINGKAT_GELAR_CHOICE, max_length=5)
    verbose_tingkat = models.CharField(null=True, blank=True, max_length=255)
    jurusan = models.CharField(choices=JURUSAN_GELAR_CHOICE, max_length=255)
    verbose_jurusan = models.CharField(null=True, blank=True, max_length=255)
    universitas = models.CharField(max_length=255)
    gelar = models.CharField(null=True, blank=True, max_length=255)

    def save(self, *args, **kwargs):
        self.verbose_tingkat = self.get_tingkat_gelar_display()
        self.verbose_jurusan = self.get_jurusan_display()
        self.gelar = self.tingkat_gelar + self.jurusan
        return super(Gelar, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.guru.nama} {self.gelar} {self.universitas}'

@receiver(models.signals.pre_save, sender=Gelar)
def gelar_pre_save(sender, instance, **kwargs):
    try:
        gelar = Gelar.objects.filter(guru=instance.guru, tingkat_gelar=instance.tingkat_gelar, jurusan=instance.jurusan)
        if gelar and instance not in gelar:
            raise ValidationError("Gelar already exists")
    except Gelar.DoesNotExist:
        pass

@receiver(models.signals.post_save, sender=Gelar)
def gelar_post_save(sender, instance, **kwargs):
    Guru.objects.get(nip=instance.guru.nip).save()

@receiver(models.signals.post_delete, sender=Gelar)
def gelar_post_delete(sender, instance, **kwargs):
    Guru.objects.get(nip=instance.guru.nip).save()

def gelarize_nama_guru(nip):
    guru = Guru.objects.get(nip=nip)
    nama = guru.nama
    gelar = Gelar.objects.filter(guru=guru).order_by('verbose_tingkat', 'jurusan')
    order = ['Diploma 1', 'Diploma 2', 'Diploma 3', 'Diploma 4', 'Sarjana', 'Magister', 'Doktor']
    gelar = sorted(gelar, key=lambda x: order.index(x.verbose_tingkat))
    for gelar in gelar:
        vb_tingkat = gelar.verbose_tingkat
        if not 'Doktor' == vb_tingkat:
            nama = nama+', '+gelar.gelar    
        elif 'Doktor' == gelar.verbose_tingkat and not str(nama).startswith('Dr. '):
            nama = 'Dr. '+nama

    return nama