PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    puede_atender INTEGER NOT NULL DEFAULT 0
        CHECK (puede_atender IN (0, 1))
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS cambios_ticket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    fecha_cambio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    campo TEXT NOT NULL
        CHECK (campo IN ('estado', 'responsable')),
    valor_anterior TEXT,
    valor_nuevo TEXT,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Datos básicos para poder probar el sistema

INSERT OR IGNORE INTO categorias (id, nombre) VALUES
    (1, 'Hardware'),
    (2, 'Software'),
    (3, 'Conectividad');

INSERT OR IGNORE INTO usuarios (id, nombre, puede_atender) VALUES
    (1, 'Usuario de prueba', 0),
    (2, 'Tecnico de prueba', 1);
