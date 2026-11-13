# devstack

Installer satu perintah, dengan update online, untuk server agentic coding pribadi: OMP (oh-my-pi), 9Router, SearXNG, toolchain PHP/JS, dan konfigurasi agent lengkap (AGENTS.md, skills, subagent, MCP, hook kualitas). Data pribadi diisi lewat wizard saat install pertama dan disimpan di `/etc/devstack/devstack.env`.

Yang dikerjakan installer:

| Area | Isi |
| --- | --- |
| Keamanan | User kerja + SSH key, SSH tanpa password dan tanpa root, firewall hanya dari subnet kantor dan VPN, fail2ban, update keamanan otomatis |
| Toolchain | PHP multi-versi (default 8.3 dan 7.4), Composer terverifikasi, Node LTS, Bun, uv, Docker, GitHub CLI, ripgrep, fd, Intelephense, LSP TypeScript, UI UX Pro Max CLI, Chromium untuk Playwright |
| Layanan | 9Router (LLM gateway, wajib API key) dan SearXNG, keduanya hanya bisa diakses dari subnet yang diizinkan |
| Agent | OMP + `~/omp-config` (repo Git) yang di-symlink ke `~/.omp/agent`, perintah `ai-init` untuk bootstrap proyek |
| Otak devstack | Task Router dan aturan (AGENTS.md), standar backend (BACKEND.md), taste engine untuk UI (`taste`), audit keamanan (`devstack-audit`), memori koreksi (`lessons`), bukti klaim (`devstack-verify`) |
| Verifikasi | `devstack-doctor` mengecek semuanya otomatis |

Yang tetap dikerjakan pemilik server (sengaja tidak diotomatisasi): akun dan API key provider LLM, combo di dashboard 9Router, dan Orca di laptop. VPN kantor tetap dikelola tim IT seperti biasa; installer tidak menyentuhnya.

## Yang baru di v0.5.0 dan v0.6.0

Rincian per versi ada di `CHANGELOG.md`. Ringkasnya:

- **Installer dan update profesional (v0.6.0)**: wizard setup, progres per tahap, perintah `devstack`, update online dari repo Git dengan catatan rilis dan rollback, cek update harian.

- **Task Router**: tugas diklasifikasi SMALL, MEDIUM, atau LARGE. Proses menyesuaikan ukuran tugas; aturan keamanan dan kualitas tetap wajib di semua kelas.
- **BACKEND.md**: standar backend yang diikuti tanpa diminta (clean architecture atau mirror, query optimal, cursor pagination, ID tidak terbuka, search bertingkat, keamanan, rate limit), dengan aturan aman untuk pilihan pengguna (Ajax, SSE, WebSocket, Redis, queue, JWT, S3). Mendukung PHP dan Node.
- **Taste engine** (`taste`): 6 arah visual, `taste init` dengan pertanyaan dan 3 kandidat berdampingan, BRAIN.md (cara berpikir desain), komponen aplikasi dan pola form, linter token, cek otomatis, review vision opsional.
- **Audit keamanan** (`devstack-audit`): Semgrep untuk Laravel, CI3, Node, dan JS; scan secret; audit dependensi; cek header dan file terbuka. Skill `security-audit` menyebar subagent per area serangan dengan verifikator skeptis.
- **Memori koreksi** (`lessons`): koreksi Anda disimpan, dipanggil kembali di tugas berikutnya, dan kesalahan yang berulang berubah menjadi pemeriksaan otomatis.
- **Bukti klaim** (`devstack-verify`): agent wajib membuktikan commit, file, dan tes sebelum melapor selesai.
- **BMAD dan Impeccable opsional**: `ai-init --bmad`, `ai-init --impeccable`.
- **Update aman** (`devstack-sync-config`): config bawaan diperbarui sebagai commit Git di `~/omp-config` setiap user, file dan skill pribadi tidak dihapus.

## Update online

Server yang dipasang lewat `get.sh` atau clone repo sudah terhubung. Server yang dipasang dari arsip cukup dihubungkan sekali:

```bash
sudo devstack source https://github.com/suciputri27/devstack.git
```

Setelah itu cukup:

