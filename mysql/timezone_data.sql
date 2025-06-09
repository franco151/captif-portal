-- Insertion des données de base pour le fuseau horaire Indian/Antananarivo
INSERT INTO time_zone (Time_zone_id, Use_leap_seconds) VALUES (1, 'N');

INSERT INTO time_zone_name (Name, Time_zone_id) VALUES ('Indian/Antananarivo', 1);

-- Insertion des transitions pour Indian/Antananarivo (UTC+3)
INSERT INTO time_zone_transition_type 
(Time_zone_id, Transition_type_id, Offset, Is_DST, Abbreviation) 
VALUES 
(1, 1, 10800, 0, 'EAT');

-- Insertion d'une transition de base
INSERT INTO time_zone_transition 
(Time_zone_id, Transition_time, Transition_type_id) 
VALUES 
(1, -1846293120, 1); 