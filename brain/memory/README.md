# devstack memory

Memori koreksi untuk agent. Model tidak benar-benar belajar (bobotnya tidak berubah), jadi devstack menyimpan koreksi Anda sebagai pelajaran, memanggilnya kembali saat relevan, dan mengubah kesalahan yang berulang menjadi pemeriksaan otomatis.

## Siklus belajar

1. **Koreksi**: Anda bilang "salah", menolak hasil, atau me-revert. Agent menyimpan pelajaran: satu aturan, alasan, contoh salah dan benar, serta file tempat aturan itu berlaku.
2. **Ingat**: di awal setiap tugas, agent memanggil pelajaran yang relevan dengan area dan file yang akan disentuh, dalam batas token (default sekitar 800).
3. **Terulang**: kalau kesalahan yang sama muncul lagi, hitungannya naik. Pelajaran yang mirip otomatis digabung.
4. **Ditegakkan**: pelajaran yang terulang dua kali dan bisa dideteksi dengan pola diubah menjadi guard. `audit.py` lalu memblokirnya, tanpa bergantung pada kepatuhan model.
5. **Dibagikan**: pelajaran proyek ada di `.ai/lessons.json` dan ikut ter-commit, jadi seluruh tim mendapatkannya. Pelajaran yang berlaku di semua proyek dinaikkan ke `~/.omp/agent/lessons.json`.
6. **Dirapikan**: `compact` menggabungkan duplikat dan mengarsipkan pelajaran lama yang tidak pernah terpakai.

## Perintah

```bash
L="lessons"
$L add --area backend --rule="Response API memakai tanggal ISO 8601" --why="Aplikasi mobile memparse ISO" --wrong="->format('d/m/Y')" --right="->toIso8601String()" --scope "app/Http/Resources/*.php"
$L recall --area backend --files app/Http/Controllers/OrderController.php
$L hit L-0001
$L guard L-0001 --regex="->format\(\s*['\"]d/m/Y['\"]\s*\)"
$L promote L-0001
$L compact
$L list
```

Pakai bentuk `--flag="nilai"` supaya nilai yang diawali `-` tetap terbaca.

Area: `ui`, `backend`, `security`, `data`, `process`, `style`, `testing`.

## Berkas

| Berkas | Isi |
| --- | --- |
| `.ai/lessons.json` | Sumber data pelajaran proyek |
| `.ai/LESSONS.md` | Ringkasan yang bisa dibaca manusia, dibuat otomatis |
| `.ai/rules/lessons.yml` | Guard yang ditegakkan `audit.py` |
| `~/.omp/agent/lessons.json` | Pelajaran global (ubah lewat `DEVSTACK_LESSONS_GLOBAL`) |

Pelajaran yang mengandung sesuatu mirip secret ditolak.