```bash
devstack update --check      # ada versi baru?
sudo devstack update         # tampilkan catatan rilis, konfirmasi, pasang, cek kesehatan
sudo devstack update --to v0.6.0   # pasang versi tertentu, juga untuk rollback
```

Server juga mengecek versi baru setiap hari, dan memberi tahu saat Anda login SSH. Config di `/etc/devstack/devstack.env` tidak pernah disentuh update. Config agent di `~/omp-config` diperbarui sebagai commit Git yang bisa dilihat (`git -C ~/omp-config show HEAD`) dan dibatalkan (`git -C ~/omp-config revert HEAD`). Untuk melewati sinkron config agent, isi `DEVSTACK_SYNC_CONFIG=false`.

Setelah update, jalankan `ai-init` lagi di setiap proyek agar hook pre-commit ikut terbarui.

### Merilis versi baru

Lihat `CONTRIBUTING.md`: kerja di `develop`, `scripts/release.sh X.Y.Z`, Pull Request ke `main`, lalu tag dan GitHub Release dibuat otomatis.

### Dari instalasi lama tanpa repo (sekali saja)

```bash
scp devstack-v0.6.0.tar.gz <user>@<SERVER_IP>:~
ssh <user>@<SERVER_IP>
tar xzf devstack-v0.6.0.tar.gz && cd devstack && sudo ./install.sh
```

`.env` lama di folder installer dipindah otomatis ke `/etc/devstack/devstack.env`. Setelah itu hubungkan ke repo dengan `devstack source`, dan update berikutnya tidak perlu copy file lagi.

## Perintah server

| Perintah | Fungsi |
| --- | --- |
| `devstack status` | Versi, sumber update, layanan |
| `devstack doctor [--full]` | Pemeriksaan kesehatan lengkap |
| `sudo devstack update` | Update online |
| `sudo devstack config` | Ubah konfigurasi lalu terapkan |
| `sudo devstack reinstall` | Jalankan installer lagi |
| `sudo devstack sync-config` | Perbarui config agent semua user |
| `sudo devstack logs [--all]` | Log install terakhir |

## Syarat

- Ubuntu 24.04 LTS (22.04 juga didukung), fresh, akses root atau sudo.
- Server berada di jaringan kantor dengan IP tetap (IP statis atau reservasi DHCP), dan Anda tahu subnet LAN kantor serta subnet klien VPN.
- Public key SSH laptop Anda.

## 1. Install server

Satu perintah, di server Ubuntu 22.04 atau 24.04 yang baru:

```bash
curl -fsSL https://raw.githubusercontent.com/suciputri27/devstack/main/get.sh | sudo bash
```

Atau manual:

```bash
git clone https://github.com/suciputri27/devstack.git /opt/devstack/src
cd /opt/devstack/src && git checkout "$(git tag -l 'v*' --sort=-v:refname | head -n 1)"
sudo ./install.sh
```

Pertama kali, installer menjalankan wizard: IP server, subnet LAN dan VPN, user kerja, key SSH, dan identitas Git. Sebagian besar terdeteksi otomatis (key yang Anda pakai login juga ditawarkan). Jawaban disimpan di `/etc/devstack/devstack.env` (izin 600), lalu install langsung berjalan.

Selama install, layar hanya menampilkan tahap dan durasinya. Detail lengkap ada di `/var/log/devstack/`, ringkasannya lewat `sudo devstack logs`. Tambahkan `--verbose` untuk melihat output Ansible penuh.

Installer aman dijalankan berulang. Ubah nilai dengan `sudo devstack config` (membuka editor lalu menerapkan perubahan). Password sudo dihapus dari file config setelah install berhasil karena hanya dibutuhkan saat membuat user.

Pengaman lockout: jika `SSH_RESTRICTED=true` dan installer mendeteksi sesi SSH aktif dari alamat di luar `ALLOWED_SUBNETS`, installer berhenti sebelum mengunci firewall dan menampilkan alamat itu. Tambahkan subnetnya ke `ALLOWED_SUBNETS` jika memang jaringan Anda.

### Mengisi jaringan untuk server kantor

