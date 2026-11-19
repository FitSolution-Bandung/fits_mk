# Rencana Pengembangan Modul MK dan RAB (Pola SNI/AHSP) — Odoo 19

Tanggal: 2026.11.19 · Penyusun: Claude bersama Pak Andhi · Status: **draf rencana, belum dikerjakan**
Repo: `FitSolution-Bandung/fits_mk`, branch `19.0` · Lokal: WSL `/home/andhi/fits_mk` (Docker Odoo 19, port 8029)
Dasar kondisi: `2026.11.19 Kondisi Repo fits_mk dan Rencana Penyempurnaan Modul MK.md`

---

## 1. Tujuan

Satu paket add-on Odoo 19 untuk dua peran Fujicon di proyek konstruksi.

1. **Perencana:** menyusun **RAB / Engineer's Estimate (EE/HPS)** mengikuti pola **SNI dan AHSP PUPR**. Alurnya: harga satuan dasar, lalu analisa harga satuan pekerjaan, lalu volume, lalu RAB dan rekapitulasi.
2. **MK (pengawas):** mengendalikan pelaksanaan kontraktor. Cakupannya kurva S rencana vs realisasi, laporan harian, mingguan, dan bulanan, persetujuan dokumen teknis, opname dan MC, serta berita acara.

Benang merahnya: **RAB menjadi sumber bobot pekerjaan.** Bobot itu menghasilkan kurva S rencana. Realisasi lapangan dari laporan harian dan opname mengisi kurva S aktual. Kurva S aktual menjadi dasar laporan MK dan termin pembayaran.

```
HSD (upah/bahan/alat per wilayah & periode)
   └─► AHSP (koefisien × HSD + biaya umum & keuntungan)
          └─► RAB (volume BoQ × HSP, per divisi) + SMKK + PPN ─► EE/HPS
                 └─► Bobot item ─► Jadwal ─► Kurva S rencana
                                              ▲
     Laporan harian ─► progres item ─► Kurva S realisasi ─► Laporan MK, deviasi, opname/MC, termin
```

## 2. Prinsip (mengikuti pola TATEKAN)

- **Odoo 19 Community saja.** `depends` hanya modul CE. Tidak bergantung pada `sale`/`purchase` di modul inti. Fujicon menjual jasa konsultansi, bukan konstruksi, jadi kaitan ke SO/RFQ dipindah ke modul jembatan opsional.
- **Generik.** Tidak ada nama klien, tarif, atau wilayah yang di-hard-code. Semua lewat data master dan konfigurasi.
- **Dapat diaudit.** Setiap angka RAB bisa ditelusuri sampai ke koefisien dan HSD sumbernya. Revisi tersimpan sebagai versi, tidak menimpa versi lama.
- **Definition of Done per modul:**
  1. Install dan uninstall bersih di database kosong.
  2. Tes `--test-enable` lolos.
  3. Label Indonesia lengkap (`i18n/id.po`).
  4. Data demo tersedia.
  5. Record rule per proyek dan per perusahaan berlaku.
  6. Semua menu dicek di browser.
- **Pengembangan lokal + ngrok.** Production Fujicon tidak disentuh. Push hanya setelah ACC.

## 3. Struktur modul yang diusulkan

Saat ini semuanya ada di satu modul `fits_management_construction`. Usulannya dipecah supaya RAB bisa dipakai tanpa modul MK, dan sebaliknya.

