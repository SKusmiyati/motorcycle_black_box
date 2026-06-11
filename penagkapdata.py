import paho.mqtt.client as mqtt
import json

BROKER_ADDRESS = "localhost"
TOPIC = "telemetry/sync"
FILE_LOG = "/home/raspberry/log_motor.json"

buffer_data = [] # Wadah sementara menampung ledakan data ESP32

def on_connect(client, userdata, flags, rc):
    print("Menunggu sinkronisasi dari motor...")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    global buffer_data
    payload = msg.payload.decode('utf-8')
    
    # JIKA MENERIMA SINYAL SELESAI DARI ESP32
    if '"status":"DONE"' in payload or '"status": "DONE"' in payload:
        if len(buffer_data) > 0:
            print(f"\n[SUKSES] Menyimpan {len(buffer_data)} data perjalanan terbaru!")
            
            # TIMPA FILE LAMA! Bot hanya akan membaca perjalanan terakhir ini
            with open(FILE_LOG, 'w') as file:
                json.dump(buffer_data, file, indent=2)
                
            print("Data diperbarui! Bot Telegram siap ditanya.")
            buffer_data = [] # Kosongkan wadah untuk perjalanan besok
        else:
            print("\n[INFO] Sinyal DONE diterima, tapi tidak ada data.")
            
    # JIKA MENERIMA DATA SENSOR BIASA
    else:
        try:
            data = json.loads(payload)
            buffer_data.append(data)
            # Tampilkan indikator proses sinkronisasi di layar
            print(f"Mengunduh data perjalanan... ({len(buffer_data)} baris)", end='\r')
        except:
            pass

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_ADDRESS, 1883, 60)
client.loop_forever()
