package com.argus.rat;

import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/**
 * Utilitários de criptografia AES-256 para Argus v.2.0
 * Usado para comunicação segura entre Android e C2
 */
public class EncryptionUtils {
    
    private static final String ALGORITHM = "AES";
    private static final String TRANSFORMATION = "AES/CBC/PKCS5Padding";
    private static final int IV_SIZE = 16;
    
    /**
     * Converte string para chave AES usando SHA-256
     */
    private static SecretKey stringToKey(String keyString) throws Exception {
        MessageDigest sha = MessageDigest.getInstance("SHA-256");
        byte[] keyBytes = sha.digest(keyString.getBytes(StandardCharsets.UTF_8));
        return new SecretKeySpec(keyBytes, ALGORITHM);
    }
    
    /**
     * Gera IV (Initialization Vector) aleatório
     */
    private static byte[] generateIV() {
        byte[] iv = new byte[IV_SIZE];
        new SecureRandom().nextBytes(iv);
        return iv;
    }
    
    /**
     * Criptografa dados usando chave string
     * 
     * @param data Dados para criptografar
     * @param keyString Chave como string
     * @return String Base64 com IV + dados criptografados
     */
    public static String encrypt(String data, String keyString) throws Exception {
        SecretKey secretKey = stringToKey(keyString);
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        byte[] iv = generateIV();
        IvParameterSpec ivSpec = new IvParameterSpec(iv);
        
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, ivSpec);
        byte[] encrypted = cipher.doFinal(data.getBytes(StandardCharsets.UTF_8));
        
        // Combinar IV + dados criptografados
        byte[] combined = new byte[iv.length + encrypted.length];
        System.arraycopy(iv, 0, combined, 0, iv.length);
        System.arraycopy(encrypted, 0, combined, iv.length, encrypted.length);
        
        return Base64.encodeToString(combined, Base64.NO_WRAP);
    }
    
    /**
     * Descriptografa dados usando chave string
     * 
     * @param encryptedData String Base64 com IV + dados criptografados
     * @param keyString Chave como string
     * @return Dados descriptografados
     */
    public static String decrypt(String encryptedData, String keyString) throws Exception {
        SecretKey secretKey = stringToKey(keyString);
        byte[] combined = Base64.decode(encryptedData, Base64.NO_WRAP);
        
        // Separar IV e dados criptografados
        byte[] iv = new byte[IV_SIZE];
        byte[] encrypted = new byte[combined.length - IV_SIZE];
        
        System.arraycopy(combined, 0, iv, 0, IV_SIZE);
        System.arraycopy(combined, IV_SIZE, encrypted, 0, encrypted.length);
        
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        IvParameterSpec ivSpec = new IvParameterSpec(iv);
        cipher.init(Cipher.DECRYPT_MODE, secretKey, ivSpec);
        
        byte[] decrypted = cipher.doFinal(encrypted);
        return new String(decrypted, StandardCharsets.UTF_8);
    }
    
    /**
     * Calcula hash SHA-256
     */
    public static String sha256(String data) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(data.getBytes(StandardCharsets.UTF_8));
        return bytesToHex(hash);
    }
    
    /**
     * Converte bytes para hexadecimal
     */
    private static String bytesToHex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes) {
            result.append(String.format("%02x", b));
        }
        return result.toString();
    }
    
    /**
     * Verifica integridade dos dados
     */
    public static boolean verifyIntegrity(String data, String hash) throws Exception {
        String calculated = sha256(data);
        return calculated.equals(hash);
    }
}

