-- Migrazione database vvf_turno_b per supporto bot Telegram
-- Eseguire una sola volta su phpMyAdmin o MySQL CLI

ALTER TABLE `vigili`
  ADD COLUMN `telegram_id`        BIGINT UNSIGNED UNIQUE DEFAULT NULL   AFTER `attivo`,
  ADD COLUMN `odt_label`          VARCHAR(60)            DEFAULT NULL   AFTER `telegram_id`,
  ADD COLUMN `email`              VARCHAR(120)           DEFAULT NULL   AFTER `odt_label`,
  ADD COLUMN `email_password_enc` TEXT                   DEFAULT NULL   AFTER `email`,
  ADD COLUMN `telefono`           VARCHAR(20)            DEFAULT NULL   AFTER `email_password_enc`,
  ADD COLUMN `ruolo`              ENUM('pompiere','fureria') NOT NULL DEFAULT 'pompiere' AFTER `telefono`;

-- Richieste ferie gestite dal bot (workflow pending/approved/rejected)
CREATE TABLE IF NOT EXISTS `bot_requests` (
  `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `vigile_id`      INT UNSIGNED NOT NULL,
  `data_richiesta` DATE NOT NULL,
  `tipo_turno`     ENUM('D','N','DN') NOT NULL,
  `stato`          ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  `created_at`     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `processed_at`   DATETIME DEFAULT NULL,
  `note_rifiuto`   VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_req` (`vigile_id`, `data_richiesta`, `tipo_turno`),
  KEY `fk_br_vigile` (`vigile_id`),
  CONSTRAINT `bot_requests_ibfk_1` FOREIGN KEY (`vigile_id`) REFERENCES `vigili` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Giorni salto tracciati dal bot
CREATE TABLE IF NOT EXISTS `bot_salto` (
  `id`        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `vigile_id` INT UNSIGNED NOT NULL,
  `data`      DATE NOT NULL,
  `tipo`      ENUM('D','N') NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_salto` (`vigile_id`, `data`, `tipo`),
  CONSTRAINT `bot_salto_ibfk_1` FOREIGN KEY (`vigile_id`) REFERENCES `vigili` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
