PRAGMA foreign_keys = ON;

-- =====================================================================
-- SoporTI · Esquema de la base de datos
-- =====================================================================

-- Organizaciones clientes (pymes, colegios, servicios TI).
-- Cada organización solo ve sus propios datos (plataforma multiorganización).
CREATE TABLE IF NOT EXISTS organizaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL DEFAULT 'Pyme'
        CHECK (tipo IN ('Pyme', 'Colegio', 'Servicio TI')),
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Usuarios del sistema.
--   solicitante: reporta fallas (no inicia sesión)
--   tecnico:     atiende tickets y alertas
--   encargado:   encargado TI de la organización (todo lo anterior + equipos e indicadores)
--   admin:       equipo SoporTI (organizaciones, cuentas y control del proyecto)
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organizacion_id INTEGER,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'solicitante'
        CHECK (rol IN ('solicitante', 'tecnico', 'encargado', 'admin')),
    usuario TEXT UNIQUE,
    clave_hash TEXT,
    email TEXT,
    telefono TEXT,

    FOREIGN KEY (organizacion_id)
        REFERENCES organizaciones(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

-- Inventario de equipos. El código se imprime como código QR.
CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organizacion_id INTEGER NOT NULL,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'Computador'
        CHECK (tipo IN ('Computador', 'Notebook', 'Impresora', 'Proyector', 'Red', 'Otro')),
    marca TEXT,
    modelo TEXT,
    numero_serie TEXT,
    ubicacion TEXT,
    fecha_compra TEXT,
    estado TEXT NOT NULL DEFAULT 'Activo'
        CHECK (estado IN ('Activo', 'En reparación', 'Dado de baja')),
    fecha_baja TEXT,
    motivo_baja TEXT,

    FOREIGN KEY (organizacion_id)
        REFERENCES organizaciones(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organizacion_id INTEGER NOT NULL,

    -- Código aleatorio para que el solicitante siga su ticket sin iniciar sesión
    codigo_seguimiento TEXT NOT NULL UNIQUE,

    titulo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prioridad TEXT NOT NULL
        CHECK (prioridad IN ('Baja', 'Media', 'Alta')),
    estado TEXT NOT NULL DEFAULT 'Nuevo'
        CHECK (estado IN ('Nuevo', 'En proceso', 'Resuelto', 'Cerrado')),
    solicitante_id INTEGER NOT NULL,
    responsable_id INTEGER,
    categoria_id INTEGER NOT NULL,
    equipo_id INTEGER,

    -- Sugerencia del clasificador (K6 Precisión IA)
    categoria_sugerida_id INTEGER,
    prioridad_sugerida TEXT,
    confianza_ia REAL,

    -- Cierre (K5 TPR) y solución aplicada
    fecha_cierre TEXT,
    solucion TEXT,

    -- Encuesta de satisfacción al cierre, nota de 1 a 5 (K8 CSAT)
    satisfaccion INTEGER
        CHECK (satisfaccion BETWEEN 1 AND 5),

    -- Evita enviar dos veces el aviso del 80 % del plazo
    aviso_sla_enviado INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (organizacion_id)
        REFERENCES organizaciones(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (solicitante_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (responsable_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    FOREIGN KEY (categoria_id)
        REFERENCES categorias(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (equipo_id)
        REFERENCES equipos(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    FOREIGN KEY (categoria_sugerida_id)
        REFERENCES categorias(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS cambios_ticket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    fecha_cambio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    campo TEXT NOT NULL
        CHECK (campo IN ('estado', 'responsable', 'categoria', 'prioridad')),
    valor_anterior TEXT,
    valor_nuevo TEXT,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Alertas preventivas por equipo
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER NOT NULL,
    motivo TEXT NOT NULL,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_limite TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'Pendiente'
        CHECK (estado IN ('Pendiente', 'Revisada')),
    fecha_revision TEXT,
    aviso_vencida_enviado INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (equipo_id)
        REFERENCES equipos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Incidencias que llegaron por otros medios (WhatsApp, correo, verbal).
-- Las registra el encargado y sirven para calcular K3 Adopción.
CREATE TABLE IF NOT EXISTS incidencias_externas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organizacion_id INTEGER NOT NULL,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    canal TEXT NOT NULL
        CHECK (canal IN ('WhatsApp', 'Correo', 'Verbal', 'Otro')),
    descripcion TEXT NOT NULL,

    FOREIGN KEY (organizacion_id)
        REFERENCES organizaciones(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Base de soluciones frecuentes de cada organización
CREATE TABLE IF NOT EXISTS soluciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organizacion_id INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    pasos TEXT NOT NULL,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (organizacion_id)
        REFERENCES organizaciones(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (categoria_id)
        REFERENCES categorias(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- Control semanal del proyecto (lo registra el Jefe de Proyecto):
-- K1 Avance del plan, K2 Desviación presupuestaria y K9 Disponibilidad.
CREATE TABLE IF NOT EXISTS mediciones_semanales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semana_inicio TEXT NOT NULL UNIQUE,
    tareas_planificadas INTEGER NOT NULL CHECK (tareas_planificadas >= 0),
    tareas_terminadas INTEGER NOT NULL CHECK (tareas_terminadas >= 0),
    costo_presupuestado INTEGER NOT NULL CHECK (costo_presupuestado >= 0),
    costo_real INTEGER NOT NULL CHECK (costo_real >= 0),
    horas_totales REAL NOT NULL CHECK (horas_totales >= 0),
    horas_en_linea REAL NOT NULL CHECK (horas_en_linea >= 0)
);

-- Datos básicos

INSERT OR IGNORE INTO categorias (id, nombre) VALUES
    (1, 'Hardware'),
    (2, 'Software'),
    (3, 'Conectividad'),
    (4, 'Por clasificar');
