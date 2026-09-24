-- Active: 1788958355331@@nappecast.cp4kw66ewhrk.eu-west-3.rds.amazonaws.com@5432@nappecast_data

CREATE TABLE IF NOT EXISTS forecast (
    id                                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    horizon                           INT,
    last_train                        DATE NOT NULL,
    ds                        DATE NOT NULL,
    inserted_at                       TIMESTAMPTZ NOT NULL DEFAULT now(),
    code_bss                          VARCHAR(50) NOT NULL,       
    bss_id                            VARCHAR(20) NOT NULL,  
    yhat                              DOUBLE PRECISION,
    yhat_lower                        DOUBLE PRECISION,
    yhat_upper                        DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_forecast_bss_date_ds
    ON forecast (code_bss, ds);

CREATE INDEX IF NOT EXISTS idx_forecast_horizon_last_train
    ON forecast (horizon, last_train);

CREATE INDEX IF NOT EXISTS idx_forecast_code_bss
    ON forecast (code_bss);

CREATE INDEX IF NOT EXISTS idx_forecast_inserted_at
    ON forecast (inserted_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_forecast_code_bss_ds_horizon_last_train
    ON forecast (code_bss, ds, horizon, last_train);

