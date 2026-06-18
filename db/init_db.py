import sqlite3
import os

db_path = "app.db"
migrations_dir = "migrations" # Al estar dentro de /db, la carpeta es directamente migrations

print("Conectando a la base de datos...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Desactivar llaves foráneas temporalmente para limpiar todo sin errores
cursor.execute("PRAGMA foreign_keys = OFF;")

# 2. Obtener todas las tablas existentes (de BiblioUL) y borrarlas para empezar limpio
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = cursor.fetchall()
for table in tables:
    print(f"Borrando tabla antigua de BiblioUL: {table[0]}...")
    cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")

# Reestablecer llaves foráneas
cursor.execute("PRAGMA foreign_keys = ON;")
conn.commit()
print("¡Base de datos de BiblioUL limpiada por completo!")
print("====================================")

# 3. Leer y ejecutar solo la sección 'UP' de cada archivo .sql de hoteles
if os.path.exists(migrations_dir):
    files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
    
    for file in files:
        file_path = os.path.join(migrations_dir, file)
        print(f"Ejecutando nueva migración de hoteles: {file}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Cortar el archivo para ejecutar solo lo que está antes de -- migrate:down
            if "-- migrate:down" in content:
                sql_up_part = content.split("-- migrate:down")[0]
            else:
                sql_up_part = content
                
            try:
                cursor.executescript(sql_up_part)
            except sqlite3.Error as e:
                print(f"❌ Error en el archivo {file}: {e}")
                conn.rollback()
                conn.close()
                exit(1)
                
    conn.commit()
    print("====================================")
    print("¡Felicidades! Tu 'app.db' ahora está limpia y tiene los datos del nuevo sistema de hoteles.")
else:
    print(f"❌ No se encontró la carpeta de migraciones en: {migrations_dir}")

conn.close()