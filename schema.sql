CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL,
    humidity REAL
);

-- Insert sample data
INSERT INTO sensor_data (temperature, humidity) VALUES (22.5, 45.0);
INSERT INTO sensor_data (temperature, humidity) VALUES (23.0, 50.0);
INSERT INTO sensor_data (temperature, humidity) VALUES (21.5, 55.0);
INSERT INTO sensor_data (temperature, humidity) VALUES (24.0, 60.0);
INSERT INTO sensor_data (temperature, humidity) VALUES (25.5, 65.0);

