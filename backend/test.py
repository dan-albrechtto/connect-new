# backend/test.py

from app.models import Base, Usuario
from app.schemas import UsuarioCreate
from database.connection import test_connection

test_connection()
print('✅ TUDO OK - PRONTO PARA ROTAS!')
