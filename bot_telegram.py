import telebot
import json
import requests
import time
import matplotlib.pyplot as plt

# --- KONFIGURASI UTAMA ---
TOKEN = "8693600157:AAFTR_2EmsETOV6-j5Vo3yrVsfYhF41YqtI"
bot = telebot.TeleBot(TOKEN)
OLLAMA_URL = "http://localhost:11434/api/generate"
NAMA_MODEL = "gemma2:2b" 
FILE_LOG = "/home/raspberry/log_motor.json"
BATAS_SERVIS_MENIT = 3000
URL_CUACA = "http://wttr.in/Surabaya?format=j1"

# --- CACHE & FUNGSI GRAFIK ---
data_cuaca_cache = "Cerah"
waktu_cuaca_terakhir = 0

def buat_grafik_dan_analisis():
    try:
        with open(FILE_LOG, "r") as file:
            data = json.load(file)
        
        az_values = [d.get('az', 0) for d in data[-50:]]
        if not az_values:
            return "Data rekaman guncangan masih kosong."
            
        max_val = max([abs(v) for v in az_values])
        status_grafik = "Kondisi jalan halus." if max_val < 15000 else "Terdeteksi guncangan keras."
        
        plt.figure(figsize=(6, 3))
        plt.plot(az_values, color='red', marker='o', markersize=3)
        plt.title("Grafik Guncangan Motor (50 Data Terakhir)")
        plt.ylabel("Tingkat Guncangan")
        plt.grid(True)
        plt.savefig("grafik_motor.png")
        plt.close()
        return status_grafik
    except Exception as e:
        return "Gagal memproses visualisasi grafik."

def bersihkan_teks(teks):
    teks = teks.strip()
    if "Note:" in teks:
        teks = teks.split("Note:")[0]
    if "Catatan:" in teks:
        teks = teks.split("Catatan:")[0]
    return teks.replace('*', '').replace('_', '').replace('"', '').replace("'", "").strip()

# --- MAIN BOT ---
@bot.message_handler(commands=['start', 'help'])
def sambutan(message):
    bot.reply_to(message, "Halo. Saya adalah asisten AI pemantau motor Anda. Ada yang bisa saya bantu terkait kondisi motor, cuaca, atau laporan perjalanan hari ini?")

