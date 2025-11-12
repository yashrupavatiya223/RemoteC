package com.argus.rat;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class ServiceRestarterReceiver extends BroadcastReceiver {
    private static final String TAG = "ServiceRestarterReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        Log.d(TAG, "Reinicialização de serviço solicitada");
        
        // Verificar se o serviço precisa ser reiniciado
        if (!PersistentService.isServiceRunning(context)) {
            restartPersistentService(context);
        } else {
            Log.d(TAG, "Serviço já está rodando, reinicialização não necessária");
        }
    }

    private void restartPersistentService(Context context) {
        try {
            Log.d(TAG, "Reiniciando PersistentService...");
            
            Intent serviceIntent = new Intent(context, PersistentService.class);
            
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                context.startForegroundService(serviceIntent);
            } else {
                context.startService(serviceIntent);
            }
            
            Log.d(TAG, "PersistentService reiniciado com sucesso");
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao reiniciar PersistentService", e);
            
            // Tentar novamente após um curto intervalo
            scheduleDelayedRestart(context);
        }
    }

    private void scheduleDelayedRestart(Context context) {
        try {
            Log.d(TAG, "Agendando reinicialização atrasada...");
            
            Intent restartIntent = new Intent(context, ServiceRestarterReceiver.class);
            android.app.PendingIntent pendingIntent = android.app.PendingIntent.getBroadcast(
                context, 1, restartIntent, 
                android.app.PendingIntent.FLAG_IMMUTABLE | android.app.PendingIntent.FLAG_UPDATE_CURRENT
            );
            
            android.app.AlarmManager alarmManager = (android.app.AlarmManager) 
                context.getSystemService(Context.ALARM_SERVICE);
            
            if (alarmManager != null) {
                long triggerTime = System.currentTimeMillis() + 30000; // 30 segundos
                
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
                    alarmManager.setExactAndAllowWhileIdle(
                        android.app.AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent
                    );
                } else if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.KITKAT) {
                    alarmManager.setExact(android.app.AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent);
                } else {
                    alarmManager.set(android.app.AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent);
                }
                
                Log.d(TAG, "Reinicialização atrasada agendada para 30 segundos");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao agendar reinicialização atrasada", e);
        }
    }

    // Método para forçar reinicialização imediata
    public static void forceRestart(Context context) {
        Intent intent = new Intent(context, ServiceRestarterReceiver.class);
        context.sendBroadcast(intent);
    }
}