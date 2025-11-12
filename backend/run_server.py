#!/usr/bin/env python3
"""
Script de inicialização do servidor de gerenciamento Android
"""

import os
import sys
from server_integrated import app, socketio

def check_dependencies():
    """Verificar se todas as dependências estão instaladas"""
    try:
        import flask
        import flask_socketio
        # import eventlet
        print("✓ Todas as dependências estão instaladas")
        return True
    except ImportError as e:
        print(f"✗ Dependência faltando: {e}")
        print("Instale as dependências com: pip install -r requirements.txt")
        return False

def create_upload_directory():
    """Criar diretório de uploads se não existir"""
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"✓ Diretório de uploads criado: {upload_dir}")
    else:
        print(f"✓ Diretório de uploads já existe: {upload_dir}")

def print_banner():
    """Imprimir banner do sistema"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                 SISTEMA DE GERENCIAMENTO ANDROID            ║
║                      SERVIDOR BACK-END                      ║
╚══════════════════════════════════════════════════════════════╝

⚡ Funcionalidades:
   • Dashboard em tempo real
   • Gerenciamento de dispositivos
   • Comandos remotos
   • Upload de payloads
   • Sistema de logs
   • WebSocket para comunicação

🔐 Credenciais padrão:
   • Usuário: admin
   • Senha: admin123

⚠️  ALTERE AS CREDENCIAIS EM PRODUÇÃO!
"""
    print(banner)

def main():
    """Função principal"""
    print_banner()
    
    # Verificar dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Criar diretórios necessários
    create_upload_directory()
    
    # Configurações do servidor
    host = '0.0.0.0'
    port = 5000
    debug = True
    
    print(f"🚀 Iniciando servidor em http://{host}:{port}")
    print("📱 Acesse a interface web no navegador")
    print("⏹️  Pressione Ctrl+C para parar o servidor")
    print("-" * 60)
    
    try:
        # Iniciar servidor
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor parado pelo usuário")
    except Exception as e:
        print(f"\n\n💥 Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()