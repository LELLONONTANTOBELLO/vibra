import time
import requests
from jnius import autoclass, cast
from plyer import vibrator
from android import AndroidService

# Android imports
PythonService = autoclass('org.kivy.android.PythonService')
Context = autoclass('android.content.Context')
PowerManager = autoclass('android.os.PowerManager')
NotificationChannel = autoclass('android.app.NotificationChannel')
NotificationManager = autoclass('android.app.NotificationManager')
PendingIntent = autoclass('android.app.PendingIntent')
Intent = autoclass('android.content.Intent')
NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
Color = autoclass('android.graphics.Color')

SERVER_URL = "https://www.crashando.it/vibe/vibra.php"
CHANNEL_ID = "vibration_service_channel"

class VibrationService:
    def __init__(self):
        self.service = None
        self.wake_lock = None
        self.running = False
        self.last_vibrate_id = None
        
        self.patterns = {
            'a': [0.4],
            'b': [0.4, 0.2, 0.4],
            'c': [0.4, 0.2, 0.4, 0.2, 0.4],
            'd': [0.4, 0.2, 0.4, 0.2, 0.4, 0.2, 0.4]
        }
    
    def start(self):
        """Avvia il servizio"""
        print("=== STARTING VIBRATION SERVICE ===")
        
        try:
            self.service = cast('android.app.Service', PythonService.mService)
            print(f"Service obtained: {self.service}")
        except Exception as e:
            print(f"ERRORE getting service: {e}")
            return
        
        # Crea notifica e canale
        self.create_notification()
        
        # Acquisisci wakelock AGGRESSIVO
        self.acquire_wake_lock()
        
        # Avvia foreground service
        self.start_foreground()
        
        # Avvia polling
        self.running = True
        print("Starting polling loop...")
        self.polling_loop()
    
    def create_notification(self):
        """Crea il canale di notifica"""
        try:
            notification_service = cast(
                NotificationManager,
                self.service.getSystemService(Context.NOTIFICATION_SERVICE)
            )
            
            channel = NotificationChannel(
                CHANNEL_ID,
                "Vibration Service",
                NotificationManager.IMPORTANCE_HIGH  # HIGH per evitare kill
            )
            channel.setDescription("Servizio vibrazioni attivo")
            channel.enableLights(True)
            channel.setLightColor(Color.GREEN)
            channel.setShowBadge(True)
            notification_service.createNotificationChannel(channel)
            
            print("Notification channel created")
            
        except Exception as e:
            print(f"ERRORE creating channel: {e}")
    
    def start_foreground(self):
        """Avvia foreground service con PRIORITY HIGH"""
        try:
            # Intent per riaprire app
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(self.service, PythonActivity)
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP)
            
            pending_intent = PendingIntent.getActivity(
                self.service, 
                0, 
                intent, 
                PendingIntent.FLAG_IMMUTABLE
            )
            
            # Notifica con PRIORITY MAX
            builder = NotificationCompat.Builder(self.service, CHANNEL_ID)
            builder.setContentTitle("🟢 Vibration Service ATTIVO")
            builder.setContentText("In ascolto continuo...")
            builder.setSmallIcon(self.service.getApplicationInfo().icon)
            builder.setOngoing(True)
            builder.setPriority(NotificationCompat.PRIORITY_MAX)  # MAX priority
            builder.setContentIntent(pending_intent)
            builder.setAutoCancel(False)
            builder.setCategory(NotificationCompat.CATEGORY_SERVICE)
            
            notification = builder.build()
            
            # START FOREGROUND
            self.service.startForeground(1, notification)
            print("✅ Foreground service started with HIGH priority")
            
        except Exception as e:
            print(f"❌ ERRORE start foreground: {e}")
    
    def acquire_wake_lock(self):
        """WakeLock AGGRESSIVO per tenere CPU attiva"""
        try:
            power_manager = cast(
                PowerManager,
                self.service.getSystemService(Context.POWER_SERVICE)
            )
            
            # PARTIAL_WAKE_LOCK tiene la CPU attiva anche a schermo spento
            self.wake_lock = power_manager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK,
                "VibrationController::WakeLock"
            )
            
            # Acquire SENZA timeout (rimane sempre attivo)
            self.wake_lock.acquire()
            print("✅ Wake lock acquired (CPU always on)")
            
        except Exception as e:
            print(f"❌ ERRORE wake lock: {e}")
    
    def polling_loop(self):
        """Loop INFINITO di polling"""
        print("🔄 Polling loop STARTED")
        
        retry_count = 0
        
        while self.running:
            try:
                # Polling con timestamp
                response = requests.get(
                    f'{SERVER_URL}?poll&t={int(time.time() * 1000)}',
                    timeout=10  # Timeout più lungo
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Reset retry counter su successo
                    retry_count = 0
                    
                    if data.get('pattern') and data.get('id') != self.last_vibrate_id:
                        self.last_vibrate_id = data['id']
                        pattern = data['pattern']
                        
                        print(f"📳 PATTERN RICEVUTO: {pattern}")
                        self.execute_vibration(pattern)
                        self.update_notification(f"Ricevuto: {pattern.upper()}")
                else:
                    print(f"⚠️ Server response: {response.status_code}")
                        
            except requests.exceptions.Timeout:
                print(f"⏱️ Timeout - retry {retry_count}")
                retry_count += 1
                
            except Exception as e:
                print(f'❌ Polling error: {e}')
                retry_count += 1
            
            # Backoff esponenziale in caso di errori ripetuti
            if retry_count > 0:
                sleep_time = min(0.5 * (2 ** retry_count), 5)  # Max 5 sec
                time.sleep(sleep_time)
            else:
                time.sleep(0.2)  # Polling veloce quando tutto ok
        
        # Cleanup
        print("🛑 Stopping service...")
        self.stop()
    
    def execute_vibration(self, pattern_key):
        """Esegue pattern di vibrazione"""
        pattern = self.patterns.get(pattern_key)
        if not pattern:
            print(f"⚠️ Pattern {pattern_key} non trovato")
            return
        
        try:
            print(f"📳 Executing vibration: {pattern}")
            for i, duration in enumerate(pattern):
                if i > 0:
                    time.sleep(0.2)
                vibrator.vibrate(duration)
                print(f"  Vibrate {i+1}: {duration}s")
        except Exception as e:
            print(f'❌ Vibration error: {e}')
    
    def update_notification(self, text):
        """Aggiorna notifica"""
        try:
            builder = NotificationCompat.Builder(self.service, CHANNEL_ID)
            builder.setContentTitle("🟢 Vibration Service")
            builder.setContentText(text)
            builder.setSmallIcon(self.service.getApplicationInfo().icon)
            builder.setOngoing(True)
            builder.setPriority(NotificationCompat.PRIORITY_MAX)
            
            notification = builder.build()
            
            notification_service = cast(
                NotificationManager,
                self.service.getSystemService(Context.NOTIFICATION_SERVICE)
            )
            notification_service.notify(1, notification)
            
            # Ripristina dopo 3 secondi
            time.sleep(3)
            builder.setContentText("In ascolto continuo...")
            notification = builder.build()
            notification_service.notify(1, notification)
            
        except Exception as e:
            print(f"❌ Notification update error: {e}")
    
    def stop(self):
        """Ferma servizio"""
        print("🛑 Stopping service...")
        self.running = False
        
        if self.wake_lock and self.wake_lock.isHeld():
            self.wake_lock.release()
            print("Wake lock released")
        
        if self.service:
            self.service.stopForeground(True)
            self.service.stopSelf()
            print("Service stopped")

# Entry point
if __name__ == '__main__':
    print("=== SERVICE ENTRY POINT ===")
    service = VibrationService()
    service.start()