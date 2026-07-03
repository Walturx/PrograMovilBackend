import sqlite3
import os
import sys

# En Windows la consola usa cp1252 y truena con los emojis de los prints; forzamos UTF-8.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

db_path = "app.db"
migrations_dir = "migrations" 

print("Conectando a la base de datos...")
conn = sqlite3.connect(db_path)

# 💡 CONFIGURACIÓN CLAVE: Desactivamos la restricción de llaves foráneas de forma global.
# Esto permite que SQLite procese tus 19 archivos de migración y fills sin trabarse
# por los IDs cruzados (como 's1' o 'htl-1').
conn.execute("PRAGMA foreign_keys = OFF;")
cursor = conn.cursor()

# =====================================================================
# 1. TABLA DE CONTROL DE MIGRACIONES (schema_migrations)
# =====================================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY
);
""")
conn.commit()

# =====================================================================
# 2. OBTENER MIGRACIONES YA EJECUTADAS
# =====================================================================
cursor.execute("SELECT version FROM schema_migrations;")
executed_migrations = {row[0] for row in cursor.fetchall()}

# =====================================================================
# 3. LEER Y EJECUTAR LOS 19 ARCHIVOS EN ORDEN ALFABÉTICO
# =====================================================================
if os.path.exists(migrations_dir):
    files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
    
    new_migrations_executed = 0
    
    for file in files:
        if file in executed_migrations:
            print(f"⏩ Saltando (ya ejecutada): {file}")
            continue
            
        file_path = os.path.join(migrations_dir, file)
        print(f"🚀 Ejecutando: {file}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Aislar el bloque de migración ascendente (UP)
            if "-- migrate:down" in content:
                sql_up_part = content.split("-- migrate:down")[0]
            else:
                sql_up_part = content
            
            sql_up_part = sql_up_part.replace("-- migrate:up", "").strip()
                
            try:
                # Ejecutar scripts de estructura o tus bloques 'fill' nativos
                cursor.executescript(sql_up_part)
                
                # Registrar en la tabla de control de versiones
                cursor.execute("INSERT INTO schema_migrations (version) VALUES (?);", (file,))
                conn.commit()
                new_migrations_executed += 1
                
            except sqlite3.Error as e:
                print(f"❌ Error fatal en el archivo {file}: {e}")
                print("Haciendo rollback de la transacción...")
                conn.rollback()
                conn.close()
                exit(1)
                
    print("====================================")
    if new_migrations_executed > 0:
        print(f"¡Éxito! Se procesaron {new_migrations_executed} archivos de migración y datos en limpio.")
    else:
        print("La base de datos ya cuenta con todas tus estructuras y datos actualizados.")
else:
    print(f"❌ Error: No se encontró la carpeta de destino en: {migrations_dir}")

# =====================================================================
# 4. REACTIVACIÓN DE LLAVES FORÁNEAS PARA LA APP
# =====================================================================
try:
    # Una vez que la base de datos se pobló por completo, encendemos el modo estricto
    # para que las transacciones en caliente desde Flutter mantengan la integridad.
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
except sqlite3.Error as e:
    print(f"⚠️ Advertencia al re-establecer las llaves foráneas: {e}")

conn.close()
print("Conexión cerrada. Entorno relacional configurado y listo para pruebas.")