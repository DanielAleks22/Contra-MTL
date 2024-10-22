DROP TABLE IF EXISTS violations;

CREATE TABLE  violations (
    id_poursuite TEXT PRIMARY KEY,
    business_id TEXT,
    date DATE,
    description TEXT,
    adresse TEXT,
    date_jugement DATE,
    etablissement TEXT,
    montant REAL,
    proprietaire TEXT,
    ville TEXT,
    statut TEXT,
    date_statut DATE,
    categorie TEXT
);
