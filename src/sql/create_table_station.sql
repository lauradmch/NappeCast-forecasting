-- Active: 1788958355331@@nappecast.cp4kw66ewhrk.eu-west-3.rds.amazonaws.com@5432@nappecast_data

CREATE TABLE IF NOT EXISTS station (
    id                                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    inserted_at                         TIMESTAMPTZ NOT NULL DEFAULT now(),
    code_bss                            VARCHAR(50) NOT NULL,       
    urn_bss                             TEXT,
    date_debut_mesure                   DATE,
    date_fin_mesure                     DATE,
    code_commune_insee                  VARCHAR(5),
    nom_commune                         TEXT,
    longitude                           DOUBLE PRECISION,
    latitude                            DOUBLE PRECISION,
    codes_bdlisa                        TEXT,  
    urns_bdlisa                         TEXT,
    geometry                            TEXT,   
    bss_id                              VARCHAR(30),
    altitude_station                    NUMERIC(10, 2),
    nb_mesures_piezo                    INTEGER,
    code_departement                    VARCHAR(3),
    nom_departement                     TEXT,
    libelle_pe                          TEXT,
    profondeur_investigation            NUMERIC(10, 2),
    codes_masse_eau_edl                 TEXT,
    noms_masse_eau_edl                  TEXT,
    urns_masse_eau_edl                  TEXT,
    date_maj                            TIMESTAMPTZ 
);

CREATE INDEX IF NOT EXISTS idx_station_code_bss_date_index
    ON station (code_bss, date_index);

CREATE INDEX IF NOT EXISTS idx_station_inserted_at
    ON station (inserted_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_station_code_bss
    ON station (code_bss);

