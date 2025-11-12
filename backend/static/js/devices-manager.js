/**
 * Devices Manager - Gerenciamento dinâmico de dispositivos
 * Integrado com WebSocket para atualizações em tempo real
 */

class DevicesManager {
    constructor() {
        this.devices = new Map();
        this.selectedDevice = null;
        this.updateInterval = null;
        this.init();
    }

    init() {
        console.log('DevicesManager inicializado');
        
        // Carregar dispositivos iniciais
        this.loadDevices();
        
        // Configurar listeners de WebSocket
        this.setupWebSocketListeners();
        
        // Configurar event handlers
        this.setupEventHandlers();
        
        // Atualizar periodicamente
        this.startAutoRefresh();
    }

    /**
     * Carrega lista de dispositivos do servidor
     */
    async loadDevices() {
        try {
            const response = await window.apiClient.get('/devices');
            
            if (Array.isArray(response)) {
                response.forEach(device => {
                    this.devices.set(device.device_id, device);
                });
                this.renderDevicesList();
                this.updateStats();
            }
        } catch (error) {
            console.error('Erro ao carregar dispositivos:', error);
            window.notificationSystem.error('Erro ao carregar dispositivos');
        }
    }

    /**
     * Configura listeners do WebSocket
     */
    setupWebSocketListeners() {
        const socket = window.socketManager;

        // Dispositivo conectado
        socket.on('device_connected', (data) => {
            this.handleDeviceConnected(data.device);
        });

        // Dispositivo desconectado
        socket.on('device_disconnected', (data) => {
            this.handleDeviceDisconnected(data.device_id);
        });

        // Dispositivo atualizado
        socket.on('device_updated', (data) => {
            this.handleDeviceUpdated(data);
        });

        // Dispositivo registrado
        socket.on('device_registered', (data) => {
            this.handleDeviceConnected(data.device);
        });
    }

