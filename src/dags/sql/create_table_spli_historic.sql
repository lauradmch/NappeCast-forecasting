-- Active: 1788958355331@@nappecast.cp4kw66ewhrk.eu-west-3.rds.amazonaws.com@5432@nappecast_data

CREATE TABLE IF NOT EXISTS spli_historic (
    id                                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    horizon                           INT,
    last_train                        DATE NOT NULL,
    date_index                        DATE NOT NULL,
    inserted_at                       TIMESTAMPTZ NOT NULL DEFAULT now(),
    pipeline_run_id                   UUID,
    code_bss                          VARCHAR(50) NOT NULL,       
    bss_id                            VARCHAR(20) NOT NULL,    
    latitude                          DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude                         DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    temperature_2m_max                DOUBLE PRECISION NOT NULL,
    sunrise                           TIMESTAMP NOT NULL,
    sunset                            TIMESTAMP NOT NULL,
    daylight_duration                 DOUBLE PRECISION NOT NULL,
    precipitation_sum                 DOUBLE PRECISION NOT NULL,
    shortwave_radiation_sum           DOUBLE PRECISION NOT NULL,
    et0_fao_evapotranspiration        DOUBLE PRECISION NOT NULL,
    cloud_cover_mean                  DOUBLE PRECISION NOT NULL,
    pressure_msl_mean                 DOUBLE PRECISION NOT NULL,
    wind_speed_10m_mean               DOUBLE PRECISION NOT NULL,
    soil_moisture_0_to_100cm_mean     DOUBLE PRECISION NOT NULL,
    soil_temperature_0_to_100cm_mean  DOUBLE PRECISION NOT NULL,   
    niveau_nappe_eau                  DOUBLE PRECISION NOT NULL,
    mode_obtention                    VARCHAR(100) NOT NULL,     
    nom_producteur                    TEXT NOT NULL,
    p_cum_30d                         DOUBLE PRECISION,
    p_cum_90d                         DOUBLE PRECISION,
    peff_cum_30d                      DOUBLE PRECISION,
    peff_cum_90d                      DOUBLE PRECISION,
    temperature_mean_30d              DOUBLE PRECISION,
    temperature_mean_90d              DOUBLE PRECISION,
    spli                              DOUBLE PRECISION,
    spi                               DOUBLE PRECISION,
    seti                              DOUBLE PRECISION,
    ssti                              DOUBLE PRECISION,
    ssri                              DOUBLE PRECISION,
    swsi                              DOUBLE PRECISION,
    scci                              DOUBLE PRECISION,
    spmi                              DOUBLE PRECISION,
    spei                              DOUBLE PRECISION,
    ssmi                              DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_processed_bss_date
    ON spli_historic (bss_id, date_index);

CREATE INDEX IF NOT EXISTS idx_horizon_last_train
    ON spli_historic (horizon, last_train);

CREATE INDEX IF NOT EXISTS idx_processed_code_bss
    ON spli_historic (code_bss);

CREATE INDEX IF NOT EXISTS idx_processed_inserted_at
    ON spli_historic (inserted_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_processed_bss_date_run
    ON spli_historic (bss_id, date_index, horizon, last_train);