| Modul | Isi | Bergantung pada |
|---|---|---|
| `*_construction_base` | Master bersama: wilayah/lokasi, satuan, divisi/WBS, peran proyek (Owner, Perencana, MK, Kontraktor), field kontrak proyek terstruktur, grup akses | `project`, `uom`, `mail` |
| `*_construction_rab` | **Estimasi biaya pola SNI/AHSP**: HSD, AHSP, pustaka AHSP, volume/back-up, RAB, SMKK, rekapitulasi, versi/revisi, ekspor Excel/PDF | base |
| `*_construction_schedule` | Jadwal pekerjaan dari RAB, bobot otomatis, kurva S rencana A/B | rab |
| `*_construction_mk` | Laporan harian, mingguan, dan bulanan, kurva S realisasi, opname/MC, persetujuan dokumen, rapat, BA, CCO | schedule |
| `*_construction_hse` | Analisis risiko, K3/HSE, izin kerja, stakeholder | base |
| `*_construction_sale_purchase` (opsional) | Jembatan ke SO/RFQ untuk pengguna kontraktor | rab, `sale`, `purchase` |

Prefix (`fits_` atau `fujicon_`) dan cara migrasi dari modul lama ditentukan di Keputusan K1.

## 4. Fitur RAB pola SNI/AHSP (rinci)

### 4.1 Rujukan

- **Seri SNI Analisa Harga Satuan Pekerjaan** (bidang Cipta Karya, mis. pekerjaan tanah, pondasi, beton, dinding, plesteran). Ini dasar historis koefisien.
- **Permen PUPR No. 8 Tahun 2023** tentang Pedoman Penyusunan Perkiraan Biaya Pekerjaan Konstruksi Bidang PUPR. Pemutakhiran AHSP dilakukan lewat **SE Dirjen Bina Konstruksi**. Materi publik terakhir yang saya temukan menyebut SE No. 30 Tahun 2025. *Status yang berlaku di 2026 dan batas persentase biaya umum & keuntungan wajib diverifikasi dari JDIH PUPR sebelum dipakai untuk HPS.*
- **Biaya Penerapan SMKK** dihitung sebagai item tersendiri dalam perkiraan biaya, mengikuti lampiran pedoman PUPR.

Aturan dan koefisien **tidak di-hard-code di Python**. Semuanya data (pustaka AHSP + parameter), sehingga pemutakhiran SE cukup dengan impor data baru.

### 4.2 Data master

| Objek | Isi utama |
|---|---|
| **Wilayah & periode HSD** | Provinsi/kab-kota, periode (mis. 2026-S1), sumber (SK bupati, survei, jurnal harga), status draft/berlaku |
| **HSD Upah** | Pekerja, tukang (batu/kayu/besi/cat/listrik/pipa), kepala tukang, mandor, operator. Satuan OH, ditambah tarif jam bila perlu |
| **HSD Bahan** | Bahan dengan satuan, harga franco lokasi, sumber harga, dan tanggal |
| **HSD Alat** | Sewa per jam, atau **analisa biaya alat**: biaya pasti (penyusutan, bunga, asuransi) + biaya operasi (BBM, pelumas, operator, perawatan) |
| **Pustaka AHSP** | Item standar dengan kode, uraian, satuan, bidang (CK/SDA/BM), rujukan SNI/SE, versi. Komponen A tenaga, B bahan, C alat, masing-masing dengan koefisien. Item pustaka read-only; untuk diubah harus disalin menjadi AHSP proyek |

### 4.3 Perhitungan AHSP

- Per komponen: **koefisien × HSD** sesuai wilayah dan periode RAB.
- **D = A + B + C.** **E = biaya umum & keuntungan = p% × D**, dengan p dikonfigurasi dan diberi batas maksimum sesuai pedoman yang berlaku.
- **F = HSP = D + E.** Pembulatan HSP bisa dikonfigurasi.
- AHSP yang memakai AHSP lain sebagai komponen (mis. adukan) dihitung berjenjang, dengan pengecekan siklus.

### 4.4 Volume (BoQ) dan back-up

- Item volume per divisi/sub-divisi. Isinya rumus sederhana (P × L × T × jumlah), referensi gambar, dan lampiran.
- Impor volume dari Excel. Templatnya disediakan modul.

### 4.5 RAB

