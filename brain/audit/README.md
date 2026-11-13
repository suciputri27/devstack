# devstack audit

Audit keamanan bergaya serangan untuk aplikasi PHP (Laravel, CodeIgniter 3), Node.js (Express, NestJS, Next.js, Prisma, MongoDB), dan JavaScript frontend. Hanya untuk kode dan lingkungan dev atau staging, tidak pernah production.

## Dua fase

| Fase | Isi | Biaya token |
| --- | --- | --- |
| 1, alat pasti | Semgrep dengan aturan khusus Laravel dan CI3, scan secret, `composer audit` dan `npm audit`, cek header keamanan dan file yang terbuka (`/.env`, `/.git`, log) | Nol |
| 2, subagent | Satu auditor per area serangan, lalu satu verifikator skeptis yang mencoba membantah setiap temuan, lalu laporan dengan patch dan tes regresi | Sedang (quick) sampai tinggi (full) |

## Pakai

```bash
devstack-audit                              # full
devstack-audit --diff origin/main           # hanya file yang berubah, untuk PR
devstack-audit --url http://localhost:8001  # tambah cek header dan file terbuka
```

Fase 2 lewat agent: minta "jalankan security audit" atau `/skill:security-audit`. Laporan ada di `.ai/security/report.md`.

Kode keluar `1` kalau ada temuan ERROR, jadi bisa dipakai di pre-commit atau CI (`--fail-on error|warning|never`).

## Isi

| Folder | Isi |
| --- | --- |
| `semgrep/` | `php.yml`, `views.yml`, `node.yml`. Aturan: SQL injection (raw, concat, order by), mass assignment, IDOR, ID integer terbuka, RCE dan unserialize, SSRF, hash lemah, CSRF mati, CORS wildcard, debug aktif, upload tidak aman, XSS (Blade, CI3, DOM), secret di JS |
| `tools/audit.py` | Fase 1 dan inventaris route (Laravel `route:list`, controller CI3) |
| `skills/security-audit/` | Alur fase 2: keamanan, mode quick atau full, brief subagent, verifikasi, rubrik severity, format laporan, aturan perbaikan |
| `areas/` | Checklist 6 area: authz-idor, injection, auth-session, upload-ssrf, business-logic, config-secrets |
| `agents/` | Subagent `security-auditor` dan `security-verifier` |
| `fixtures/` | Contoh kode rentan PHP (20 celah) dan Node (12 celah), semua tertangkap tanpa salah tandai di kode aman |

Guard dari pelajaran proyek (`.ai/rules/*.yml`, dibuat `lessons guard`) ikut dijalankan otomatis.

## Keamanan devstack untuk penggunanya (rencana v0.5.0)

Yang sudah ada: SSH hanya key, akses dibatasi subnet, fail2ban, perintah berbahaya diblokir di config OMP, kredensial production tidak pernah di devbox, key provider tersimpan di 9Router.

Yang akan ditambah:
- Pre-commit menjalankan `audit.py --diff HEAD --fail-on error` dan scan secret, sehingga celah jelas dan secret tidak pernah ter-commit.
- Penyamaran secret sebelum konteks dikirim ke provider model (memastikan fitur `secrets` OMP aktif dan mencakup pola di atas).
- Pembatasan koneksi keluar devbox hanya ke 9Router, registry paket, dan Git.
- Isolasi agent per proyek (user atau container terpisah) untuk tim.

## Batasan jujur

- Aturan Semgrep berbasis pola: menangkap kesalahan umum dengan cepat, tetapi tidak mengerti alur data lintas file. Itu tugas fase 2.
- Kualitas fase 2 bergantung pada model. Verifikator dibuat untuk menyaring temuan palsu yang sering muncul dari model murah.
- Aplikasi tidak bisa menahan DDoS volumetrik sendirian; laporan selalu menyertakan rekomendasi infrastruktur.
