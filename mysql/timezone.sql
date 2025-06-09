-- MySQL timezone tables
CREATE TABLE IF NOT EXISTS time_zone (
    Time_zone_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    Use_leap_seconds ENUM('Y', 'N') NOT NULL DEFAULT 'N',
    PRIMARY KEY (Time_zone_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS time_zone_name (
    Name CHAR(64) NOT NULL,
    Time_zone_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (Name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS time_zone_transition (
    Time_zone_id INT UNSIGNED NOT NULL,
    Transition_time BIGINT NOT NULL,
    Transition_type_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (Time_zone_id, Transition_time)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS time_zone_transition_type (
    Time_zone_id INT UNSIGNED NOT NULL,
    Transition_type_id INT UNSIGNED NOT NULL,
    Offset INT NOT NULL,
    Is_DST TINYINT NOT NULL,
    Abbreviation CHAR(8) NOT NULL,
    PRIMARY KEY (Time_zone_id, Transition_type_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS time_zone_leap_second (
    Transition_time BIGINT NOT NULL,
    Correction INT NOT NULL,
    PRIMARY KEY (Transition_time)
) ENGINE=InnoDB;