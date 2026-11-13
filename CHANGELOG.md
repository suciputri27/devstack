# Changelog

## 0.6.0

- Installer baru: wizard setup (IP, subnet, VPN, user, key SSH, identitas Git terdeteksi otomatis), progres per tahap dengan durasi, log lengkap di `/var/log/devstack/`.
- Perintah `devstack`: `status`, `doctor`, `update`, `source`, `config`, `reinstall`, `sync-config`, `logs`, `version`.
- Update online dari repo Git: `sudo devstack source <git-url>` sekali, lalu `sudo devstack update`. Menampilkan catatan rilis, bisa rollback dengan `--to`.
- Cek update harian otomatis dan pesan saat login SSH.
- Konfigurasi pindah ke `/etc/devstack/devstack.env` (dipindah otomatis dari `.env` lama), tidak tertimpa update.
- Instal satu baris lewat `get.sh` dari repo publik.
- Alur rilis lewat Pull Request: `scripts/release.sh`, `scripts/check.sh`, CI GitHub Actions, tag dan GitHub Release otomatis setelah merge ke `main`.
- `.gitattributes` memaksa line ending Unix agar skrip tidak rusak saat diedit di Windows.

## 0.5.0

- Task Router, RULES dan GUIDELINES, belajar dari koreksi, audit keamanan setelah setiap tugas (AGENTS.md).
- BACKEND.md: standar backend PHP dan Node.
- Taste engine (`taste`): 6 arah visual, taste init, BRAIN.md, komponen, linter token, review vision opsional.
- Audit keamanan (`devstack-audit`, skill `security-audit`), memori koreksi (`lessons`), bukti klaim (`devstack-verify`).
- BMAD dan Impeccable opsional di `ai-init`. Sinkron config sebagai commit Git.
