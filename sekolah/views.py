from django.shortcuts import redirect, render
from guru.models import Guru
from siswa.models import Absensi, Siswa
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.query_utils import Q
from django.http.response import Http404
from django.views.generic import View
from django.utils.decorators import method_decorator
from .models import Ekskul, Jurusan, KKM, Kelas, MataPelajaran, Rapor, Sekolah, Semester, TahunPelajaran
from .forms import DisabledKelasForm, EditMatapelajaranForm, EkskulForm, JurusanForm, KKMForm, KelasForm, MatapelajaranForm, SekolahForm, SemesterForm, TambahAnggotaKelas, TambahMatapelajaranKelas
from django.db.models.deletion import ProtectedError
from django.core.paginator import Paginator
from raporsmk.decorators import staftu_required, validdirs_required, activesemester_required, login_required
from raporsmk import settings
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from helpers import active_semester, active_tp, generate_rapor_context, get_initial, form_value, get_sekolah, get_validwalikelas, get_validsiswabaru, get_validpelajaran, semiactive_semester, tambahanggota_choice, tambahmapel_choice, walikelas_choice
from helpers import generate_pdf
from helpers.choice import tingkat_choice
from helpers.nilai_helpers import list_siswa_status, zip_pelkkm
import os, shutil

# Create your views here.

def index(request):
    return redirect('dashboard')


@method_decorator(login_required, name='dispatch')
class dashboard(View):
    def get(self, request):
        request.session['page'] = 'Dashboard'
        semester = active_semester()
        list_tp = TahunPelajaran.objects.all()
        list_tp = [tp for tp in list_tp]
        siswa_pria = [Siswa.objects.exclude(kelas=None).filter(kelas__tahun_pelajaran=tp, gender='P').count() for tp in list_tp]
        siswa_wanita = [Siswa.objects.exclude(kelas=None).filter(kelas__tahun_pelajaran=tp, gender='W').count() for tp in list_tp]
        tp = active_tp()
        context = {
            'sekolah': get_sekolah(),
            'semester': semester,
            'siswa_berkelas': Siswa.objects.exclude(kelas=None).filter(kelas__tahun_pelajaran=tp).count(),
            'siswa_nokelas': Siswa.objects.exclude(kelas__tahun_pelajaran=tp).filter(kelas=None).count(),
            'jumlah_kelas': Kelas.objects.filter(tahun_pelajaran=tp).count(),
            'jumlah_jurusan': Jurusan.objects.count(),
            'jumlah_guru': Guru.objects.count(),
            'jumlah_walikelas': Guru.objects.filter(is_walikelas=True, is_staftu=False).count(),
            'jumlah_tu': Guru.objects.filter(is_staftu=True, is_walikelas=False).count(),
            'jumlah_admin': Guru.objects.filter( Q( Q(is_walikelas=True)&Q(is_staftu=True) | Q(is_superuser=True) ) ).count(),
            'jumlah_mapel': MataPelajaran.objects.count(),
            'jumlah_ekskul': Ekskul.objects.count(),
            'chart_data': zip(list_tp, siswa_pria, siswa_wanita),
        }
        return render(request, 'pages/dashboard.html', context)

@method_decorator(login_required, name='dispatch')
class detail_sekolah(View):
    def get(self, request):
        request.session['page'] = 'Detail Sekolah'
        sekolah = Sekolah.objects.get()
        sekolah_form = SekolahForm(initial=get_initial(sekolah))
        context = {
            'sekolah_form': sekolah_form,
        }
        return render(request, 'pages/detail-sekolah.html', context)

    def post(self, request):
        sekolah_form = SekolahForm(request.POST)
        try:
            if sekolah_form.is_valid():
                Sekolah.objects.update(**form_value(sekolah_form))
                Sekolah.objects.get().save()
                messages.success(request, 'Data Sekolah berhasil diubah')
        except Exception as e:
            messages.error(request, e)
        finally:
            return redirect('detail-sekolah')
    