- Struktur hierarki: Divisi → Sub-divisi → Item. Contoh divisi: Persiapan, Tanah, Struktur, Arsitektur, MEP.
- Jumlah per item = volume × HSP.
- **Item SMKK** wajib tersedia sebagai divisi/item tersendiri, dihitung dari komponennya.
- **Rekapitulasi:** jumlah per divisi, total, **PPN** (memakai `account.tax`, tidak di-hard-code), total + PPN, **pembulatan** (aturan dapat dikonfigurasi), dan **terbilang**.
- **Versi & revisi:** EE/HPS v1, v2, ..., dan perbandingan antarversi. Setelah ditetapkan, RAB dikunci. Revisi selalu menjadi versi baru.
- **Keluaran:** Rekapitulasi, RAB rinci, AHSP terpakai, Daftar HSD, Back-up volume. Tersedia dalam **Excel** (format yang lazim dipakai PUPR) dan **PDF** berkop.
- Hubungan ke `project.project` dan analytic account `[kode]`.

### 4.6 Kondisi saat ini vs target

Model yang sudah ada (`unit.price.analysis`, `ahs.*`, `unit.price.data`, `price.*`, `boq`, `budget.plan`, `rab.mk`) sudah mencakup sebagian pola, yaitu koefisien × harga per lokasi. Yang belum ada:

- Peran upah standar.
- Biaya umum & keuntungan per AHSP. Saat ini profit diterapkan di level RAB dengan default 1%.
- Analisa alat.
- Pustaka AHSP dan versinya.
- SMKK.
- PPN di level rekap. Saat ini pajak dihitung per baris.
- Hierarki divisi.
- Versi RAB.
- Ekspor Excel.

Keputusan K2: model lama dirombak, atau dibuat model baru lalu data lama dimigrasi.

### 4.7 Riset data terkini dengan AI → Excel → impor

Tujuannya: data yang cepat basi bisa diperbarui dengan bantuan AI generatif, tanpa mengetik ulang, dan tetap bisa diaudit. Contohnya HSD upah, bahan, dan sewa alat per wilayah, harga material terbaru, AHSP/SE terbaru, dan regulasi.

Alurnya:

```
Template Prompt Riset ──► Prompt siap pakai ──► AI (Claude/ChatGPT/Gemini, atau API)
   (jenis data, wilayah,      (berisi daftar item,         │
    periode, daftar item)      format kolom, aturan)        ▼
                                                    File .xlsx sesuai template
                                                            │
             ┌──────────────────────────────────────────────┤
             ▼                                              ▼
   Impor standar Odoo (base_import)            Impor dibantu AI (file bebas format
   ke staging, pakai template kolom            → AI memetakan kolom & satuan)
             └───────────────┬──────────────────────────────┘
                             ▼
            Batch Impor (staging) ─► Validasi otomatis ─► Review & Setujui ─► HSD/AHSP versi baru
```

**a. Template Prompt Riset** (model data, bisa diubah tanpa kode)

- Jenis data: HSD upah / HSD bahan / sewa alat / pustaka AHSP / regulasi.
- Parameter: wilayah (provinsi/kab-kota), periode, bidang, mata uang.
- Tombol **Buat Prompt** menyusun teks prompt lengkap, berisi:
  - Daftar item yang dicari, diambil dari master (kode, nama, satuan) supaya hasilnya cocok saat diimpor.
  - **Spesifikasi keluaran yang ketat:** nama kolom persis sama dengan template impor, satuan baku, format angka, satu baris per item.
  - **Aturan kejujuran data:** setiap baris wajib punya sumber (URL/nama dokumen) dan tanggal data. Kalau data tidak ditemukan, isi kosong dengan keterangan "tidak ditemukan", jangan diperkirakan. Ada juga kolom tingkat keyakinan.
  - Permintaan agar hasil diberikan sebagai file .xlsx, atau tabel yang bisa langsung disalin ke Excel.
- Tombol **Salin Prompt** dan **Unduh Template Excel** yang kolomnya sudah cocok dengan model staging.
- Setiap prompt yang dibuat tersimpan (siapa, kapan, parameter) untuk jejak audit.

