package com.argus.rat;

import android.content.Context;
import android.provider.Settings;
import android.util.Log;
import java.security.MessageDigest;

/**
 * Utilitário centralizado para geração e cache de Device ID
 * Garante consistência em todo o aplicativo
 */
public class DeviceIdentifier {
    private static final String TAG = "DeviceIdentifier";
    private static String cachedDeviceId = null;
    private static final String PREFS_NAME = "device_prefs";
    private static final String KEY_DEVICE_ID = "device_id";
    
    /**
     * Obtém o Device ID (cache em memória e SharedPreferences)
     */
    public static synchronized String getDeviceId(Context context) {
        // 1. Verificar cache em memória
        if (cachedDeviceId != null) {
            return cachedDeviceId;
        }
        
        // 2. Verificar SharedPreferences
        android.content.SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        cachedDeviceId = prefs.getString(KEY_DEVICE_ID, null);
        
        if (cachedDeviceId != null) {
            Log.d(TAG, "Device ID recuperado de SharedPreferences");
            return cachedDeviceId;
        }
        
        // 3. Gerar novo Device ID
        cachedDeviceId = generateDeviceId(context);
        
        // 4. Salvar em SharedPreferences
        prefs.edit().putString(KEY_DEVICE_ID, cachedDeviceId).apply();
        
        Log.i(TAG, "Novo Device ID gerado e salvo: " + cachedDeviceId);
        
        return cachedDeviceId;
    }
    
    /**
     * Gera um Device ID único baseado em ANDROID_ID + hash de informações do dispositivo
     */
    private static String generateDeviceId(Context context) {
        try {
            // Obter ANDROID_ID (único por instalação)
            String androidId = Settings.Secure.getString(
                context.getContentResolver(),
                Settings.Secure.ANDROID_ID
            );
            
            // Criar string com informações do dispositivo
            StringBuilder deviceInfo = new StringBuilder();
            deviceInfo.append(androidId != null ? androidId : "unknown");
            deviceInfo.append("|");
            deviceInfo.append(android.os.Build.MODEL);
            deviceInfo.append("|");
            deviceInfo.append(android.os.Build.MANUFACTURER);
            deviceInfo.append("|");
            deviceInfo.append(android.os.Build.BRAND);
            deviceInfo.append("|");
            deviceInfo.append(android.os.Build.DEVICE);
            
            // Gerar hash SHA-256
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(deviceInfo.toString().getBytes("UTF-8"));
            
            // Converter para hex
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            
            // Retornar primeiros 32 caracteres
            return hexString.toString().substring(0, 32);
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao gerar Device ID, usando fallback", e);
            
            // Fallback: usar ANDROID_ID direto ou gerar UUID aleatório
            String androidId = Settings.Secure.getString(
                context.getContentResolver(),
                Settings.Secure.ANDROID_ID
            );
            
            return androidId != null ? androidId : java.util.UUID.randomUUID().toString();
        }
    }
    
    /**
     * Limpa o cache (útil para testes)
     */
    public static synchronized void clearCache(Context context) {
        cachedDeviceId = null;
        
        android.content.SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        prefs.edit().remove(KEY_DEVICE_ID).apply();
        
        Log.i(TAG, "Cache de Device ID limpo");
    }
    
    /**
     * Obtém informações detalhadas do dispositivo
     */
    public static DeviceInfo getDeviceInfo(Context context) {
        return new DeviceInfo(
            getDeviceId(context),
            android.os.Build.MODEL,
            android.os.Build.MANUFACTURER,
            android.os.Build.BRAND,
            android.os.Build.DEVICE,
            android.os.Build.VERSION.RELEASE,
            android.os.Build.VERSION.SDK_INT
        );
    }
    
    /**
     * Classe para armazenar informações do dispositivo
     */
    public static class DeviceInfo {
        public final String deviceId;
        public final String model;
        public final String manufacturer;
        public final String brand;
        public final String device;
        public final String androidVersion;
        public final int apiLevel;
        
        DeviceInfo(String deviceId, String model, String manufacturer, String brand,
                   String device, String androidVersion, int apiLevel) {
            this.deviceId = deviceId;
            this.model = model;
            this.manufacturer = manufacturer;
            this.brand = brand;
            this.device = device;
            this.androidVersion = androidVersion;
            this.apiLevel = apiLevel;
        }
        
        @Override
        public String toString() {
            return String.format("Device[id=%s, model=%s %s, Android=%s (API %d)]",
                deviceId, manufacturer, model, androidVersion, apiLevel);
        }
    }
}