@method_decorator(staftu_required, name='dispatch')
class list_semester(View):
    def get(self, request):
        request.session['page'] = 'Daftar Tahun Pelajaran'
        if 'search' in request.GET and request.GET['search'] != '':
            list_tp = TahunPelajaran.objects.filter(
                Q(mulai__icontains=request.GET['search']) |
                Q(akhir__icontains=request.GET['search'])
            ).order_by('-mulai', '-akhir')
        else:
            list_tp = TahunPelajaran.objects.all().order_by('-mulai', '-akhir')
        tp = active_tp()
        paginator = Paginator(list_tp, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        number_of_pages = [(number+1) for number in range(page_obj.paginator.num_pages)]
        context = {
            'list_tp': page_obj,
            'page_obj': page_obj,
            'tp_form': SemesterForm(),
            'number_of_pages': number_of_pages,
            'jumlah_kelas': Kelas.objects.filter(tahun_pelajaran=active_tp()).count(),
            'jumlah_siswa': Siswa.objects.exclude(kelas=None).filter(kelas__tahun_pelajaran=tp).count(),
        }
        return render(request, 'pages/semester/semester.html', context)

@method_decorator(staftu_required, name='dispatch')
class buat_semester(View):
    def post(self, request):
        semester_form = SemesterForm(request.POST)
        try:
            if semester_form.is_valid():
                TahunPelajaran.objects.create(**form_value(semester_form))
                messages.success(request, 'Tahun Pelajaran berhasil dibuat')
        except ValidationError:
            messages.error(request, 'Tahun Pelajaran dengan data persis seperti itu sudah ada')
        except Exception as e:
            print(e)
        finally:
            return redirect('list-semester')

@method_decorator(staftu_required, name='dispatch')
class aktifkan_semester(View):
    def get(self, request, semester):
        semester = Semester.objects.get(pk=semester)
        semester.is_active = True
        semester.save()
        messages.success(request, 'Semester berhasil diaktifkan, data akan mengacu kepada semester ini')
        return redirect('list-semester')

@method_decorator(staftu_required, name='dispatch')
class hapus_semester(View):
    def get(self, request, semester):
        try:
            TahunPelajaran.objects.get(pk=semester).delete()
            messages.success(request, 'Tahun Pelajaran berhasil dihapus')
        except ProtectedError:
            messages.error(request, 'Tahun Pelajaran memiliki Semester yang masih menampung data, tidak dapat dihapus')
        finally:
            return redirect('list-semester')

@method_decorator(login_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class list_kelas(View):
    def get(self, request):
        request.session['page'] = 'Daftar Kelas'
        semester = active_semester()
        if 'search' in request.GET and request.GET['search'] != '':
            list_kelas = Kelas.objects.filter(
                Q(tahun_pelajaran=semester.tahun_pelajaran) & (
                Q(nama__icontains=request.GET['search']) |
                Q(walikelas__nama__icontains=request.GET['search']))
                ).order_by('jurusan', 'tingkat', 'kelas')
        else:
            list_kelas = Kelas.objects.filter(tahun_pelajaran=semester.tahun_pelajaran).order_by('jurusan', 'tingkat', 'kelas')
        
        paginator = Paginator(list_kelas, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        number_of_pages = [(number+1) for number in range(page_obj.paginator.num_pages)]
        context = {
            'page_obj': page_obj,
            'number_of_pages': number_of_pages,
            'list_kelas': list_kelas,
        }
        return render(request, 'pages/kelas/kelas.html', context)

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class buat_kelas(View):
    def get(self, request):
        request.session['page'] = 'Buat Kelas'
        context = {
            'kelas_form': KelasForm(tingkat_list=tingkat_choice(get_sekolah()), walikelas_list=walikelas_choice(get_validwalikelas())),
        }
        return render(request, 'pages/kelas/buat-kelas.html', context)
    def post(self, request):
        kelas_form = KelasForm(tingkat_choice(get_sekolah()), walikelas_choice(get_validwalikelas()), request.POST)
        try:
            if kelas_form.is_valid():
                try:
                    kelas_form.cleaned_data['walikelas'] = Guru.objects.get(nip=kelas_form.cleaned_data['walikelas'])
                except Guru.DoesNotExist:
                    kelas_form.cleaned_data['walikelas'] = None
                Kelas.objects.create(**form_value(kelas_form), tahun_pelajaran=active_tp())
                messages.success(request, 'Kelas berhasil dibuat, segera lengkapi data kelas tadi')
        except ValidationError:
            messages.error(request, 'Kelas itu sudah ada')
        finally:
            return redirect('list-kelas')

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class hapus_kelas(View):
    def get(self, request, kelas):
        tp = active_tp()
        try:
            Kelas.objects.get(nama=kelas, tahun_pelajaran=tp).delete()
            messages.success(request, f'Kelas {kelas} berhasil dihapus dari tahun pelajaran {tp}')
        except ProtectedError:
            messages.error(request, 'Kelas masih memiliki siswa, tidak dapat dihapus')
        finally:
            return redirect('list-kelas')

@method_decorator(login_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class detail_kelas(View):
    def get(self, request, kelas):
        request.session['page'] = f'Detail {kelas}'
        tp = active_tp()
        try:
            kelas = Kelas.objects.get(nama=kelas, tahun_pelajaran=tp)
        except ObjectDoesNotExist:
            raise Http404
        
        try:
            active_walikelas = Guru.objects.get(kelas=kelas)
        except ObjectDoesNotExist:
            active_walikelas = None
        
        if active_walikelas == request.user or request.user.is_superuser: auth_walikelas = True
        else: auth_walikelas = False

        initial = get_initial(kelas)
        if initial['walikelas']: initial['walikelas'] = Guru.objects.get(pk=initial['walikelas'])
        if initial['jurusan']: initial['jurusan'] = Jurusan.objects.get(id=initial['jurusan']).nama

        list_siswa = Siswa.objects.filter(kelas=kelas).order_by('nama')
        if list_siswa:
            finished, unfinished, status = list_siswa_status(list_siswa=list_siswa, semester=active_semester())
        else:
            finished = []
            unfinished = []
        
        list_mapel = MataPelajaran.objects.filter(kelas=kelas, kelas__tahun_pelajaran=tp).order_by('kelompok', 'nama')
        if list_mapel: list_mapel = zip_pelkkm(list_mapel, tp)
        context = {
            'kelas': kelas,
            'auth_walikelas': auth_walikelas,
            'kelas_form': DisabledKelasForm(initial=initial),
            'list_siswa': list_siswa,
            'jumlah_siswa': list_siswa.count(),
            'status_siswa': f'{len(finished)} Siswa tuntas / {len(unfinished)} Siswa belum tuntas',
            'list_matapelajaran': list_mapel,
            'active_walikelas': active_walikelas,
            'valid_walikelas': get_validwalikelas(),
            'tambahmapel_form': TambahMatapelajaranKelas(mapel_list=tambahmapel_choice(get_validpelajaran(kelas.nama))),
            'tambahanggota_form': TambahAnggotaKelas(anggota_list=tambahanggota_choice(get_validsiswabaru())),
        }
        return render(request, 'pages/kelas/detail-kelas.html', context)

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class ganti_walikelas(View):
    def post(self, request, kelas):
        kelas = Kelas.objects.get(id=kelas)
        if request.POST['new_walikelas']:
            if request.POST['new_walikelas'] == 'empty':
                kelas.walikelas = None
            else:
                new_walikelas = Guru.objects.get(nip=request.POST['new_walikelas'])
                kelas.walikelas = new_walikelas
            kelas.save()
            messages.success(request, f'Walikelas untuk {kelas.nama} berhasil diubah')
        return redirect('detail-kelas', kelas=kelas.nama)

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class tambah_anggota(View):
    def post(self, request, kelas):
        data = request.POST.getlist('siswa')
        kelas = Kelas.objects.get(id=kelas)
        for nis in data:
            siswa = Siswa.objects.get(nis=nis)
            siswa.kelas.add(kelas)
        messages.success(request, f'Anggota kelas berhasil ditambahkan ke kelas {kelas.nama}')
        return redirect('detail-kelas', kelas=kelas.nama)

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class hapus_anggota(View):
    def get(self, request, kelas, siswa):
        siswa = Siswa.objects.get(nis=siswa)
        kelas = Kelas.objects.get(id=kelas)
        siswa.kelas.remove(kelas)
        siswa.save()
        messages.success(request, f'{siswa.nama} berhasil dihapus dari anggota kelas {kelas.nama}')
        return redirect('detail-kelas', kelas=kelas.nama)

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class tambah_pelajaran(View):
    def post(self, request, kelas):
        data = request.POST.getlist('matapelajaran')
        kelas = Kelas.objects.get(id=kelas, tahun_pelajaran=active_tp())
        for _id in data:
            kelas.matapelajaran.add(_id)
        messages.success(request, f'Mata pelajaran berhasil ditambahkan ke kelas {kelas.nama}')
        return redirect('detail-kelas', kelas=kelas.nama)

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class hapus_pelajaran(View):
    def get(self, request, kelas, pelajaran):
        matapelajaran = MataPelajaran.objects.get(pk=pelajaran)
        kelas = Kelas.objects.get(id=kelas, tahun_pelajaran=active_tp())
        kelas.matapelajaran.remove(matapelajaran)
        messages.success(request, f'{matapelajaran.nama} berhasil dihapus dari kelas {kelas.nama}')
        return redirect('detail-kelas', kelas=kelas.nama)

@method_decorator(staftu_required, name='dispatch')
class list_jurusan(View):
    def get(self, request):
        request.session['page'] = 'Daftar Jurusan'
        context = {
            'list_jurusan': Jurusan.objects.all(),
            'jurusan_form': JurusanForm(),
        }
        return render(request, 'pages/jurusan/jurusan.html', context)

@method_decorator(staftu_required, name='dispatch')
class buat_jurusan(View):
    def post(self, request):
        jurusan_form = JurusanForm(request.POST)
        try:
            if jurusan_form.is_valid():
                jurusan = Jurusan.objects.create(**form_value(jurusan_form))
                messages.success(request, f'Jurusan {jurusan.nama} berhasil dibuat')
        except ValidationError:
            messages.error(request, f'Jurusan itu sudah tersedia')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan saat membuat jurusan')
        finally:
            return redirect('list-jurusan')

@method_decorator(staftu_required, name='dispatch')
class hapus_jurusan(View):
    def get(self, request, jurusan):
        try:
            jurusan = Jurusan.objects.get(pk=jurusan)
            nama_jurusan = jurusan.nama
            jurusan.delete()
            messages.success(request, f'{nama_jurusan} berhasil dihapus dari daftar jurusan sekolah')
        except ProtectedError:
            messages.error(request, f'{nama_jurusan} masih memiliki kelas aktif, tidak dapat dihapus')
        finally:
            return redirect('list-jurusan')

@method_decorator(staftu_required, name='dispatch')
class list_ekskul(View):
    def get(self, request):
        request.session['page'] = 'Daftar Ekskul'
        context = {
            'list_ekskul': Ekskul.objects.all().order_by('jenis'),
            'ekskul_form': EkskulForm(),
        }
        return render(request, 'pages/ekskul/ekskul.html', context)

@method_decorator(staftu_required, name='dispatch')
class buat_ekskul(View):
    def post(self, request):
        ekskul_form = EkskulForm(request.POST)
        try:
            if ekskul_form.is_valid():
                ekskul = Ekskul.objects.create(**form_value(ekskul_form))
                messages.success(request, f'Ekstrakulikuler {ekskul.nama} berhasil dibuat')
        except ValidationError:
            messages.error(request, f'Ekskul dengan data persis seperti itu sudah tersedia')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan saat membuat ekskul ')
        finally:
            return redirect('list-ekskul')

@method_decorator(staftu_required, name='dispatch')
class hapus_ekskul(View):
    def get(self, request, ekskul):
        try:
            ekskul = Ekskul.objects.get(pk=ekskul)
            nama_ekskul = ekskul.nama
            ekskul.delete()
            messages.success(request, f'{nama_ekskul} berhasil dihapus dari daftar ekstrakuliker sekolah')
        except Exception:
            messages.error(request, f'Terjadi kesalahan saat mencoba menghapus ekstrakulikuler')
        finally:
            return redirect('list-ekskul')

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class list_matapelajaran(View):
    def get(self, request):
        request.session['page'] = 'Daftar Matapelajaran'
        list_matapelajaran = MataPelajaran.objects.all().order_by('kelompok')
        context = {
            'list_matapelajaran': zip_pelkkm(list_matapelajaran, active_tp()),
            'matapelajaran_form': MatapelajaranForm(),
        }
        return render(request, 'pages/matapelajaran/matapelajaran.html', context)

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class buat_matapelajaran(View):
    def post(self, request):
        matapelajaran_form = MatapelajaranForm(request.POST)
        try:
            if matapelajaran_form.is_valid():
                mapel = MataPelajaran.objects.create(**form_value(matapelajaran_form))
                messages.success(request, f'{mapel.nama} berhasil dibuat')
        except Exception as e:
            messages.error(request, 'Terjadi kesalahan saat mencoba membuat Matapelajaran')
        finally:
            return redirect('list-matapelajaran')

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class detail_matapelajaran(View):
    def get(self, request, matapelajaran):
        try:
            matapelajaran = MataPelajaran.objects.get(pk=matapelajaran)
        except ObjectDoesNotExist:
            raise Http404
        tp = active_tp()
        request.session['page'] = f'Detail {matapelajaran.nama}'
        initial = get_initial(matapelajaran)
        kkm, created = KKM.objects.get_or_create(matapelajaran=matapelajaran, tahun_pelajaran=tp)
        initial['pengetahuan'] = kkm.pengetahuan
        initial['keterampilan'] = kkm.keterampilan
        context = {
            'matapelajaran': matapelajaran,
            'kkm': kkm,
            'mapelkkm_form': EditMatapelajaranForm(initial=initial),
            'list_kelas': matapelajaran.kelas.filter(tahun_pelajaran=tp),
        }
        return render(request, 'pages/matapelajaran/detail-matapelajaran.html', context)
    
    def post(self, request, matapelajaran):
        matapelajaran_form = EditMatapelajaranForm(request.POST)
        try:
            if matapelajaran_form.is_valid():
                data = form_value(matapelajaran_form)
                pengetahuan = data['pengetahuan']
                keterampilan = data['keterampilan']
                del data['pengetahuan']
                del data['keterampilan']
                MataPelajaran.objects.filter(pk=matapelajaran).update(**data)
                kkm = KKM.objects.get(matapelajaran__pk=matapelajaran, tahun_pelajaran=active_tp())
                kkm.pengetahuan = pengetahuan
                kkm.keterampilan = keterampilan
                kkm.save()
                
                messages.success(request, f'Data Matapelajaran {kkm.matapelajaran.nama} berhasil diubah')
        except Exception as e:
            messages.error(request, e)
        finally:
            return redirect('detail-matapelajaran', matapelajaran=matapelajaran)

@method_decorator(staftu_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class hapus_matapelajaran(View):
    def get(self, request, matapelajaran):
        try:
            mapel = MataPelajaran.objects.get(pk=matapelajaran)
            nama_mapel = mapel.nama
            mapel.delete()
            messages.success(request, f'{nama_mapel} telah berhasil dihapus')
        except Exception as e:
            messages.error(request, 'Terjadi kesalahan saat mencoba menghapus Matapelajaran')
        finally:
            return redirect('list-matapelajaran')

@method_decorator(login_required, name='dispatch')
@method_decorator(validdirs_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class rapor_view(View):
    def get(self, request, nis, action, **kwargs):
        try:
            siswa = Siswa.objects.get(nis=nis)
        except ObjectDoesNotExist:
            raise Http404
        sekolah = Sekolah.objects.get()
        semester = active_semester()
        context = generate_rapor_context(sekolah, semester, siswa)
        generate_pdf(siswa, kwargs['pdf_dir'], context)
        rapor = Rapor.objects.get(siswa=siswa, semester=semester)
        with open(rapor.rapor, 'rb') as result:            
            response = HttpResponse(result, content_type='application/pdf;')
            if action == 'unduh':
                response['Content-Disposition'] = f'attachment; filename={siswa.nama}.pdf'
                response['Content-Transfer-Encoding'] = 'binary'
            elif action == 'pratinjau':
                response['Content-Disposition'] = f'inline; filename={siswa.nama}.pdf'
                response['Content-Transfer-Encoding'] = 'binary'
            else:
                return redirect('dashboard')

            return response

@method_decorator(login_required, name='dispatch')
@method_decorator(validdirs_required, name='dispatch')
@method_decorator(activesemester_required, name='dispatch')
class bundle_rapor_view(View):
    def get(self, request, kelas, **kwargs):
        try:
            sekolah = Sekolah.objects.get()
            semester = active_semester()
            tp = active_tp()
            kelas = Kelas.objects.get(nama=kelas, tahun_pelajaran=tp)
            siswa = Siswa.objects.filter(kelas=kelas)
        except ObjectDoesNotExist:
            raise Http404

        # for siswa in siswa:
        #     context = generate_rapor_context(sekolah, semester, siswa)
        #     generate_pdf(siswa, kwargs['pdf_dir'], context)

        bundle_dir = f'{settings.MEDIA_ROOT}/rapor/{kelas.tahun_pelajaran.mulai} - {kelas.tahun_pelajaran.akhir} {semester.semester}/bundel/{kelas.jurusan}'
        if not os.path.isdir(bundle_dir):
            os.makedirs(bundle_dir)
        
        shutil.make_archive(f'{bundle_dir}/Rapor-{kelas.nama}', 'zip', kwargs['pdf_dir'])
        zip_file = open(f'{bundle_dir}/Rapor-{kelas.nama}.zip', 'rb')
        response = FileResponse(zip_file, content_type='application/force-download')
        response['Content-Disposition'] = f'attachment; filename=Rapor-{kelas.nama}.zip'

        return response
        