Server di kantor, dibuka dari rumah lewat VPN, tanpa VPN saat di kantor:

1. `SERVER_IP`: IP LAN server (di server: `ip -4 addr`).
2. `ALLOWED_SUBNETS`: subnet LAN kantor, ditambah subnet klien VPN jika berbeda.
3. Cara tahu alamat Anda saat lewat VPN: dari rumah, sambungkan VPN, SSH ke server, jalankan `echo $SSH_CLIENT`. Jika alamatnya sudah masuk subnet LAN (VPN memakai NAT), cukup subnet LAN. Jika alamatnya dari rentang lain (misalnya `10.10.0.x`), tambahkan subnet itu.

Contoh: `ALLOWED_SUBNETS="192.168.1.0/24 10.10.0.0/24"`.

Dengan ini, laptop memakai IP server yang sama di kantor maupun dari rumah, jadi config OMP dan alias SSH tidak perlu diganti.

Hanya menjalankan bagian tertentu:

```bash
sudo ./install.sh --tags workspace
sudo ./install.sh --tags ninerouter,searxng
sudo ./install.sh --check --diff     # simulasi tanpa mengubah apa pun
```

## 2. Siapkan 9Router (dari laptop, di kantor atau lewat VPN)

1. Ambil password awal: `sudo grep INITIAL_PASSWORD /opt/9router/.env`
2. Buka `http://<SERVER_IP>:20128/dashboard`, login, ganti password.
3. Providers: masukkan API key LLM Anda.
4. Buat combo dengan nama persis seperti ini (isinya bebas, model apa pun):

| Combo | Isi yang disarankan | Peran OMP |
| --- | --- | --- |
| `code-main` | Model coding harian, lalu cadangan dari provider lain | default, task |
| `code-heavy` | Model reasoning terkuat yang Anda punya | plan, slow |
| `code-design` | Model terbaik untuk frontend menurut uji Anda | designer, subagent ui-designer |
| `code-vision` | Model yang mendukung input gambar | vision (membaca screenshot) |
| `code-review` | Keluarga model berbeda dari `code-main` | advisor, subagent security-reviewer |
| `code-fast` | Model termurah dan tercepat | smol, tiny, commit |

5. Pastikan opsi wajib API key di dashboard aktif. Biarkan RTK Token Saver ON; mode yang mengubah gaya jawaban (Caveman, Ponytail) OFF.
6. API Keys: buat satu key per device (misalnya `devbox-omp`, `laptop-omp`).
7. Masukkan key server ke `~/.omp/agent/.env` milik user kerja (`NINEROUTER_API_KEY=`), atau isi di `.env` devstack lalu `sudo ./install.sh --tags workspace`.

Gunakan mode API key provider milik Anda sendiri. Jangan berbagi langganan atau akun OAuth provider ke orang lain lewat 9Router.

## 3. Verifikasi

```bash
devstack doctor           # cek keamanan, layanan, toolchain, konfigurasi
devstack doctor --full    # plus uji jawaban OMP lewat 9Router
```

## 4. Laptop

macOS atau Linux (Windows: jalankan di WSL):

```bash
./client/setup-laptop.sh <SERVER_IP> <user>
```

Skrip ini menambah alias SSH `devbox`, memasang Bun dan OMP, meng-clone `omp-config` dari server, dan menyiapkan `~/.omp/agent/.env` laptop. Setelah itu pasang Orca dari onorca.dev dan tambahkan SSH target `devbox`.

## 5. Per proyek

```bash
cd ~/projects/nama-proyek
ai-init
taste init          # proyek baru: pilih arah visual
taste pick civic    # kunci pilihan, lalu commit DESIGN.md, .taste/, dan aset taste
```

`ai-init` memasang pre-commit hook (em dash, syntax PHP, `taste lint`, `devstack-audit --staged`), folder `.ai/` untuk spesifikasi, screenshot, laporan keamanan, pelajaran, dan guard, template `AGENTS.md` dan `WATCHDOG.md`, serta skill CLI Orca. BMAD dan Impeccable hanya dipasang bila diminta (`--bmad`, `--impeccable`). Proyek yang sudah punya tampilan akan di-mirror; `taste init` hanya untuk arah visual baru.

