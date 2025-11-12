"""
Script de inicialização do banco de dados
"""

import os
import sys

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config import get_config
from database.backend.database_manager import DatabaseManager

def init_database(reset=False):
    """Inicializa o banco de dados"""
    
    # Criar aplicação Flask temporária
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # Inicializar DatabaseManager
    db_manager = DatabaseManager(app)
    
    with app.app_context():
        if reset:
            print("⚠️  ATENÇÃO: Resetando banco de dados...")
            confirmation = input("Tem certeza? Todos os dados serão perdidos! (digite 'SIM' para confirmar): ")
            if confirmation == 'SIM':
                db_manager.reset_database()
                print("✅ Banco de dados resetado com sucesso!")
            else:
                print("❌ Operação cancelada.")
                return
        else:
            print("📦 Criando tabelas do banco de dados...")
            db_manager.create_tables()
            print("✅ Tabelas criadas com sucesso!")
            
            print("👤 Criando dados padrão...")
            try:
                db_manager.create_default_data()
                print("✅ Dados padrão criados com sucesso!")
            except Exception as e:
                print(f"ℹ️  Dados padrão já existem: {e}")
        
        # Verificar saúde do banco
        print("\n🔍 Verificando saúde do banco de dados...")
        health = db_manager.get_health_status()
        
        if health.get('database_connected'):
            print(f"✅ Banco de dados conectado")
            print(f"   Tabelas: {health.get('tables_count')}")
            print(f"   Dispositivos: {health.get('total_devices')}")
            print(f"   Comandos: {health.get('total_commands')}")
            print(f"   Payloads: {health.get('total_payloads')}")
            print(f"   Logs: {health.get('total_logs')}")
            print(f"   Tamanho: {health.get('database_size')}")
        else:
            print(f"❌ Erro ao conectar ao banco: {health.get('error')}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Inicializar banco de dados Argus C2')
    parser.add_argument('--reset', action='store_true', 
                       help='Resetar banco de dados (APAGA TODOS OS DADOS)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   ARGUS C2 - Inicialização do Banco de Dados")
    print("=" * 60)
    
    init_database(reset=args.reset)
    
    print("\n" + "=" * 60)
    print("   Inicialização concluída!")
    print("=" * 60)




