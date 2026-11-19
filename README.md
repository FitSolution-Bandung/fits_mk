# fits_mk — Construction Management Indonesia (Odoo 19)

Add-on Odoo untuk **Manajemen Konstruksi (MK)**: perencanaan biaya, pengendalian progres,
laporan harian, dan dokumen pengawasan lapangan. Pemilik: PT. Fujicon Priangan Perdana.

| Branch | Odoo | Status |
|---|---|---|
| `19.0` | 19 Community | Hasil port dari 17.0. Install dan tes lolos di database kosong |
| `17.0` / `main` | 17 | Versi yang diterbitkan di Odoo Apps (Jul 2025) |

## Isi modul `fits_management_construction`

- **Perencanaan biaya:** RAB, BoQ, Analisa Harga Satuan (AHS), data harga satuan.
- **Progres:** bobot task dari biaya, progres harian per task, **Kurva S** (rencana A/B vs aktual, deviasi) dengan grafik.
- **Laporan harian:** WBS, material, alat, tenaga kerja, cuaca, catatan, foto/PDF monitoring.
- **Formulir lapangan:** izin kerja, izin pengecoran, izin pelaksanaan, izin lembur, permintaan kerja,
  pengajuan barang, persetujuan material, persetujuan gambar kerja, perubahan lapangan, koreksi pekerjaan,
  inspeksi kelayakan, NCR, defect list, form pengawasan, monitoring cuaca, serah terima akhir, surat masuk/keluar.
- **Risiko dan K3:** analisis risiko dan mitigasi, HSE, analisis stakeholder.
- **Grup akses:** Owner (baca) → User → Manager.

## Lingkungan lokal (WSL + Docker)

```bash
cp .env.example .env                       # isi POSTGRES_PASSWORD
cp config/odoo.conf.example config/odoo.conf   # isi admin_passwd
docker compose up -d                       # Odoo 19 di http://localhost:8029
```

Repo ini di-mount ke `/mnt/extra-addons`. Database demo: `mk_demo`. Port 8029/8030 dipakai agar tidak
bentrok dengan TATEKAN (8019) dan Odoo 16 (8016).

### Install dan tes

```bash
docker compose stop odoo
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d mk_test --db-filter='^mk_test$' \
  -i fits_management_construction --test-enable --test-tags /fits_management_construction \
  --stop-after-init
docker compose up -d odoo
```

Tes (`fits_management_construction/tests/`):
- `test_views`: semua window action bisa dibuka (view terkompilasi, model terbaca); setiap laporan punya template.
- `test_curve_s`: bobot task dari biaya, pembagian rencana per hari, kurva S kumulatif, deviasi, progres proyek.
- `test_security`: endpoint yang dulu publik kini wajib login; tidak ada API key ter-hard-code.

## Catatan port 17 → 19

- `<tree>` → `<list>`, chatter → `<chatter/>`, `view_mode` tree → list, `type='json'` → `jsonrpc`.
- Grup memakai `res.groups.privilege` (Odoo 19). Admin otomatis masuk grup Manager.
- `uom.category` hilang di Odoo 19: menu Satuan memakai menu UoM standar.
- `web_editor` → `html_editor`. `pdf2image` jadi opsional (pratinjau PDF laporan harian).
- Kurva S memakai `_read_group` (tidak lagi mengurai teks tanggal yang bergantung locale).
- Perbaikan bug yang ikut ditemukan: field `work_detail_ids` ke model yang tidak pernah ada,
  bobot rencana memakai bobot task pertama untuk semua task, `_sql_constraints` yang merujuk kolom
  tidak ada, kode provinsi Papua Pegunungan.
- Dilepas: override kop laporan standar Odoo (mengubah kop **semua** laporan perusahaan) dan
  override kanban kontak global.
- Keamanan: API key dihapus, endpoint wajib login, `auto_install` dimatikan.

## Lisensi

AGPL-3 (lihat manifest). Keputusan lisensi untuk versi 19 (AGPL vs OPL-1 seperti TATEKAN) belum ditetapkan.
