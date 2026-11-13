# devstack Taste Pack v4

Otak desain yang dibawa ke agent: `BRAIN.md` (prinsip dan resep per jenis layar), primitif tata letak, 6 preset, komponen aplikasi, pola form, `taste init`, review vision opsional, dan linter token. Agent bebas membangun fitur apa pun yang dibutuhkan proyek; kualitasnya dijaga prinsip dan pemeriksaan, bukan katalog tertutup.

## Alur per proyek

1. **Lead menjalankan `taste init` sekali**:
   ```bash
   taste init
   ```
   Delapan pertanyaan pilihan: nama, jenis produk, pengguna, kesan, tema, kepadatan, sudut, warna merek.
2. **Buka `.taste/compare.html`** dan bandingkan 3 kandidat (layar aplikasi dan landing).
3. **Kunci pilihan**:
   ```bash
   taste pick dashboard-pro
   ```
   Hasilnya `DESIGN.md`, `.taste/`, dan `public/assets/taste/` (CSS, JS, font). Commit semuanya.
4. **Anggota tim** cukup meminta agent membuat layar. Semua hasil otomatis memakai arah yang sudah dikunci.

## Vision: opsional, tapi disarankan

Model yang bisa melihat gambar membuat review tampilan jauh lebih tajam. Tanpa vision, devstack tetap bekerja dengan cek otomatis (kontras, overflow, target sentuh) dan screenshot untuk dicek manusia.

```bash
taste vision --base-url http://localhost:20128/v1 --model code-vision --api-key-env NINEROUTER_API_KEY
taste review http://localhost:8100/pegawai.html
```

`taste review` membuktikan model bisa melihat dengan mengirim gambar kecil berwarna merah. Model teks saja otomatis dilewati dan dicatat di cache, jadi tidak membuang token.

## Isi

| Folder | Isi |
| --- | --- |
| `presets/` | 6 arah visual: `bold-tech`, `editorial-night`, `clean-corporate`, `civic`, `warm-umkm`, `dashboard-pro` |
| `core/` | `base.css` dan `motion.js` (landing), `app.css` dan `app.js` (komponen aplikasi) |
| `screens/` | Layar referensi aplikasi: galeri komponen, form bersection, wizard |
| `blocks/` | 13 template blok HTML |
| `fonts/` | Font self-hosted (woff2) beserta lisensi OFL, tanpa Google Fonts |
| `content/` | Data contoh landing dan layar aplikasi dalam JSON |
| `tools/` | Dipanggil lewat perintah `taste`: init, pick, vision, build, lint, contrast, check, review |
| `dist/` | Contoh hasil build: `app-<preset>/` dan `landing-<preset>/` untuk keenam preset |
| `BRAIN.md` | Cara berpikir desain: prinsip, primitif, resep layar (kiosk, display TV, panel petugas, daftar, detail, dashboard, laporan, login) |
| `TASTE.md` | Cara memakai pack: init, komponen, pola form, pemeriksaan |

## Pakai

```bash
taste build content/devstack.bold-tech.json dist/devstack-bold-tech.html
taste contrast
taste check http://localhost:8100/devstack-bold-tech.html --shots .ai/screens
```

`assemble.py` dan `taste contrast` hanya butuh Python 3. `taste check` butuh Playwright dan Chromium.

## Interaksi

Navigasi lengket dengan blur, menu ponsel, reveal saat scroll, efek ketik di terminal, sorotan kursor di kartu fitur, tombol magnetik, angka count-up, tab dengan keyboard, toggle harga bulanan dan tahunan, serta FAQ akordeon. Semua menghormati `prefers-reduced-motion` dan tetap terbaca tanpa JavaScript.

## Komponen aplikasi

Select dengan pencarian dan grup, multiselect dengan chip, datepicker berbahasa Indonesia (bisa diketik), upload dengan seret dan lepas serta validasi ukuran dan jenis, switch, kartu pilihan, segmented, penghitung karakter, toast, dan shell aplikasi (sidebar, topbar, breadcrumb). Semua dibangun di atas elemen HTML asli, sehingga form tetap terkirim normal ke Laravel atau CI3.

Pola form: form bersection dengan action bar menempel, draf otomatis yang bisa dipulihkan, tombol "Simpan dan tambah lagi" yang mempertahankan isian berulang, dan wizard bertahap dengan halaman tinjau.

Build layar aplikasi dengan preset lain:

```bash
taste build content/app-form-sectioned.json dist/app-bold-tech/form-sectioned.html --preset bold-tech
```

## Batasan v4

- Output berupa HTML statis. Untuk Blade atau CI3, potong bagian yang dibutuhkan ke view dan muat CSS serta JS di layout.
- Primitif tabel, stat, list, empty, dan skeleton sudah ada. Belum ada: perilaku tabel (sort, filter, paginasi via JS) dan komponen grafik.
- Testimoni, angka dampak, dan harga di contoh adalah ilustrasi dan diberi label "Contoh".
