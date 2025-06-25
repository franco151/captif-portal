-- Création des tables de fuseaux horaires
CREATE TABLE IF NOT EXISTS time_zone (
  Time_zone_id int unsigned NOT NULL auto_increment,
  Use_leap_seconds enum('Y','N') NOT NULL DEFAULT 'N',
  PRIMARY KEY (Time_zone_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS time_zone_name (
  Name char(64) NOT NULL,
  Time_zone_id int unsigned NOT NULL,
  PRIMARY KEY (Name)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS time_zone_transition (
  Time_zone_id int unsigned NOT NULL,
  Transition_time bigint signed NOT NULL,
  Transition_type_id int unsigned NOT NULL,
  PRIMARY KEY (Time_zone_id, Transition_time)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS time_zone_transition_type (
  Time_zone_id int unsigned NOT NULL,
  Transition_type_id int unsigned NOT NULL,
  Offset int signed NOT NULL DEFAULT 0,
  Is_DST tinyint unsigned NOT NULL DEFAULT 0,
  Abbreviation char(8) NOT NULL DEFAULT '',
  PRIMARY KEY (Time_zone_id, Transition_type_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS time_zone_leap_second (
  Transition_time bigint signed NOT NULL,
  Correction int signed NOT NULL,
  PRIMARY KEY (Transition_time)
) CHARACTER SET utf8mb4;

-- Insertion des données de base
INSERT IGNORE INTO time_zone (Time_zone_id, Use_leap_seconds) VALUES 
(1, 'N'),  -- UTC
(2, 'N');  -- Indian/Antananarivo

INSERT IGNORE INTO time_zone_name (Name, Time_zone_id) VALUES 
('UTC', 1),
('Indian/Antananarivo', 2);

-- Données de transition pour Indian/Antananarivo (UTC+3)
INSERT IGNORE INTO time_zone_transition_type (Time_zone_id, Transition_type_id, Offset, Is_DST, Abbreviation) VALUES
(2, 0, 10800, 0, 'EAT');  -- East Africa Time (UTC+3)

-- Insertion d'une transition initiale pour Indian/Antananarivo
INSERT IGNORE INTO time_zone_transition (Time_zone_id, Transition_time, Transition_type_id) VALUES
(2, -2147483648, 0);  -- Définir le fuseau horaire par défaut