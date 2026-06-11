# 🏍️ Motorcycle Black Box

> *"Every Ride Recorded, Every Accident Explained."*

Sistem monitoring dan perekaman perjalanan sepeda motor berbasis IoT yang mampu mendeteksi kecelakaan secara otomatis, menyimpan data sensor, dan mengirimkan notifikasi darurat melalui Telegram Bot.

Proyek ini dikembangkan oleh mahasiswa **Institut Teknologi Sepuluh Nopember (ITS)** sebagai solusi atas minimnya sistem black box pada kendaraan roda dua di Indonesia.

---

## 📋 Daftar Isi

- [Latar Belakang](#latar-belakang)
- [Fitur Utama](#fitur-utama)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Komponen](#komponen)
- [Instalasi & Konfigurasi](#instalasi--konfigurasi)
- [Cara Penggunaan](#cara-penggunaan)
- [Struktur Proyek](#struktur-proyek)
- [Tim Pengembang](#tim-pengembang)

---

## 🎯 Latar Belakang

Indonesia memiliki lebih dari **120 juta** unit sepeda motor yang beredar, menjadikannya penyumbang kecelakaan lalu lintas terbesar. Namun hingga kini, kendaraan roda dua umumnya tidak dilengkapi sistem black box, sehingga:

- Kronologi kecelakaan sulit direkonstruksi
- Korban kesulitan memperoleh bukti untuk klaim asuransi
- Data kondisi kendaraan sebelum dan sesudah kecelakaan tidak tersedia

**Motorcycle Black Box** hadir sebagai solusi IoT yang terjangkau untuk menjawab permasalahan ini.

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|---|---|
| 📡 **Real-Time Monitoring** | Merekam data pitch dan roll kendaraan secara terus-menerus |
| ⚡ **Accident Detection** | Mendeteksi benturan keras, rollover, dan akselerasi ekstrem secara otomatis |
| 💾 **Data Logging** | Menyimpan riwayat perjalanan lengkap ke penyimpanan lokal |
| 🔔 **Emergency Alert** | Mengirim notifikasi darurat kepada keluarga/pihak terkait via Telegram Bot |
| 🤖 **AI Assistant** | Bot Telegram berbasis AI (Ollama/Gemma2) yang bisa menjawab pertanyaan tentang kondisi motor |
| ☁️ **Cloud Sync** | Sinkronisasi data dari ESP32 ke Raspberry Pi via protokol MQTT |

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  MOTORCYCLE     │────▶│  ESP32           │────▶│  ACCIDENT          │
│  (MPU6050)      │     │  CONTROLLER      │     │  DETECTION         │
└─────────────────┘     └──────────────────┘     └────────────────────┘
                                                           │
                                                           ▼
                                                  ┌────────────────────┐
                                                  │   CLOUD SERVER     │
                                                  │  (Raspberry Pi +   │
                                                  │   MQTT Broker)     │
                                                  └────────────────────┘
                                                           │
                                          ┌────────────────┴──────────────┐
                                          ▼                               ▼
                                 ┌─────────────────┐           ┌──────────────────┐
                                 │  MOBILE APP     │           │  EMERGENCY       │
                                 │  (Telegram Bot) │           │  NOTIFICATION    │
                                 └─────────────────┘           └──────────────────┘
```

**Alur data:**
1. Sensor MPU6050 membaca data akselerometer & giroskop dari motor
2. ESP32 memproses data dan mengirimkannya via Wi-Fi menggunakan protokol MQTT
3. Raspberry Pi (MQTT Broker) menerima dan menyimpan data ke file JSON
4. Telegram Bot membaca data JSON dan menjawab pertanyaan pengguna menggunakan AI lokal (Ollama)

---

## 🔧 Komponen

### Hardware

| Komponen | Fungsi | Estimasi Biaya |
|---|---|---|
| ESP32 | Mikrokontroler utama + konektivitas Wi-Fi | Rp 80.000 |
| MPU6050 | Akselerometer & Giroskop (6-axis IMU) | Rp 20.000 |
| Power Supply / Powerbank | Sumber daya portabel | Rp 35.000 |
| Box Project | Wadah pelindung komponen | Rp 10.000 |
| **Total** | | **Rp 145.000** |

### Software & Dependencies

**ESP32 Firmware (`UAS_SBM.ino`)**
- Arduino IDE
- Library: `Wire.h`, `WiFi.h`, `PubSubClient.h`, `MPU6050.h`

**Raspberry Pi / Server**
```bash
pip install paho-mqtt
pip install pyTelegramBotAPI
pip install matplotlib
pip install requests
```

**AI Engine**
- [Ollama](https://ollama.ai/) dengan model `gemma2:2b` (berjalan lokal di Raspberry Pi)

---

## 🚀 Instalasi & Konfigurasi

### 1. Setup ESP32

Buka `UAS_SBM.ino` di Arduino IDE, lalu sesuaikan konfigurasi berikut:

```cpp
const char* ssid     = "NAMA_WIFI_ANDA";
const char* password = "PASSWORD_WIFI_ANDA";
const char* mqtt_server = "IP_RASPBERRY_PI_ANDA";
```

Upload sketch ke ESP32.

### 2. Setup MQTT Broker di Raspberry Pi

```bash
sudo apt install mosquitto mosquitto-clients -y
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### 3. Jalankan Data Collector

Script ini mendengarkan data dari ESP32 dan menyimpannya ke file JSON:

```bash
python3 penagkapdata.py
```

### 4. Setup Telegram Bot

- Buat bot baru via [@BotFather](https://t.me/BotFather) di Telegram
- Salin token yang diberikan
- Edit `bot_telegram.py` dan isi konfigurasi:

```python
TOKEN = "TOKEN_BOT_TELEGRAM_ANDA"
FILE_LOG = "/path/ke/log_motor.json"
BATAS_SERVIS_MENIT = 3000  # sesuaikan interval servis (menit)
```

### 5. Install & Jalankan Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull gemma2:2b
ollama serve
```

### 6. Jalankan Telegram Bot

```bash
python3 bot_telegram.py
```

---

## 💬 Cara Penggunaan

Setelah semua komponen berjalan, buka Telegram dan mulai chat dengan bot Anda.

| Pertanyaan Contoh | Respons Bot |
|---|---|
| `/start` | Sambutan dan pengenalan bot |
| "Berapa lama motor sudah berjalan?" | Durasi perjalanan dalam menit |
| "Berapa kali melewati lubang?" | Jumlah deteksi hentakan keras |
| "Motor pernah oleng?" | Jumlah insiden miring/rollover |
| "Kapan servis berikutnya?" | Sisa waktu menuju jadwal servis |
| "Cuaca sekarang gimana?" | Informasi cuaca terkini (Surabaya) |
| "Tampilkan laporan" | Laporan lengkap + grafik guncangan |
| "Grafik motor" | Visualisasi guncangan 50 data terakhir |

---

## 📁 Struktur Proyek

```
motorcycle-black-box/
│
├── UAS_SBM.ino          # Firmware ESP32 (pembacaan sensor & MQTT publisher)
├── penagkapdata.py      # MQTT subscriber & data logger (berjalan di Raspberry Pi)
├── bot_telegram.py      # Telegram Bot + AI assistant (berjalan di Raspberry Pi)
└── README.md
```

**Format data log (`log_motor.json`):**
```json
[
  {
    "ax": 1200,
    "ay": -300,
    "az": 16800,
    "gx": 150,
    "gy": -80,
    "gz": 20,
    "timestamp": "..."
  }
]
```

| Field | Keterangan |
|---|---|
| `ax`, `ay`, `az` | Data akselerometer (X, Y, Z) |
| `gx`, `gy`, `gz` | Data giroskop (X, Y, Z) |
| Threshold `az > 15000` | Indikator melewati lubang / hentakan keras |
| Threshold `gx/gy > 20000` | Indikator motor oleng / miring |

---

## 👥 Tim Pengembang

| Nama | Peran | Tanggung Jawab |
|---|---|---|
| Galuh Andar Siwi | Project Manager | Overall Project & Team Management |
| Sri Kusmiyati | Hardware Specialist | ESP32 & MPU6050 |
| Riri Desi Nofitri | Software Specialist | MQTT & AI Integration |
| Fathika Afrine A | Quality Assurance | Test Drive & Data Verification |

**Institut Teknologi Sepuluh Nopember (ITS)** — Surabaya, Indonesia

---

## 📊 SWOT Analysis

| | Positif | Negatif |
|---|---|---|
| **Internal** | ✅ Harga terjangkau, IoT-based, real-time monitoring | ⚠️ Memerlukan koneksi internet |
| **Eksternal** | 🚀 Pasar motor yang besar, tren smart transportation, integrasi asuransi | 🔒 Kompetitor, keamanan data |

---

## 📄 Lisensi

Proyek ini dikembangkan untuk keperluan akademik di Institut Teknologi Sepuluh Nopember.
