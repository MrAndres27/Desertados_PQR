"""Script para inicializar datos básicos del sistema"""
import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models import Role, Permission, PQRSStatus, User
from app.core.security import get_password_hash

def init_roles_and_permissions():
    """Crear roles y permisos iniciales"""
    db = SessionLocal()
    
    try:
        # Crear permisos
        permissions = [
            Permission(name="crear_pqrs", description="Crear PQRS", module="pqrs"),
            Permission(name="ver_pqrs", description="Ver PQRS", module="pqrs"),
            Permission(name="editar_pqrs", description="Editar PQRS", module="pqrs"),
            Permission(name="eliminar_pqrs", description="Eliminar PQRS", module="pqrs"),
            Permission(name="asignar_pqrs", description="Asignar PQRS", module="pqrs"),
            Permission(name="gestionar_usuarios", description="Gestionar usuarios", module="users"),
            Permission(name="ver_dashboard", description="Ver dashboard", module="dashboard"),
            Permission(name="ver_reportes", description="Ver reportes", module="reports"),
            Permission(name="ver_auditoria", description="Ver auditoría", module="audit"),
        ]
        
        for perm in permissions:
            existing = db.query(Permission).filter_by(name=perm.name).first()
            if not existing:
                db.add(perm)
        
        db.commit()
        print("✅ Permisos creados")
        
        # Crear roles
        roles_data = {
            "Administrador": ["crear_pqrs", "ver_pqrs", "editar_pqrs", "eliminar_pqrs", 
                             "asignar_pqrs", "gestionar_usuarios", "ver_dashboard", 
                             "ver_reportes", "ver_auditoria"],
            "Gestor": ["crear_pqrs", "ver_pqrs", "editar_pqrs", "asignar_pqrs", 
                      "ver_dashboard", "ver_reportes"],
            "Supervisor": ["ver_pqrs", "ver_dashboard", "ver_reportes"],
            "Usuario": ["crear_pqrs", "ver_pqrs"]
        }
        
        for role_name, perm_names in roles_data.items():
            role = db.query(Role).filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f"Rol de {role_name}")
                perms = db.query(Permission).filter(Permission.name.in_(perm_names)).all()
                role.permissions = perms
                db.add(role)
        
        db.commit()
        print("✅ Roles creados")
        
        # Crear estados de PQRS
        statuses = [
            PQRSStatus(name="Recibida", description="PQRS recién creada", order=1, is_final=0),
            PQRSStatus(name="En Proceso", description="PQRS en atención", order=2, is_final=0),
            PQRSStatus(name="Resuelta", description="PQRS resuelta", order=3, is_final=0),
            PQRSStatus(name="Cerrada", description="PQRS cerrada", order=4, is_final=1),
            PQRSStatus(name="Cancelada", description="PQRS cancelada", order=5, is_final=1),
        ]
        
        for status in statuses:
            existing = db.query(PQRSStatus).filter_by(name=status.name).first()
            if not existing:
                db.add(status)
        
        db.commit()
        print("✅ Estados de PQRS creados")
        
        # Crear usuario administrador inicial
        admin_role = db.query(Role).filter_by(name="Administrador").first()
        admin = db.query(User).filter_by(username="admin").first()
        
        if not admin:
            admin = User(
                username="admin",
                email="admin@pqrs.com",
                hashed_password=get_password_hash("Admin123!"),
                full_name="Administrador del Sistema",
                is_active=True,
                is_superuser=True,
                role_id=admin_role.id
            )
            db.add(admin)
            db.commit()
            print("✅ Usuario administrador creado")
            print("   Username: admin")
            print("   Password: Admin123!")
        else:
            print("ℹ️  Usuario administrador ya existe")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Inicializando datos del sistema...")
    init_roles_and_permissions()
    print("✅ Inicialización completada")
