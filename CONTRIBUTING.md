# Alur kerja devstack

## Branch

| Branch | Isi | Aturan |
| --- | --- | --- |
| `main` | Hanya versi stabil yang sudah dirilis | Dikunci: tanpa push langsung, tanpa force push, masuk hanya lewat Pull Request yang lulus CI |
| `develop` | Kumpulan perubahan untuk rilis berikutnya | Tempat merge fitur dan perbaikan |
| `feat/<nama>`, `fix/<nama>` | Satu perubahan | Dibuat dari `develop`, kembali ke `develop` lewat Pull Request |

Server tidak pernah mengikuti branch. Server hanya memasang tag rilis (`v0.6.0`, `v0.6.1`, ...), jadi pekerjaan yang belum selesai di `develop` tidak akan pernah sampai ke server.

## Sehari-hari

```bash
git switch develop && git pull
git switch -c fix/pesan-wizard
# ubah, lalu
scripts/check.sh
git commit -am "fix: pesan wizard lebih jelas"
git push -u origin fix/pesan-wizard
# buka Pull Request ke develop
```

Format commit: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`. Tanpa em dash.

## Rilis

1. Di `develop`, tulis bagian `## X.Y.Z` paling atas di `CHANGELOG.md`.
2. `scripts/release.sh X.Y.Z` (menaikkan `VERSION`, menjalankan semua pemeriksaan, commit, push).
3. Buka Pull Request `develop` ke `main`. Setelah CI hijau, merge.
4. GitHub Actions membuat tag `vX.Y.Z` dan GitHub Release otomatis.
5. Server: `sudo devstack update` (atau tunggu pemberitahuan cek harian).

Nomor versi: `X` perubahan besar yang butuh langkah manual, `Y` fitur baru, `Z` perbaikan.

## Pemeriksaan

`scripts/check.sh` menjalankan syntax shell dan Python, YAML dan JSON, em dash, line ending Unix, bit eksekusi, kontras preset, aturan keamanan terhadap contoh rentan, dan syntax playbook. CI menjalankan skrip yang sama di setiap Pull Request.

Jangan pernah meng-commit `.env`, key, token, atau data pelanggan. Repo ini publik.