@bot.message_handler(func=lambda message: True)
def balas_pesan(message):
    global data_cuaca_cache, waktu_cuaca_terakhir
    pertanyaan = message.text
    chat_id = message.chat.id
    
    # 1. BACA DATA AKTUAL
    try:
        with open(FILE_LOG, "r") as file:
            log_data = json.load(file)
    except:
        log_data = []

    # HITUNGAN PERBAIKAN
    jumlah_lubang = sum(1 for d in log_data if abs(d.get('az', 0)) > 15000)
    insiden_miring = sum(1 for d in log_data if abs(d.get('gx', 0)) > 20000 or abs(d.get('gy', 0)) > 20000)
    
    # Tambahan: Menghitung waktu motor berjalan berdasarkan log (asumsi 1 log = 1 detik)
    waktu_berjalan_menit = len(log_data) // 60
    sisa_menit_servis = max(0, BATAS_SERVIS_MENIT - waktu_berjalan_menit)
    
    status_analisis = buat_grafik_dan_analisis()
    
    # 2. UPDATE DATA CUACA
    if time.time() - waktu_cuaca_terakhir > 600:
        try:
            req = requests.get(URL_CUACA, timeout=3).json()
            data_cuaca_cache = req['current_condition'][0]['weatherDesc'][0]['value']
            waktu_cuaca_terakhir = time.time()
        except: pass

    # 3. ROUTING INTENT (ALGORITMA KLASIFIKASI PERTANYAAN)
    p_lower = pertanyaan.lower()
    
    is_grafik = any(k in p_lower for k in ['grafik', 'merah', 'gambar', 'visualisasi'])
    is_laporan = any(k in p_lower for k in ['laporan', 'data', 'dashboard', 'statistik', 'statik'])
    is_analisis = any(k in p_lower for k in ['analisis', 'maksud analisis', 'jelaskan', 'maksudnya', 'artinya']) and not is_grafik
    is_bantuan = any(k in p_lower for k in ['bisa apa', 'fitur', 'bantuan', 'kemampuan', 'tolong', 'apa saja', 'menu'])
    
    tanya_miring = any(k in p_lower for k in ['miring', 'jatuh', 'roboh', 'oleng', 'keseimbangan'])
    tanya_lubang = any(k in p_lower for k in ['lubang', 'hentakan', 'guncangan', 'rusak'])
    tanya_servis = any(k in p_lower for k in ['servis', 'perawatan', 'ganti oli']) # Hapus kata 'waktu' agar tidak tabrakan
    tanya_jalan = any(k in p_lower for k in ['berjalan', 'jalan', 'menyala', 'hidup', 'durasi', 'sudah berapa lama']) # Tambahan keyword berjalan
    tanya_cuaca = any(k in p_lower for k in ['cuaca', 'hujan', 'panas', 'suhu', 'haze', 'mendung'])
    is_tanya_angka = any(k in p_lower for k in ['berapa', 'jumlah', 'hitung', 'kapan'])

    # 4. PROMPT DASAR
    prompt_base = f"""Kamu adalah asisten AI pemantau motor yang profesional, cerdas, dan responsif.
Data saat ini:
- Lama motor berjalan: {waktu_berjalan_menit} menit
- Sisa waktu servis: {sisa_menit_servis} menit
- Melindas lubang: {jumlah_lubang} kali
- Oleng/miring: {insiden_miring} kali
- Cuaca: {data_cuaca_cache}

Aturan Mutlak (WAJIB DIPATUHI):
1. Tiru gaya bahasa user. Jika user baku/formal, balas formal namun luwes. Jika user santai, balas santai namun tetap sopan.
2. DILARANG KERAS menggunakan kata gaul (bro, sis, eh, oh, dong, deh, waduh).
3. Jawab langsung ke inti pertanyaan tanpa basa-basi. 
4. Jika ditanya data berupa angka/berapa, berikan HANYA angka yang ditanyakan. Jangan bahas data lain.
5. Jangan gunakan istilah teknis sensor, gunakan bahasa awam yang mudah dipahami.
"""
    
    # 5. MATRIKS PROMPT (CONTEXT HARDLOCKING)
    if is_bantuan:
        prompt_sistem = prompt_base + "\n[TUGAS KHUSUS] Sebutkan dengan rapi bahwa kamu bisa: 1. Mengecek lama motor berjalan. 2. Mengecek jumlah motor melindas lubang. 3. Mengecek frekuensi motor oleng/miring. 4. Mengingatkan sisa waktu servis. 5. Mengecek cuaca. 6. Menampilkan laporan dan grafik perjalanan."
    elif is_grafik or is_analisis:
        prompt_sistem = prompt_base + "\n[TUGAS KHUSUS] Jelaskan grafik/analisis dengan bahasa awam yang mudah dipahami: Grafik ini menampilkan tingkat guncangan motor. Garis yang melonjak tinggi menunjukkan bahwa motor sedang melewati jalan berlubang atau permukaan yang tidak rata."
    elif is_laporan:
        prompt_sistem = prompt_base + "\n[TUGAS KHUSUS] Berikan pengantar laporan singkat dan sopan. Contoh: 'Berikut adalah laporan data perjalanan motor Anda saat ini.'"
    elif is_tanya_angka or tanya_miring or tanya_lubang or tanya_servis or tanya_cuaca or tanya_jalan:
        fokus = []
        # Memasukkan logika fokus yang lebih presisi
        if tanya_jalan: fokus.append(f"Motor sudah berjalan selama {waktu_berjalan_menit} menit.")
        if tanya_miring: fokus.append(f"Motor tercatat miring atau oleng sebanyak {insiden_miring} kali.")
        if tanya_lubang: fokus.append(f"Motor melewati jalan berlubang sebanyak {jumlah_lubang} kali.")
        if tanya_servis: fokus.append(f"Sisa waktu menuju servis berikutnya adalah {sisa_menit_servis} menit.")
        if tanya_cuaca: fokus.append(f"Cuaca saat ini terpantau {data_cuaca_cache}.")
        
        fokus_teks = " ".join(fokus) if fokus else "Sebutkan data yang diminta secara ringkas berdasarkan informasi di atas."
        prompt_sistem = prompt_base + f"\n[TUGAS KHUSUS] User meminta informasi spesifik. Jawab HANYA menggunakan informasi berikut ini: '{fokus_teks}'. Dilarang menambahkan penjelasan lain atau membahas data yang tidak ditanyakan."
    else:
        prompt_sistem = prompt_base + "\n[TUGAS KHUSUS] Respons percakapan user dengan natural, adaptif, dan sopan. Jika pertanyaan tidak relevan dengan motor, sampaikan dengan sopan bahwa fokus utamamu adalah memantau kondisi sepeda motor."

    # 6. INFERENSI LLM (OLLAMA)
    try:
        bot.send_chat_action(chat_id, 'typing')
        response = requests.post(OLLAMA_URL, json={
            "model": NAMA_MODEL, 
            "prompt": prompt_sistem + "\nUser: " + pertanyaan + "\nJawaban:", 
            "stream": False,
            "options": {"temperature": 0.15} 
        })
        
        hasil_ai = bersihkan_teks(response.json()['response'])
        if not hasil_ai:
            hasil_ai = "Maaf, saya kurang mengerti. Bisa diulangi pertanyaannya mengenai motor atau cuaca?"
            
        pesan_final = f"🤖 {hasil_ai}"
        
        # 7. MANAJEMEN OUTPUT 
        if is_laporan or is_grafik:
            if is_laporan:
                pesan_final += (f"\n\n--- 📊 Catatan Teknis ---\n"
                                f"⏳ Waktu Berjalan: {waktu_berjalan_menit} mnt | ⏱️ Sisa Servis: {sisa_menit_servis} mnt\n"
                                f"🚧 Melindas Lubang: {jumlah_lubang} kali | ⚠️ Oleng/Miring: {insiden_miring} kali\n"
                                f"📈 Kesimpulan: {status_analisis}")
            bot.send_message(chat_id, pesan_final)
            try:
                with open("grafik_motor.png", "rb") as photo:
                    bot.send_photo(chat_id, photo, caption="Visualisasi Grafik Guncangan")
            except:
                bot.send_message(chat_id, "⚠️ Berkas gambar grafik gagal dimuat.")
        else:
            bot.send_message(chat_id, pesan_final)
            
    except Exception as e:
        bot.send_message(chat_id, "❌ Koneksi ke sistem AI sedang mengalami gangguan.")

bot.infinity_polling()