Perintah harian:

| Perintah | Fungsi |
| --- | --- |
| `taste init`, `taste pick <preset>` | Pilih dan kunci arah visual |
| `taste lint`, `taste check <url>`, `taste review <url>` | Cek token, tampilan, dan review vision (opsional) |
| `devstack-audit [--diff origin/main] [--url http://localhost:PORT]` | Audit keamanan fase 1 |
| `lessons recall`, `lessons add`, `lessons list` | Memori koreksi |
| `devstack-verify --commit --run "php artisan test"` | Bukti sebelum melapor selesai |

Pengguna tidak perlu menghafal ini: agent menjalankannya sendiri sesuai AGENTS.md.

## Tim

Isi `TEAM_MEMBERS` di `.env` dengan `nama:public_key` setiap anggota, dipisah tanda `|`, lalu jalankan `sudo ./install.sh` lagi. Setiap anggota mendapat:

- User Linux sendiri, login hanya dengan SSH key, tanpa sudo.
- Bun, uv, OMP, Chromium, dan `~/omp-config` sendiri.
- Rentang port sendiri lewat `DEVSTACK_PORT_BASE` (pengguna utama 8100, anggota pertama 8200, berikutnya 8300, dst). Agent diarahkan memakai rentang ini.
- Akses Docker sesuai `TEAM_DOCKER_ACCESS`.

Setiap anggota lalu: membuat key 9Router sendiri di dashboard, mengisinya di `~/.omp/agent/.env` miliknya, dan menjalankan `./client/setup-laptop.sh <SERVER_IP> <nama>` di laptopnya. Agar aturan dan skill tim selalu sama, simpan `omp-config` di repo Git tim dan isi `OMP_CONFIG_REPO`.

## Menyimpan config agent

`~/omp-config` sudah berupa repo Git. Hubungkan ke repo privat Anda agar perubahan bisa disinkron antar mesin:

```bash
cd ~/omp-config
git remote add origin git@github.com:<user>/omp-config.git
git push -u origin main
```

Public key server untuk GitHub/GitLab: `cat ~/.ssh/id_ed25519.pub`.

## Update komponen

Versi dikunci di `versions.env`, termasuk `SEMGREP_VERSION` dan `PLAYWRIGHT_PY_VERSION` untuk tool devstack. Naikkan versi, uji di server staging, lalu `sudo ./install.sh`. OMP: tambahkan versi di `OMP_PACKAGE`, lalu `bun install -g <paket>` sebagai user kerja.

## Server berupa container LXC Proxmox

Docker versi terbaru gagal menjalankan container di LXC Proxmox sebelum versi 9.1 (error `ip_unprivileged_port_start`). Dengan `DOCKER_LXC_PIN=auto`, installer mendeteksi LXC lalu memasang `containerd.io` 1.7.28-1 dan versi Docker yang cocok, kemudian menguncinya agar tidak ter-update. Kunci ini bisa dilepas (`apt-mark unhold containerd.io docker-ce docker-ce-cli docker-ce-rootless-extras`) setelah host Proxmox diperbarui ke 9.1 atau lebih baru. Versi itu melewatkan satu patch keamanan runc, jadi hanya jalankan container yang Anda percayai.

## Catatan keamanan

- User kerja ada di grup `docker`, yang setara akses root. Ini wajar untuk dev box pribadi, tetapi jangan pakai server ini untuk production.
- Secret 9Router dibuat sekali di `/opt/9router/.env` (izin 600) dan tidak pernah ditimpa.
- Backup terenkripsi: `sudo devstack-backup-9router`.
- Semua port layanan di-bind ke `SERVER_IP`, bukan `0.0.0.0`, karena Docker bisa melewati aturan ufw.
- Rekan kantor yang satu subnet bisa menjangkau port 9Router, tetapi tidak bisa memakainya tanpa API key yang Anda buat. Persempit `ALLOWED_SUBNETS` (misalnya hanya IP laptop Anda, `192.168.1.23/32`) jika ingin lebih ketat.

## Lisensi pihak ketiga

Lihat `THIRD_PARTY.md`.
