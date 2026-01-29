IF DB_ID('catalogo') IS NULL
BEGIN
    CREATE DATABASE catalogo;
END
GO

USE catalogo;
GO

IF OBJECT_ID('dbo.dataset_snapshot', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dataset_snapshot (
        dataset_id NVARCHAR(50) NOT NULL PRIMARY KEY,
        title NVARCHAR(200) NOT NULL,
        description NVARCHAR(1000) NULL,
        owner NVARCHAR(200) NULL,
        tags NVARCHAR(400) NULL,
        url NVARCHAR(500) NULL,
        modified_at DATETIME2 NULL
    );
END
ELSE
BEGIN
    DELETE FROM dbo.dataset_snapshot;
END
GO

INSERT INTO dbo.dataset_snapshot (dataset_id, title, description, owner, tags, url, modified_at)
VALUES
('ds_001', 'catalogo_a', '', 'equipo_a', 'open,metadata', 'https://example.org/a', '2025-12-18T10:30:00Z'),
('ds_002', 'catalogo_b', 'metadatos basicos', 'equipo_b', 'dcat,open', 'https://example.org/b', '2025-12-18T10:31:00Z'),
('ds_003', 'catalogo_c', 'metadatos base', 'equipo_c', 'catalogo', 'https://example.org/c', '2025-12-18T10:32:00Z');
GO