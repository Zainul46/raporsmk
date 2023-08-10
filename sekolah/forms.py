from django import forms
from django_select2 import forms as s2forms
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import OperationalError, ProgrammingError
from .models import Ekskul, Jurusan, KKM, Kelas, MataPelajaran, Semester, Sekolah, TahunPelajaran


def active_tp():
            try:
                from sekolah.models import TahunPelajaran
                return TahunPelajaran.objects.get(is_active=True)
            except ObjectDoesNotExist:
                return None
            except OperationalError:
                return None
            except ProgrammingError:
                return None
def tingkat_choice(sekolah):
    if sekolah:
        if sekolah.tingkat == 'SMK':
            return [
                ('10', '10'),
                ('11', '11'),
                ('12', '12'),
            ]
        else:
            return [ 
                ('10', '10'),
                ('11', '11'),
                ('12', '12'),
            ]
def get_sekolah():
    from sekolah.models import Sekolah
    try:
        return Sekolah.objects.get_or_create()[0]
    except ObjectDoesNotExist:
        return None
    except OperationalError:
        return None        
def walikelas_choice(validwalikelas):
    vw = {}
    vw[None] = '---------'
    for walikelas in validwalikelas:
        vw[walikelas.nip] = walikelas.nama
    return [(nip, walikelas) for nip, walikelas in vw.items()]
def get_validwalikelas():
    from guru.models import Guru
    from sekolah.models import Kelas
    valid_walikelas = []
    all_walikelas = Guru.objects.filter(is_walikelas=True, is_active=True)
    tp = active_tp()
    for walikelas in all_walikelas:
        try:
            list_kelas = [kelas.tahun_pelajaran for kelas in Kelas.objects.select_related('tahun_pelajaran').filter(walikelas=walikelas)]
            if not tp in list_kelas:
                raise ObjectDoesNotExist
        except ObjectDoesNotExist:
            valid_walikelas.append(walikelas)
        return valid_walikelas
    
class SekolahForm(forms.ModelForm):
    class Meta:
        model = Sekolah
        exclude = ('tingkat_verbose',)

class SemesterForm(forms.ModelForm):
    mulai = forms.IntegerField(label='Tahun Mulai')
    akhir = forms.IntegerField(label='Tahun Akhir')
    class Meta:
        model = TahunPelajaran
        fields = ('mulai', 'akhir')

class KelasForm(forms.ModelForm):
    try:
        
        tingkat = forms.ChoiceField(choices=tingkat_choice(get_sekolah()))
        walikelas = forms.ChoiceField(choices=walikelas_choice(get_validwalikelas()), required=False)
    except Exception:
        pass

    def __init__(self, tingkat_list, walikelas_list, *args, **kwargs):
        super(KelasForm, self).__init__(*args, **kwargs)
        self.fields["tingkat"] = forms.ChoiceField(choices=tingkat_list)
        self.fields["walikelas"] = forms.ChoiceField(choices=walikelas_list, required=False)
    class Meta:
        model = Kelas
        fields = ('tingkat', 'jurusan', 'kelas')

class DisabledKelasForm(forms.ModelForm):
    try:
        tingkat = forms.CharField()
        walikelas = forms.CharField()
        jurusan = forms.CharField()
        kelas = forms.CharField()
    except Exception:
        pass
    class Meta:
        model = Kelas
        fields = ('tingkat', 'jurusan', 'kelas')

class JurusanForm(forms.ModelForm):
    class Meta:
        model = Jurusan
        fields = '__all__'

class EkskulForm(forms.ModelForm):
    class Meta:
        model = Ekskul
        fields = '__all__'

class MultiMatapelajaran(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "nama__icontains",
        "kelompok__icontains",
    ]

class MultiSiswa(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "nama__icontains",
        "nis__istartswith",
        "nisn__istartswith",
        ]

class TambahMatapelajaranKelas(forms.ModelForm):
    def __init__(self, mapel_list, *args, **kwargs):
        super(TambahMatapelajaranKelas, self).__init__(*args, **kwargs)
        self.fields["matapelajaran"] = forms.MultipleChoiceField(choices=mapel_list)
    class Meta:
        model = Kelas
        fields = ('matapelajaran',)
        widgets = {
            'matapelajaran': MultiMatapelajaran
        }

class TambahAnggotaKelas(forms.Form):
    siswa = forms.MultipleChoiceField(widget=MultiSiswa)

    def __init__(self, anggota_list, *args, **kwargs):
        super(TambahAnggotaKelas, self).__init__(*args, **kwargs)
        self.fields["siswa"] = forms.MultipleChoiceField(choices=anggota_list)

class MatapelajaranForm(forms.ModelForm):
    class Meta:
        model = MataPelajaran
        fields = '__all__'

class EditMatapelajaranForm(forms.ModelForm):
    pengetahuan = forms.IntegerField()
    keterampilan = forms.IntegerField()
    class Meta:
        model = MataPelajaran
        fields = '__all__'

class KKMForm(forms.ModelForm):
    class Meta:
        model = KKM
        fields = ('pengetahuan', 'keterampilan')