    /**
     * Configura event handlers
     */
    setupEventHandlers() {
        // Filtro de busca
        const searchInput = document.getElementById('device-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterDevices(e.target.value);
            });
        }

        // Filtro de status
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterByStatus(e.target.value);
            });
        }

        // Refresh manual
        const refreshBtn = document.getElementById('refresh-devices');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDevices();
            });
        }
    }

    /**
     * Manipula dispositivo conectado
     */
    handleDeviceConnected(device) {
        console.log('Dispositivo conectado:', device);
        
        this.devices.set(device.device_id, device);
        this.renderDevicesList();
        this.updateStats();
        
        // Notificar usuário
        window.notificationSystem.success(
            `📱 Dispositivo conectado: ${device.model || device.device_name}`
        );
        
        // Adicionar efeito visual
        this.highlightDevice(device.device_id, 'success');
    }

    /**
     * Manipula dispositivo desconectado
     */
    handleDeviceDisconnected(deviceId) {
        console.log('Dispositivo desconectado:', deviceId);
        
        const device = this.devices.get(deviceId);
        if (device) {
            device.status = 'offline';
            device.last_seen = new Date().toISOString();
            this.renderDevicesList();
            this.updateStats();
            
            window.notificationSystem.warning(
                `📱 Dispositivo desconectado: ${device.model || device.device_name}`
            );
            
            this.highlightDevice(deviceId, 'warning');
        }
    }

    /**
     * Manipula atualização de dispositivo
     */
    handleDeviceUpdated(data) {
        const device = this.devices.get(data.device_id);
        if (device) {
            Object.assign(device, data);
            this.renderDevicesList();
            this.updateStats();
        }
    }

    /**
     * Renderiza lista de dispositivos
     */
    renderDevicesList() {
        const container = document.getElementById('devices-list');
        if (!container) return;

        // Ordenar dispositivos (online primeiro, depois por última visualização)
        const deviceArray = Array.from(this.devices.values()).sort((a, b) => {
            if (a.status === 'online' && b.status !== 'online') return -1;
            if (a.status !== 'online' && b.status === 'online') return 1;
            return new Date(b.last_seen || 0) - new Date(a.last_seen || 0);
        });

        container.innerHTML = deviceArray.map(device => this.renderDeviceCard(device)).join('');
        
        // Adicionar event listeners aos cards
        this.attachDeviceCardListeners();
    }

    /**
     * Renderiza card de dispositivo
     */
    renderDeviceCard(device) {
        const statusClass = device.status === 'online' ? 'success' : 'secondary';
        const statusIcon = device.status === 'online' ? '🟢' : '⚫';
        const batteryIcon = this.getBatteryIcon(device.battery_level, device.is_charging);
        const lastSeen = device.last_seen ? window.utils.formatRelativeTime(device.last_seen) : 'Nunca';

        return `
            <div class="col-md-6 col-lg-4 mb-3" data-device-id="${device.device_id}">
                <div class="card device-card h-100 ${this.selectedDevice === device.device_id ? 'border-primary' : ''}">
                    <div class="card-header bg-${statusClass} text-white">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">${statusIcon} ${device.model || device.device_name}</h6>
                            <span class="badge bg-light text-dark">${device.status}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="mb-1"><strong>ID:</strong> <code>${device.device_id.substring(0, 8)}...</code></p>
                        <p class="mb-1"><strong>Fabricante:</strong> ${device.manufacturer || 'N/A'}</p>
                        <p class="mb-1"><strong>Android:</strong> ${device.android_version || 'N/A'} (API ${device.api_level || 'N/A'})</p>
                        <p class="mb-1"><strong>Bateria:</strong> ${batteryIcon} ${device.battery_level !== null ? device.battery_level + '%' : 'N/A'}</p>
                        <p class="mb-1"><strong>Última Conexão:</strong> ${lastSeen}</p>
                        ${device.latitude && device.longitude ? `
                            <p class="mb-1"><strong>Localização:</strong> 
                                <a href="https://www.google.com/maps?q=${device.latitude},${device.longitude}" target="_blank">
                                    📍 Ver no mapa
                                </a>
                            </p>
                        ` : ''}
                    </div>
                    <div class="card-footer">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-sm btn-primary device-select" data-device-id="${device.device_id}">
                                Selecionar
                            </button>
                            <button class="btn btn-sm btn-info device-info" data-device-id="${device.device_id}">
                                Info
                            </button>
                            <button class="btn btn-sm btn-danger device-delete" data-device-id="${device.device_id}">
                                Remover
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Obtém ícone de bateria
     */
    getBatteryIcon(level, isCharging) {
        if (level === null || level === undefined) return '🔋';
        if (isCharging) return '⚡';
        if (level >= 80) return '🔋';
        if (level >= 50) return '🔋';
        if (level >= 20) return '🪫';
        return '🪫';
    }

    /**
     * Anexa event listeners aos cards
     */
    attachDeviceCardListeners() {
        // Selecionar dispositivo
        document.querySelectorAll('.device-select').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const deviceId = e.target.dataset.deviceId;
                this.selectDevice(deviceId);
            });
        });

        // Informações do dispositivo
        document.querySelectorAll('.device-info').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const deviceId = e.target.dataset.deviceId;
                this.showDeviceInfo(deviceId);
            });
        });

        // Remover dispositivo
        document.querySelectorAll('.device-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const deviceId = e.target.dataset.deviceId;
                this.deleteDevice(deviceId);
            });
        });
    }

    /**
     * Seleciona dispositivo
     */
    selectDevice(deviceId) {
        this.selectedDevice = deviceId;
        this.renderDevicesList();
        
        const device = this.devices.get(deviceId);
        if (device) {
            window.notificationSystem.info(`Dispositivo selecionado: ${device.model}`);
            
            // Salvar na sessão
            sessionStorage.setItem('selected_device', deviceId);
            
            // Emitir evento
            document.dispatchEvent(new CustomEvent('device-selected', { detail: device }));
        }
    }

    /**
     * Mostra informações detalhadas do dispositivo
     */
    async showDeviceInfo(deviceId) {
        const device = this.devices.get(deviceId);
        if (!device) return;

        const modalHtml = `
            <div class="modal fade" id="deviceInfoModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Informações do Dispositivo</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <pre>${JSON.stringify(device, null, 2)}</pre>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Adicionar modal ao DOM
        const existingModal = document.getElementById('deviceInfoModal');
        if (existingModal) existingModal.remove();
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('deviceInfoModal'));
        modal.show();
    }

    /**
     * Remove dispositivo
     */
    async deleteDevice(deviceId) {
        if (!confirm('Tem certeza que deseja remover este dispositivo?')) {
            return;
        }

        try {
            await window.apiClient.delete(`/device/${deviceId}`);
            
            this.devices.delete(deviceId);
            this.renderDevicesList();
            this.updateStats();
            
            window.notificationSystem.success('Dispositivo removido com sucesso');
        } catch (error) {
            console.error('Erro ao remover dispositivo:', error);
            window.notificationSystem.error('Erro ao remover dispositivo');
        }
    }

    /**
     * Filtra dispositivos por texto
     */
    filterDevices(searchText) {
        const text = searchText.toLowerCase();
        
        document.querySelectorAll('.device-card').forEach(card => {
            const cardText = card.textContent.toLowerCase();
            const shouldShow = cardText.includes(text);
            card.closest('.col-md-6').style.display = shouldShow ? '' : 'none';
        });
    }

    /**
     * Filtra dispositivos por status
     */
    filterByStatus(status) {
        if (!status || status === 'all') {
            document.querySelectorAll('.device-card').forEach(card => {
                card.closest('.col-md-6').style.display = '';
            });
            return;
        }

        document.querySelectorAll('.device-card').forEach(card => {
            const deviceId = card.closest('[data-device-id]').dataset.deviceId;
            const device = this.devices.get(deviceId);
            const shouldShow = device && device.status === status;
            card.closest('.col-md-6').style.display = shouldShow ? '' : 'none';
        });
    }

    /**
     * Destaca dispositivo
     */
    highlightDevice(deviceId, type = 'info') {
        const card = document.querySelector(`[data-device-id="${deviceId}"] .device-card`);
        if (card) {
            card.classList.add(`border-${type}`);
            setTimeout(() => {
                card.classList.remove(`border-${type}`);
            }, 3000);
        }
    }

    /**
     * Atualiza estatísticas
     */
    updateStats() {
        const total = this.devices.size;
        const online = Array.from(this.devices.values()).filter(d => d.status === 'online').length;
        const offline = total - online;

        // Atualizar elementos no DOM se existirem
        this.updateStatElement('total-devices', total);
        this.updateStatElement('online-devices', online);
        this.updateStatElement('offline-devices', offline);
    }

    /**
     * Atualiza elemento de estatística
     */
    updateStatElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * Inicia auto-refresh
     */
    startAutoRefresh() {
        this.updateInterval = setInterval(() => {
            this.loadDevices();
        }, 30000); // 30 segundos
    }

    /**
     * Para auto-refresh
     */
    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    /**
     * Obtém dispositivo selecionado
     */
    getSelectedDevice() {
        return this.devices.get(this.selectedDevice);
    }

    /**
     * Obtém todos os dispositivos
     */
    getAllDevices() {
        return Array.from(this.devices.values());
    }

    /**
     * Obtém dispositivos online
     */
    getOnlineDevices() {
        return Array.from(this.devices.values()).filter(d => d.status === 'online');
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.devicesManager = new DevicesManager();
});

