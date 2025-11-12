# 🧪 GUIA DE TESTES - ARGUS v2.0

**Data**: 2025-10-27  
**Versão**: 1.0

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Testes Backend Python](#testes-backend-python)
3. [Testes Android](#testes-android)
4. [Executando Testes](#executando-testes)
5. [Interpretando Resultados](#interpretando-resultados)

---

## 🎯 VISÃO GERAL

Este projeto possui uma suite completa de testes dividida em:

### Backend Python
- ✅ **Testes Unitários** - Funções isoladas (crypto, models)
- ✅ **Testes de Integração** - APIs e fluxos completos
- ✅ **Testes de Segurança** - SQL Injection, XSS, Auth, CORS
- ✅ **Cobertura de Código** - Relatórios HTML e terminal

### Android
- 📝 **Testes Instrumentados** - UI e serviços
- 📝 **Testes Unitários** - Lógica de negócio
- 📝 **Testes de Integração** - Comunicação com C2

---

## 🐍 TESTES BACKEND PYTHON

### Estrutura de Testes

```
backend/tests/
├── __init__.py
├── conftest.py                    # Fixtures pytest
├── pytest.ini                     # Configuração pytest
├── requirements_test.txt          # Dependências de teste
├── run_tests.py                   # Script executor
│
├── unit/                          # Testes unitários
│   ├── __init__.py
│   ├── test_encryption.py         # Testes de criptografia
│   └── test_models.py             # Testes de models
│
├── integration/                   # Testes de integração
│   ├── __init__.py
│   └── test_api_devices.py        # Testes de APIs
│
└── security/                      # Testes de segurança
    ├── __init__.py
    └── test_security.py           # SQL Injection, XSS, etc
```

### Instalação de Dependências

```bash
cd backend
pip install -r requirements.txt
pip install -r tests/requirements_test.txt
```

### Executar Todos os Testes

```bash
# Opção 1: Script Python (recomendado)
python tests/run_tests.py

# Opção 2: Pytest direto
pytest tests/ -v

# Opção 3: Com cobertura
pytest tests/ --cov=. --cov-report=html
```

### Executar Testes Específicos

```bash
# Apenas testes unitários
pytest tests/unit/ -v

# Apenas testes de criptografia
pytest tests/unit/test_encryption.py -v

# Teste específico
pytest tests/unit/test_encryption.py::TestEncryptionBasics::test_encrypt_decrypt_simple_string -v

# Apenas testes de segurança
pytest tests/security/ -v

# Apenas testes de integração
pytest tests/integration/ -v
```

### Testes com Marcadores

```bash
# Testes rápidos
pytest -m "not slow" -v

# Apenas testes de segurança
pytest -m security -v
```

---

## 📊 COBERTURA DE CÓDIGO

### Gerar Relatório de Cobertura

```bash
# Relatório no terminal
pytest tests/ --cov=. --cov-report=term

# Relatório HTML (recomendado)
pytest tests/ --cov=. --cov-report=html

# Abrir relatório HTML
# Windows:
start htmlcov/index.html

# Linux/Mac:
open htmlcov/index.html
```

### Interpretar Cobertura

- **90-100%**: Excelente ✅
- **80-89%**: Bom 👍
- **70-79%**: Aceitável ⚠️
- **<70%**: Precisa melhorar ❌

---

## 📱 TESTES ANDROID

### Estrutura Recomendada

```
android/src/
├── test/                          # Testes unitários
│   └── java/com/argus/rat/
│       ├── EncryptionUtilsTest.java
│       ├── DeviceIdentifierTest.java
│       └── DataExfiltrationManagerTest.java
│
└── androidTest/                   # Testes instrumentados
    └── java/com/argus/rat/
        ├── C2ClientTest.java
        ├── WebSocketClientTest.java
        └── PersistentServiceTest.java
```

### Testes Unitários Android (JUnit)

**Exemplo**: `EncryptionUtilsTest.java`

```java
package com.argus.rat;

import org.junit.Test;
import static org.junit.Assert.*;

public class EncryptionUtilsTest {
    
    @Test
    public void testEncryptDecrypt() throws Exception {
        String original = "Test message";
        String keyString = "test_key_123";
        
        String encrypted = EncryptionUtils.encrypt(original, keyString);
        String decrypted = EncryptionUtils.decrypt(encrypted, keyString);
        
        assertEquals(original, decrypted);
        assertNotEquals(original, encrypted);
    }
    
    @Test
    public void testSHA256Hash() throws Exception {
        String data = "Test data";
        String hash = EncryptionUtils.sha256(data);
        
        assertNotNull(hash);
        assertEquals(64, hash.length());  // SHA-256 = 64 hex chars
    }
    
    @Test(expected = Exception.class)
    public void testDecryptWithWrongKey() throws Exception {
        String encrypted = EncryptionUtils.encrypt("data", "key1");
        EncryptionUtils.decrypt(encrypted, "key2");  // Deve lançar exceção
    }
}
```

### Executar Testes Android

```bash
# Testes unitários (locais)
./gradlew test

# Testes instrumentados (requerem dispositivo/emulador)
./gradlew connectedAndroidTest

# Relatório de cobertura
./gradlew jacocoTestReport
```

### Testes Instrumentados

**Exemplo**: `C2ClientTest.java`

```java
package com.argus.rat;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class C2ClientTest {
    
    @Test
    public void testC2ClientInitialization() {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        C2Client client = C2Client.getInstance(context);
        
        assertNotNull(client);
    }
    
    @Test
    public void testDeviceRegistration() throws Exception {
        // Test device registration flow
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        C2Client client = C2Client.getInstance(context);
        
        // Setup mock server
        // Test registration
        // Assert results
    }
}
```

---

## 🧪 TIPOS DE TESTES

### 1. Testes Unitários

**O que testam**: Funções/métodos isolados

**Exemplo**:
```python
def test_encrypt_decrypt_simple_string():
    original = "Hello"
    encrypted = EncryptionUtils.encrypt(original)
    decrypted = EncryptionUtils.decrypt(encrypted)
    assert decrypted == original
```

**Quando usar**: Sempre! Para toda função importante.

---

### 2. Testes de Integração

**O que testam**: Interação entre componentes

**Exemplo**:
```python
def test_device_registration_flow(client):
    # 1. Registrar device
    response = client.post('/api/device/register', json={...})
    assert response.status_code == 200
    
    # 2. Verificar no banco
    device = Device.query.filter_by(device_id='test').first()
    assert device is not None
```

**Quando usar**: Para fluxos completos e APIs.

---

### 3. Testes de Segurança

**O que testam**: Vulnerabilidades

**Exemplo**:
```python
@pytest.mark.parametrize('malicious_input', [
    "' OR '1'='1",
    "'; DROP TABLE devices; --",
])
def test_sql_injection(client, malicious_input):
    response = client.get(f'/api/device/{malicious_input}')
    assert response.status_code < 500  # Não deve quebrar
```

**Quando usar**: Sempre! Especialmente em inputs de usuário.

---

## 📊 RELATÓRIOS

### Relatório de Testes

Após executar `pytest`, você verá:

```
================================ test session starts =================================
platform linux -- Python 3.10.0, pytest-7.4.3, pluggy-1.3.0
collected 87 items

tests/unit/test_encryption.py::TestEncryptionBasics::test_encrypt_decrypt ... PASSED
tests/unit/test_encryption.py::TestEncryptionBasics::test_encrypt_unicode ... PASSED
...

============================== 87 passed in 12.34s ===============================
```

### Relatório de Cobertura

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
crypto/encryption.py                 85      5    94%
database/backend/models.py          142     12    92%
server_integrated.py                318     89    72%
-----------------------------------------------------
TOTAL                               845    156    82%
```

---

## 🐛 DEBUGGING TESTES

### Teste Falhando

```bash
# Ver traceback completo
pytest tests/unit/test_encryption.py -v --tb=long

# Parar no primeiro erro
pytest tests/ -x

# Ver print() nos testes
pytest tests/ -s

# Debug interativo
pytest tests/ --pdb
```

### Logs Durante Testes

```python
import logging

def test_something(caplog):
    caplog.set_level(logging.INFO)
    # ... código que gera logs ...
    assert "expected message" in caplog.text
```

---

## ✅ CHECKLIST ANTES DE COMMIT

- [ ] Todos os testes passando
- [ ] Cobertura > 80%
- [ ] Testes de segurança passando
- [ ] Sem warnings
- [ ] Código lintado

```bash
# Verificar tudo de uma vez
pytest tests/ -v --cov=. --cov-report=term && \
echo "✅ Todos os testes passaram!" || \
echo "❌ Testes falharam!"
```

---

## 🚀 CI/CD INTEGRATION

### GitHub Actions

Criar `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r tests/requirements_test.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

## 📚 RECURSOS

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Android Testing](https://developer.android.com/training/testing)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

## 💡 BOAS PRÁTICAS

1. **Escreva testes ANTES de corrigir bugs**
2. **Um teste = Um conceito**
3. **Nomes descritivos**: `test_should_reject_invalid_device_id`
4. **Fixtures para setup comum**
5. **Mocks para dependências externas**
6. **Testes independentes** (não dependem de ordem)
7. **Rápidos** (< 1 segundo cada)

---

## 🎯 MÉTRICAS DE QUALIDADE

| Métrica | Objetivo | Status Atual |
|---------|----------|--------------|
| Cobertura de Testes | > 80% | A verificar |
| Testes Passando | 100% | A verificar |
| Tempo de Execução | < 60s | A verificar |
| Falhas Intermitentes | 0 | A verificar |

---

**Criado por**: Agente Testador  
**Última Atualização**: 2025-10-27

