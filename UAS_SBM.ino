#include <Wire.h>
#include <ArduinoJson.h> // Pastikan menggunakan Versi 7.x.x
#include <LittleFS.h>
#include <WiFi.h>
#include <PubSubClient.h>

// =======================================================
// --- KONFIGURASI JARINGAN GARASI & SERVER ---
// =======================================================
const char* ssid = "riri16indi"; 
const char* password = "15mai2024";
const char* mqtt_server = "192.168.236.205"; // Pastikan IP Raspberry Pi tidak berubah
const char* mqtt_topic = "telemetry/sync";

// Variabel Sensor I2C
const int MPU_ADDR = 0x68; 
int16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;

WiFiClient espClient;
PubSubClient client(espClient);

// Penanda agar data tidak di-dump berulang-ulang saat motor sudah parkir
bool isDataDumped = false; 

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22); // Pin SDA=21, SCL=22 untuk ESP32

  Serial.println("\n=== Sistem Motorcycle Black Box Aktif ===");

  // 1. Inisialisasi LittleFS (Sistem File ESP32)
  if(!LittleFS.begin(true)){
    Serial.println("Gagal me-mount LittleFS! Sistem berhenti.");
    return;
  }
  
  // 2. Bangunkan Sensor MPU6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);  // Register Power Management
  Wire.write(0);     // Set 0 untuk membangunkan
  byte error = Wire.endTransmission(true);
  
  if(error == 0) {
    Serial.println("Sensor IMU Siap.");
  } else {
    Serial.println("Gagal menemukan IMU! Cek kabel SDA/SCL.");
  }

  // 3. Setelan Jaringan
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password); 
  
  // 4. Setelan MQTT
  client.setServer(mqtt_server, 1883);
}

// Fungsi Khusus: Membaca Flash Disk & Mengirim ke Raspberry Pi
void dumpDataKeServer() {
  Serial.println("\n[SINKRONISASI] Mengakses memori perjalanan...");
  File file = LittleFS.open("/log_perjalanan.txt", FILE_READ);
  
  if (!file || file.size() == 0) {
    Serial.println("Tidak ada data baru untuk dikirim. Memori kosong.");
    isDataDumped = true; 
    if (file) file.close();
    return;
  }

  Serial.print("Total ukuran file log: ");
  Serial.print(file.size());
  Serial.println(" bytes.");
  Serial.println("Mulai membuang data (dump) ke Garasi...");

  int barisTerkirim = 0;

  // Baca selama file masih ada isinya
  while(file.available()){
    String line = file.readStringUntil('\n'); // Ambil 1 baris
    line.trim(); 
    
    if (line.length() > 0) {
      if (client.publish(mqtt_topic, line.c_str())) {
        barisTerkirim++;
        Serial.print("."); // Indikator pengiriman di Serial Monitor
      } else {
        Serial.println("\n[GAGAL] Koneksi MQTT terputus di tengah jalan!");
        file.close();
        return; 
      }
      
      // Jeda 50ms sangat penting agar Raspberry Pi tidak kewalahan menerima ledakan data
      delay(50); 
    }
  }

  file.close();

  Serial.println();
  Serial.print("[SUKSES] Berhasil mengirim ");
  Serial.print(barisTerkirim);
  Serial.println(" baris log perjalanan!");

  // ====================================================================
  // TRIGGER EVENT-DRIVEN (KUNCI UTAMA AI FORENSIK)
  // Mengirim sinyal "DONE" agar Python menghapus data lama & memicu Bot
  // ====================================================================
  Serial.println("Mengirim sinyal DONE ke Raspberry Pi...");
  client.publish(mqtt_topic, "{\"status\":\"DONE\"}");
  delay(100); 

  // Hapus file setelah sukses dikirim agar siap untuk perjalanan besok
  LittleFS.remove("/log_perjalanan.txt"); 
  isDataDumped = true; 
}

void loop() {
  // ============================================================
  // SKENARIO 1: ONLINE / MASUK GARASI (WI-FI TERSAMBUNG)
  // ============================================================
  if (WiFi.status() == WL_CONNECTED) {
    
    // Pastikan MQTT tersambung
    if (!client.connected()) {
      Serial.println("\nWi-Fi terhubung! Menyambung ke MQTT Broker...");
      if (client.connect("BlackBox_Motor_ESP32")) {
        Serial.println("Koneksi Broker Berhasil!");
      } 
    }
    
    client.loop(); 

    // Jika ada data perjalanan yang belum di-dump, eksekusi sekarang
    if (client.connected() && !isDataDumped) {
      dumpDataKeServer();
      Serial.println("\nMotor sedang parkir di garasi. Mode Siaga (Idle)...");
    }
  } 
  
  // ============================================================
  // SKENARIO 2: OFFLINE / DI JALAN RAYA (WI-FI TERPUTUS)
  // ============================================================
  else {
    isDataDumped = false; // Reset status siap-siap kalau nanti pulang ke garasi

    // 1. Baca Sensor MPU6050
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x3B);  
    Wire.endTransmission(false);
    Wire.requestFrom(MPU_ADDR, 14, true); 
    
    if(Wire.available() == 14) {
      AcX = Wire.read()<<8 | Wire.read(); 
      AcY = Wire.read()<<8 | Wire.read(); 
      AcZ = Wire.read()<<8 | Wire.read(); 
      Tmp = Wire.read()<<8 | Wire.read(); 
      GyX = Wire.read()<<8 | Wire.read(); 
      GyY = Wire.read()<<8 | Wire.read(); 
      GyZ = Wire.read()<<8 | Wire.read(); 

      // 2. Format JSON menggunakan ArduinoJson v7
      JsonDocument doc; 
      doc["ax"] = AcX; doc["ay"] = AcY; doc["az"] = AcZ;
      doc["gx"] = GyX; doc["gy"] = GyY; doc["gz"] = GyZ;

      String jsonString;
      serializeJson(doc, jsonString);

      // 3. Simpan ke Memori Flash (LittleFS)
      File file = LittleFS.open("/log_perjalanan.txt", FILE_APPEND);
      if(file){
        file.println(jsonString); 
        file.close();
        
        // Tampilkan di Serial Monitor untuk keperluan debugging
        Serial.print("[MEREKAM OFFLINE] -> ");
        Serial.println(jsonString);
      }
    }
  }
  
  // Interval sampling 500ms (sesuai standar kompromi kecepatan memori ESP32)
  delay(500); 
}