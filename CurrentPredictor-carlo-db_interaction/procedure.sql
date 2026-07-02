-- 1. Rimuovo la tabella se esisteva una versione parziale o precedente per evitare conflitti
DROP TABLE IF EXISTS anomalies CASCADE;
 
-- 2. Creazione della tabella anomalies con l'ordine richiesto: prima timestamp e poi variable_id
CREATE TABLE anomalies (
    timestamp TIMESTAMPTZ NOT NULL,
    variable_id INTEGER NOT NULL,
    
    -- Chiave primaria composta invertita: prima timestamp e poi variable_id
    PRIMARY KEY (timestamp, variable_id),
    
    -- Vincolo di chiave esterna (Foreign Key) verso la tabella master delle variabili
    CONSTRAINT fk_anomalies_variable
        FOREIGN KEY (variable_id)
        REFERENCES variables(id)
        ON DELETE CASCADE
);
 
-- 3. Creazione dell'indice dedicato per rendere velocissime le query di ricerca e i JOIN
CREATE INDEX IF NOT EXISTS anomalies_timestamp_variable_idx
    ON anomalies (timestamp DESC, variable_id DESC);