# SGRA

Sistema de Gestión de requisitos agiles (SGRA).

## Requisitos Previos

*   Python 3.8+
*   `venv` para entornos virtuales

## Configuración del Entorno

Siga estos pasos en orden cronológico para configurar su entorno de desarrollo local.

### 1. Clonar el Repositorio (Si aún no lo ha hecho)

```bash
git clone <URL_DEL_REPOSITORIO>
cd sgra
```

### 2. Crear y Activar el Entorno Virtual

Es una buena práctica aislar las dependencias del proyecto.

```bash
# Crear el entorno virtual
python -m venv entorno

# Activar en Linux/macOS
source entorno/bin/activate

# Activar en Windows
.\entorno\Scripts\activate
```

### 3. Configurar las Variables de Entorno

Cree un archivo llamado `.env` en la raíz del proyecto. Este archivo es fundamental para la conexión a la base de datos. Copie y pegue el siguiente contenido en él:

```env
DB_HOST=HOST
DB_USER=USER
DB_PASSWORD=PASSWORD
DB_NAME=NAME
DB_PORT=PORT
```

### 4. Instalar Dependencias

Instale todas las dependencias del proyecto y luego instale el paquete actual en modo "editable". Esto permite que los cambios en el código fuente se reflejen inmediatamente sin necesidad de reinstalar.

```bash
# Instalar desde requirements.txt
pip install -r requirements.txt

# Instalar el proyecto en modo editable
pip install -e .
```

## Ejecución de la Aplicación

Una vez completada la configuración, puede iniciar la aplicación con el comando:

```bash
start
```