**b. Impor ke sistem, dengan dua jalur**

1. **Impor standar Odoo** (`base_import`, sudah ada di CE dan mendukung .xlsx). Data masuk ke model staging *Batch Impor Riset*, memakai template kolom yang sama, sehingga pemetaan kolom tersimpan dan bisa dipakai ulang.
2. **Impor dibantu AI** (opsional). Pengguna mengunggah file hasil riset dengan format bebas (xlsx/csv/pdf tabel). AI lalu memetakan kolom ke field, menormalkan satuan (mis. "sak 50 kg" → kg), dan mencocokkan nama item ke master. Hasilnya tetap masuk ke **staging**, tidak langsung ke master.

**c. Validasi & persetujuan** (wajib untuk kedua jalur)

- Pengecekan otomatis:
  - Item cocok dengan master.
  - Satuan sesuai.
  - Sumber dan tanggal terisi.
  - Angka positif.
  - **Pencilan:** selisih terhadap periode sebelumnya di atas ambang (mis. ±25%) diberi tanda.
- Review per baris: terima, ubah, atau tolak. Status batch: Draft → Divalidasi → Disetujui → Diterapkan.
- Saat diterapkan, sistem membuat **HSD/AHSP versi periode baru**. Data lama tidak ditimpa. Sumber, tanggal, model AI, dan prompt yang dipakai ikut tersimpan di setiap baris.

**d. Mode integrasi AI**

- **Mode manual (default, tanpa biaya integrasi):** prompt disalin ke AI pilihan pengguna, lalu file hasilnya diimpor. Tidak ada API key di sistem.
- **Mode API (modul jembatan opsional `*_construction_ai`):** prompt dikirim langsung dari Odoo ke penyedia AI yang dipilih, dan hasilnya kembali sebagai data terstruktur ke staging. **API key hanya disimpan di Pengaturan (`ir.config_parameter`), tidak pernah di kode.** Ini pelajaran dari kebocoran kunci OpenAI di repo lama. Ada juga batas pemakaian dan log biaya.
- **Prinsip keamanan:** hasil AI diperlakukan sebagai *data*, bukan perintah, dan selalu lewat staging + persetujuan manusia sebelum memengaruhi RAB.

**e. Kegunaan lain di luar RAB:** pola yang sama (prompt → xlsx → staging → setujui) dapat dipakai untuk data MK. Contohnya daftar regulasi/SNI teknis terbaru, data cuaca historis lokasi proyek, dan harga material untuk evaluasi CCO.

## 4A. Multi-proyek dan multi-perusahaan

**Kondisi sekarang (dicek di kode 2026.11.19): baru sebagian.**

- ✅ Banyak proyek bisa disimpan sekaligus. 21 file model sudah punya kolom Proyek (`project.project`), antara lain RAB, BoQ, laporan harian, kurva S, NCR, material approval, shop drawing, perubahan lapangan, dan serah terima.
- ❌ **Belum ada record rule.** Setiap pengguna MK melihat **semua** proyek. Pengawas proyek A bisa membuka dokumen proyek B.
- ❌ **Belum multi-perusahaan.** Tidak ada `company_id` di model MK, jadi FPP/FSE/klien belum bisa dipisah dalam satu database.
- ❌ **11 file model tidak terhubung ke proyek:** analisis risiko, HSE, izin pelaksanaan, izin pekerjaan, izin lembur, form pengawasan, stakeholder, absensi template, serta AHSP dan data harga. AHSP dan data harga memang sengaja lintas proyek, tetapi dokumen lapangan harus per proyek.
- ❌ Belum ada **tim proyek per peran** (Owner, Perencana, MK, Kontraktor) dan belum ada tampilan berpusat pada proyek.

**Target (masuk Tahap 1):**

