from database.connection import test_connection

# Teste 1: Verificar conexão
print("Testando conexão com PostgreSQL...")
if test_connection():
    print("✅ SUCESSO! Banco conectado!")
else:
    print("❌ FALHA! Verifique as credenciais")
