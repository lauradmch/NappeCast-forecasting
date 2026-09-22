-- Active: 1788958355331@@nappecast.cp4kw66ewhrk.eu-west-3.rds.amazonaws.com@5432@nappecast_data

CREATE TABLE IF NOT EXISTS spli_forecast (
    id                                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    horizon                           INT,
    last_train                        DATE NOT NULL,
    date_index                        DATE NOT NULL,
    inserted_at                       TIMESTAMPTZ NOT NULL DEFAULT now(),
    pipeline_run_id                   UUID,
    code_bss                          VARCHAR(50) NOT NULL,       
    bss_id                            VARCHAR(20) NOT NULL,  
    yhat                              DOUBLE PRECISION,
    yhat_lower                        DOUBLE PRECISION,
    yhat_upper                        DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_processed_bss_date
    ON spli_forecast (bss_id, date_index);

CREATE INDEX IF NOT EXISTS idx_horizon_last_train
    ON spli_forecast (horizon, last_train);

CREATE INDEX IF NOT EXISTS idx_processed_code_bss
    ON spli_forecast (code_bss);

CREATE INDEX IF NOT EXISTS idx_processed_inserted_at
    ON spli_forecast (inserted_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_processed_bss_date_run
    ON spli_forecast (bss_id, date_index, horizon, last_train);

