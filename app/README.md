# Guía de colaboración – Flujo de desarrollo de funcionalidades

Este documento explica el flujo recomendado para implementar nuevas funcionalidades en el proyecto.  
El objetivo es mantener una arquitectura clara, modular y sostenible conforme el sistema crezca.

---

## 1. Punto de partida: los modelos

Todas las funcionalidades deben partir del análisis de los **modelos existentes en la base de datos**:

- Identificar qué entidades están relacionadas.
- Verificar si los atributos necesarios ya existen.
- Si es necesario añadir nuevos campos, primero solicitar la aprobación del equipo (ver documento *¿Cómo colaborar?*).

---

## 2. Definición de Schemas

A partir de los modelos, se deben definir los **schemas necesarios en la carpeta `schemas/`**:

- Utilizar `BaseModel` de **Pydantic**.
- Crear schemas para:
  - Solicitud de datos (Create, Update).
  - Respuesta del servidor (Response, ListResponse si aplica).
  - Modelos de lectura directa desde la base de datos (schema con `from_attributes=True`).

Estos schemas permiten validar la entrada y salida de datos de la API.

---

## 3. Controladores (carpeta `controllers/`)

Los controladores deben limitarse a:

- Declarar rutas y métodos HTTP.
- Validar la entrada mediante schemas.
- Delegar toda la lógica al servicio correspondiente.
- Manejar respuestas y códigos de estado.

---

## 4. Servicios (carpeta `services/`)

La carpeta `services/` debe contener la **lógica de negocio** para cada controlador, incluyendo:

- Procesamiento de datos.
- Reglas de negocio.
- Interacción con la base de datos a través de modelos o repositorios.
- Cualquier función que implemente la funcionalidad principal sin preocuparse por detalles de API o presentación.

---

## 5. Ejemplo de colaboración

Para facilitar la colaboración y el estándar de implementación, en el repositorio está incluido un archivo llamado `ejemplo.py`. Este ejemplo muestra cómo deben colaborar las diferentes capas (modelos, schemas, controladores y servicios) de forma coherente y modular.

Se recomienda revisarlo para entender la estructura y los patrones de diseño que se deben seguir en nuevas funcionalidades.

---

> Mantener este flujo ayudará a conservar la calidad y escalabilidad del proyecto conforme crezca.