| Hal | Rancangan |
|---|---|
| Proyek wajib | Semua dokumen lapangan wajib punya Proyek. Proyek terisi otomatis dari konteks |
| Tim proyek | Model *Anggota Proyek*: pengguna/partner + peran (Owner, Perencana, MK, Kontraktor) + masa tugas |
| Record rule | Pengguna hanya melihat proyek tempat ia menjadi anggota. Manager MK melihat semua proyek di perusahaannya. Owner/Kontraktor (portal) hanya melihat proyeknya dan dokumen yang dibagikan |
| Multi-perusahaan | `company_id` di semua model transaksi + rule perusahaan standar Odoo. Pustaka AHSP/HSD bisa dipakai bersama atau per perusahaan |
| Tampilan | Smart button di form proyek (RAB, kurva S, laporan, dokumen, NCR terbuka), dashboard portofolio semua proyek (progres, deviasi, dokumen menunggu persetujuan) |
| Penomoran | Nomor dokumen bisa memakai kode proyek, mis. `[KODE]/LH/2026/001` |
| Tes | Tes otomatis: pengguna proyek A tidak bisa membaca atau mengubah dokumen proyek B |

## 5. Fitur MK (rinci)

| Kelompok | Fitur |
|---|---|
| Kurva S & progres | Bobot dari RAB, jadwal per item (rencana A/B), realisasi dari laporan harian/opname, deviasi + **peringatan ambang** (mis. terlambat > 5% → kritis, sesuai kebiasaan SCM/show cause meeting) |
| Laporan | Harian (sudah ada), **mingguan & bulanan otomatis** dari harian: progres, cuaca, tenaga, alat, material, kendala, foto. Cetak berkop dan ekspor |
| Opname & MC | Opname bersama per item. MC-0 (penyesuaian volume awal) dan MC-100. Dasar **sertifikat pembayaran/termin** |
| Persetujuan dokumen | Alur **Kontraktor → MK → Owner** dengan status, catatan, dan riwayat untuk: material approval, shop drawing, RFI, NCR, metode kerja, perubahan lapangan |
| Perubahan kontrak | **CCO/addendum** dalam bentuk versi RAB kontrak baru, dengan selisih tambah/kurang |
| Rapat & BA | Notulen rapat koordinasi dengan tindak lanjut, surat teguran, BA PHO/FHO, BA lapangan |
| Integrasi Fujicon | Analytic account `[kode]`, timesheet personel MK per proyek, tim MK per proyek |
| Portal & mobile | Portal Owner/Kontraktor untuk melihat dan mengajukan dokumen. Laporan harian dari ponsel (memakai ulang `mk-mobile` atau portal responsif) |

## 6. Tahapan

| Tahap | Lingkup | Hasil |
|---|---|---|
| **0** ✅ | Keamanan + port 17→19, tes dasar, Docker lokal + ngrok | Branch `19.0` (sudah di-push) |
| **1** | Fondasi: pecah modul, branding & lisensi, `id.po`, data demo, **multi-proyek & multi-perusahaan (§4A)**: tim proyek, record rule, `company_id`, dashboard portofolio. Keluarkan SO/RFQ ke modul jembatan | Struktur modul baru, akses per proyek teruji |
| **2** | **RAB inti pola SNI/AHSP**: HSD per wilayah/periode, AHSP (A+B+C, biaya umum & keuntungan), volume, RAB hierarki, SMKK, rekap + PPN + pembulatan + terbilang, cetak PDF | EE/HPS bisa dibuat dari nol sampai cetak |
| **3** | RAB lanjutan: pustaka AHSP + impor data SE terbaru, analisa alat, versi/revisi + perbandingan, ekspor/impor Excel | RAB siap dipakai di proyek nyata |
| **3A** | **Riset data AI → Excel → impor (§4.7)**: template prompt, template Excel, staging + validasi + persetujuan, impor standar Odoo. Mode API sebagai modul opsional | HSD periode baru bisa diperbarui dari hasil riset AI dengan jejak sumber |
| **4** | Jadwal & kurva S rencana dari RAB (bobot otomatis) | Kurva S terhubung ke RAB |
| **5** | Laporan progres MK (mingguan/bulanan), realisasi, peringatan deviasi | Laporan MK otomatis |
| **6** | Alur persetujuan dokumen teknis + RFI | Kontraktor → MK → Owner |
| **7** | Opname, MC-0/100, CCO/addendum, termin; rapat & BA | Siklus kontrak lengkap |
| **8** | Integrasi Fujicon (analytic, timesheet) + portal/mobile | Dipakai tim MK di lapangan |

