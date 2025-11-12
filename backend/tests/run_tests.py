#!/usr/bin/env python3
"""
Script para executar todos os testes do Argus C2
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Executa comando e retorna resultado"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    """Executa suite completa de testes"""
    print("\n" + "="*60)
    print("🧪 ARGUS C2 - SUITE COMPLETA DE TESTES")
    print("="*60 + "\n")
    
    # Mudar para diretório backend
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
    
    results = []
    
    # 1. Testes unitários
    success = run_command(
        'pytest tests/unit/ -v --tb=short',
        'TESTES UNITÁRIOS'
    )
    results.append(('Unitários', success))
    
    # 2. Testes de integração
    success = run_command(
        'pytest tests/integration/ -v --tb=short',
        'TESTES DE INTEGRAÇÃO'
    )
    results.append(('Integração', success))
    
    # 3. Testes de segurança
    success = run_command(
        'pytest tests/security/ -v --tb=short',
        'TESTES DE SEGURANÇA'
    )
    results.append(('Segurança', success))
    
    # 4. Todos os testes com cobertura
    print(f"\n{'='*60}")
    print("📊 EXECUTANDO TODOS OS TESTES COM COBERTURA")
    print(f"{'='*60}\n")
    
    subprocess.run(
        'pytest tests/ -v --cov=. --cov-report=html --cov-report=term',
        shell=True
    )
    
    # Relatório final
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL")
    print("="*60 + "\n")
    
    for test_type, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_type:20s}: {status}")
    
    print("\n" + "="*60)
    print("📁 Relatório de cobertura HTML: htmlcov/index.html")
    print("="*60 + "\n")
    
    # Retornar código de erro se algum teste falhou
    all_passed = all(success for _, success in results)
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