Setiap tahap: kerja di branch fitur dari `19.0`, uji lokal + ngrok, lalu PR setelah ACC.

## 7. Keputusan yang dibutuhkan dari Pak Andhi

| # | Keputusan | Pilihan | Usulan |
|---|---|---|---|
| K1 | Nama/prefix modul dan pemecahan | Tetap satu modul `fits_management_construction` / dipecah dengan prefix `fits_construction_*` / `fujicon_construction_*` | Dipecah. Prefix mengikuti TATEKAN (`fujicon_*`) bila ini produk Fujicon |
| K2 | Model RAB lama | Dirombak di tempat / model baru + migrasi data lama | Model baru. Model lama dipensiunkan setelah migrasi |
| K3 | Lisensi | AGPL-3 (sekarang) / OPL-1 (seperti TATEKAN, bisa dijual) | OPL-1 bila akan dijual di Odoo Apps |
| K4 | **Di mana dipakai tim Fujicon** | Odoo Fujicon production masih v12, sedangkan modul ini v19. Pilihan: (a) instance Odoo 19 terpisah khusus MK/RAB, (b) menunggu migrasi Odoo Fujicon ke 19, (c) produk untuk klien dulu | Perlu arahan Bapak. Ini menentukan Tahap 8 |
| K5 | Sumber data pustaka AHSP | Ketik/impor dari lampiran Permen PUPR + SE yang berlaku / dataset pihak ketiga | Dari dokumen resmi PUPR (peraturan, bebas dipakai). Dataset pihak ketiga hanya sebagai pembanding |
| K6 | Bidang AHSP yang didahulukan | Cipta Karya (gedung) / SDA / Bina Marga | Cipta Karya, sesuai mayoritas proyek gedung Fujicon (perlu konfirmasi) |
| K7 | Format laporan RAB acuan | Format standar PUPR / format internal Fujicon yang sudah dipakai | Kirimkan contoh RAB/EE Fujicon terakhir sebagai acuan |
| K8 | Repo publik | Ubah jadi private sekarang / tetap publik untuk Odoo Apps | Private, sesudah kunci OpenAI dicabut |
| K9 | Mode AI untuk riset data | Manual saja (salin prompt, unggah xlsx) / manual + mode API | Mulai manual. Mode API menyusul setelah pola datanya stabil |
| K10 | Penyedia AI untuk mode API & impor dibantu AI | Claude / OpenAI / Gemini / bisa dipilih di Pengaturan | Bisa dipilih di Pengaturan, dengan satu penyedia default |
| K11 | Visibilitas antarproyek | Pengguna hanya melihat proyeknya / semua staf MK melihat semua proyek | Hanya proyeknya. Manager MK dan Direksi melihat semua |

## 8. Risiko & catatan

- **Regulasi berubah.** AHSP dimutakhirkan lewat SE. Mitigasinya: koefisien dan parameter disimpan sebagai data yang berversi, bukan kode.
- **Hak cipta SNI.** Dokumen SNI dilindungi BSN, jadi teks SNI tidak disalin. Pustaka diambil dari lampiran peraturan PUPR, dan rujukan SNI dicatat sebagai kode/nomor saja.
- **Versi Odoo.** Lihat K4. Tanpa keputusan ini, integrasi ke data proyek Fujicon di v12 belum bisa dilakukan langsung.
- **Kunci OpenAI lama** masih ada di riwayat repo publik dan harus dicabut di dashboard OpenAI.
