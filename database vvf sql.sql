-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Creato il: Mag 25, 2026 alle 17:53
-- Versione del server: 10.4.32-MariaDB
-- Versione PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `vvf_turno_b`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `abilitazioni`
--

CREATE TABLE `abilitazioni` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `codice` varchar(20) NOT NULL,
  `nome` varchar(60) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `abilitazioni`
--

INSERT INTO `abilitazioni` (`id`, `codice`, `nome`) VALUES
(1, 'NBCR', 'Nucleare Biologico Chimico Radiologico'),
(2, 'SAF_BASICO', 'Speleo Alpino Fluviale — Basico'),
(3, 'SAF_AVANZATO', 'Speleo Alpino Fluviale — Avanzato'),
(4, 'SA', 'Sommozzatore'),
(5, 'SFA', 'Supporto Fluviale Alluvionale'),
(6, 'TAS', 'Topografia Applicata al Soccorso'),
(7, 'MIRT', 'Modulo Intervento Rapido Territoriale'),
(8, 'USAR-L', 'Urban Search And Rescue — Light'),
(9, 'USAR-M', 'Urban Search And Rescue — Medium'),
(10, 'SO', 'Supporto Operativo');

-- --------------------------------------------------------

--
-- Struttura della tabella `assegnazioni`
--

CREATE TABLE `assegnazioni` (
  `id` int(10) UNSIGNED NOT NULL,
  `foglio_id` int(10) UNSIGNED NOT NULL,
  `posizione_id` smallint(5) UNSIGNED NOT NULL,
  `vigile_id` int(10) UNSIGNED NOT NULL,
  `ordine` tinyint(3) UNSIGNED DEFAULT 0,
  `in_straordinario` tinyint(1) DEFAULT 0,
  `note` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `assegnazioni`
--

INSERT INTO `assegnazioni` (`id`, `foglio_id`, `posizione_id`, `vigile_id`, `ordine`, `in_straordinario`, `note`) VALUES
(18, 3, 28, 1, 1, 0, NULL),
(31, 1, 17, 19, 1, 0, NULL),
(32, 1, 18, 13, 1, 0, NULL),
(33, 1, 18, 6, 2, 0, NULL),
(34, 1, 18, 1, 3, 0, NULL),
(35, 1, 22, 10, 1, 0, NULL),
(36, 7, 1, 2, 1, 0, NULL),
(37, 7, 14, 3, 1, 0, NULL),
(38, 7, 14, 4, 2, 0, NULL),
(39, 7, 17, 5, 1, 0, NULL),
(40, 7, 17, 6, 2, 0, NULL),
(41, 7, 23, 7, 1, 0, NULL),
(42, 7, 18, 9, 1, 0, NULL),
(43, 7, 18, 10, 2, 0, NULL),
(44, 7, 19, 11, 1, 0, NULL),
(45, 7, 19, 12, 2, 0, NULL),
(46, 7, 19, 13, 3, 0, NULL),
(47, 7, 21, 14, 1, 0, NULL),
(48, 7, 21, 16, 2, 0, NULL),
(49, 7, 21, 17, 3, 0, NULL),
(50, 7, 20, 18, 1, 0, NULL),
(51, 7, 20, 19, 2, 0, NULL),
(52, 7, 20, 20, 3, 0, NULL),
(53, 8, 1, 1, 1, 0, NULL),
(54, 8, 1, 2, 2, 0, NULL),
(56, 8, 14, 4, 2, 0, NULL),
(57, 8, 17, 5, 1, 0, NULL),
(58, 8, 17, 6, 2, 0, NULL),
(61, 8, 18, 9, 1, 0, NULL),
(63, 8, 19, 11, 1, 0, NULL),
(64, 8, 19, 12, 2, 0, NULL),
(65, 8, 19, 13, 3, 0, NULL),
(69, 8, 20, 18, 1, 0, NULL),
(70, 8, 20, 19, 2, 0, NULL),
(81, 8, 24, 8, 1, 0, NULL),
(82, 8, 21, 15, 1, 0, NULL),
(83, 8, 21, 10, 2, 0, NULL),
(84, 9, 1, 1, 1, 0, NULL),
(85, 9, 1, 2, 2, 0, NULL),
(86, 9, 14, 3, 1, 0, NULL),
(88, 9, 17, 6, 1, 0, NULL),
(89, 9, 23, 7, 1, 0, NULL),
(90, 9, 23, 8, 2, 0, NULL),
(91, 9, 18, 9, 1, 0, NULL),
(92, 9, 19, 11, 1, 0, NULL),
(93, 9, 19, 12, 2, 0, NULL),
(94, 9, 19, 13, 3, 0, NULL),
(95, 9, 21, 14, 1, 0, NULL),
(96, 9, 21, 15, 2, 0, NULL),
(97, 9, 21, 16, 3, 0, NULL),
(98, 9, 20, 18, 1, 0, NULL),
(99, 9, 20, 19, 2, 0, NULL),
(100, 9, 20, 20, 3, 0, NULL),
(101, 9, 14, 4, 2, 0, NULL),
(103, 10, 1, 1, 1, 0, NULL),
(104, 10, 1, 2, 2, 0, NULL),
(105, 10, 14, 4, 1, 0, NULL),
(106, 10, 17, 5, 1, 0, NULL),
(107, 10, 17, 6, 2, 0, NULL),
(108, 10, 23, 7, 1, 0, NULL),
(109, 10, 23, 8, 2, 0, NULL),
(110, 10, 18, 9, 1, 0, NULL),
(111, 10, 18, 10, 2, 0, NULL),
(112, 10, 19, 11, 1, 0, NULL),
(113, 10, 19, 12, 2, 0, NULL),
(114, 10, 19, 13, 3, 0, NULL),
(115, 10, 21, 14, 1, 0, NULL),
(116, 10, 21, 15, 2, 0, NULL),
(117, 10, 21, 16, 3, 0, NULL),
(118, 10, 21, 17, 4, 0, NULL),
(119, 10, 20, 18, 1, 0, NULL),
(120, 10, 20, 19, 2, 0, NULL),
(121, 10, 20, 20, 3, 0, NULL),
(122, 10, 1, 21, 3, 0, NULL),
(123, 10, 1, 22, 4, 0, NULL),
(124, 10, 1, 24, 5, 0, NULL),
(125, 10, 1, 25, 6, 0, NULL),
(128, 11, 14, 3, 1, 0, NULL),
(129, 11, 14, 4, 2, 0, NULL),
(130, 11, 17, 6, 1, 0, NULL),
(131, 11, 23, 7, 1, 0, NULL),
(133, 11, 18, 9, 1, 0, NULL),
(137, 11, 21, 14, 1, 0, NULL),
(138, 11, 21, 15, 2, 0, NULL),
(139, 11, 21, 16, 3, 0, NULL),
(141, 11, 20, 19, 2, 0, NULL),
(142, 11, 20, 20, 3, 0, NULL),
(145, 11, 1, 24, 5, 0, NULL),
(151, 11, 20, 13, 4, 0, NULL),
(152, 11, 20, 12, 5, 0, NULL),
(153, 11, 20, 11, 6, 0, NULL),
(161, 11, 8, 1, 1, 0, NULL),
(167, 11, 4, 22, 1, 0, NULL),
(168, 11, 2, 2, 1, 0, NULL),
(169, 11, 28, 5, 1, 1, NULL),
(171, 11, 24, 8, 1, 0, NULL),
(172, 11, 20, 18, 7, 0, NULL),
(175, 12, 14, 3, 1, 0, NULL),
(176, 12, 14, 4, 2, 0, NULL),
(177, 12, 17, 5, 1, 0, NULL),
(178, 12, 17, 6, 2, 0, NULL),
(179, 12, 23, 7, 1, 0, NULL),
(181, 12, 18, 9, 1, 0, NULL),
(182, 12, 18, 10, 2, 0, NULL),
(183, 12, 19, 11, 1, 0, NULL),
(184, 12, 19, 12, 2, 0, NULL),
(185, 12, 21, 14, 1, 0, NULL),
(186, 12, 21, 15, 2, 0, NULL),
(187, 12, 21, 16, 3, 0, NULL),
(188, 12, 21, 17, 4, 0, NULL),
(189, 12, 20, 18, 1, 0, NULL),
(190, 12, 20, 19, 2, 0, NULL),
(191, 12, 20, 20, 3, 0, NULL),
(192, 12, 1, 21, 3, 0, NULL),
(194, 12, 1, 23, 5, 0, NULL),
(195, 12, 1, 24, 6, 0, NULL),
(197, 12, 2, 2, 1, 0, NULL),
(198, 12, 3, 1, 1, 0, NULL),
(199, 12, 2, 22, 2, 0, NULL),
(200, 12, 4, 25, 1, 0, NULL);

-- --------------------------------------------------------

--
-- Struttura della tabella `assenze`
--

CREATE TABLE `assenze` (
  `id` int(10) UNSIGNED NOT NULL,
  `foglio_id` int(10) UNSIGNED NOT NULL,
  `vigile_id` int(10) UNSIGNED NOT NULL,
  `tipo_assenza_id` tinyint(3) UNSIGNED NOT NULL,
  `sede_distaccata` varchar(20) DEFAULT NULL,
  `data_da` date DEFAULT NULL,
  `data_a` date DEFAULT NULL,
  `nr_turni` tinyint(3) UNSIGNED DEFAULT NULL,
  `note` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `assenze`
--

INSERT INTO `assenze` (`id`, `foglio_id`, `vigile_id`, `tipo_assenza_id`, `sede_distaccata`, `data_da`, `data_a`, `nr_turni`, `note`) VALUES
(4, 8, 17, 3, NULL, NULL, NULL, NULL, NULL),
(10, 8, 16, 3, NULL, NULL, NULL, NULL, NULL),
(15, 8, 3, 3, NULL, NULL, NULL, NULL, NULL),
(16, 8, 7, 1, NULL, NULL, NULL, NULL, NULL),
(20, 12, 8, 1, NULL, NULL, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Struttura della tabella `foglio_furieri`
--

CREATE TABLE `foglio_furieri` (
  `foglio_id` int(10) UNSIGNED NOT NULL,
  `vigile_id` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `fogli_servizio`
--

CREATE TABLE `fogli_servizio` (
  `id` int(10) UNSIGNED NOT NULL,
  `data_servizio` date NOT NULL,
  `tipo_turno` enum('D','N') NOT NULL,
  `salto_riposo_id` tinyint(3) UNSIGNED NOT NULL,
  `capo_servizio_id` int(10) UNSIGNED DEFAULT NULL,
  `vice_capo_id` int(10) UNSIGNED DEFAULT NULL,
  `funzionario` varchar(100) DEFAULT NULL,
  `note_generali` text DEFAULT NULL,
  `creato_da` varchar(60) DEFAULT NULL,
  `creato_il` datetime DEFAULT current_timestamp(),
  `modificato_il` datetime DEFAULT NULL ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `fogli_servizio`
--

INSERT INTO `fogli_servizio` (`id`, `data_servizio`, `tipo_turno`, `salto_riposo_id`, `capo_servizio_id`, `vice_capo_id`, `funzionario`, `note_generali`, `creato_da`, `creato_il`, `modificato_il`) VALUES
(1, '2026-05-21', 'D', 1, NULL, NULL, '', '', 'sistema', '2026-05-20 23:17:05', '2026-05-21 00:16:19'),
(2, '2026-05-29', 'D', 3, NULL, NULL, NULL, NULL, 'sistema', '2026-05-20 23:31:50', NULL),
(3, '2026-05-22', 'N', 1, NULL, NULL, NULL, NULL, 'sistema', '2026-05-20 23:31:54', NULL),
(4, '2026-05-30', 'N', 3, NULL, NULL, NULL, NULL, 'sistema', '2026-05-21 00:21:39', NULL),
(5, '2026-05-17', 'D', 8, NULL, NULL, NULL, NULL, 'sistema', '2026-05-21 00:27:14', NULL),
(6, '2026-05-26', 'N', 2, NULL, NULL, NULL, NULL, 'sistema', '2026-05-21 00:27:29', NULL),
(7, '2026-05-09', 'D', 6, NULL, NULL, NULL, NULL, 'sistema', '2026-05-21 00:28:43', NULL),
(8, '2026-05-13', 'D', 7, NULL, NULL, '', '', 'sistema', '2026-05-21 00:28:56', '2026-05-21 01:10:49'),
(9, '2026-05-01', 'D', 4, NULL, NULL, NULL, NULL, 'sistema', '2026-05-21 01:11:10', NULL),
(10, '2026-05-06', 'N', 5, NULL, NULL, NULL, NULL, 'sistema', '2026-05-21 01:15:25', NULL),
(11, '2026-05-02', 'N', 4, NULL, NULL, NULL, NULL, 'sistema', '2026-05-21 18:04:55', NULL),
(12, '2026-05-25', 'D', 2, NULL, NULL, NULL, NULL, 'sistema', '2026-05-25 17:38:33', NULL);

-- --------------------------------------------------------

--
-- Struttura della tabella `patenti`
--

CREATE TABLE `patenti` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `tipo` varchar(5) NOT NULL,
  `nome` varchar(60) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `patenti`
--

INSERT INTO `patenti` (`id`, `tipo`, `nome`) VALUES
(1, '1', 'Patente categoria 1'),
(2, '2', 'Patente categoria 2'),
(3, '3', 'Patente categoria 3'),
(4, '4', 'Patente categoria 4');

-- --------------------------------------------------------

--
-- Struttura della tabella `posizioni`
--

CREATE TABLE `posizioni` (
  `id` smallint(5) UNSIGNED NOT NULL,
  `sede_id` tinyint(3) UNSIGNED NOT NULL,
  `codice` varchar(20) NOT NULL,
  `nome` varchar(60) DEFAULT NULL,
  `ordine` tinyint(3) UNSIGNED DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `posizioni`
--

INSERT INTO `posizioni` (`id`, `sede_id`, `codice`, `nome`, `ordine`) VALUES
(1, 1, 'CENTR-OP', 'Centrale Operativa', 1),
(2, 1, '1A', 'Autopompa Serbatoio 1A', 2),
(3, 1, '2A', 'Autopompa Serbatoio 2A', 3),
(4, 1, '3A', 'Squadretta 3A', 4),
(5, 1, '4A', 'Autopompa Serbatoio 4A', 5),
(6, 1, '5A', 'Autopompa Serbatoio 5A', 6),
(7, 1, '1B', 'Autobotte 1B', 7),
(8, 1, '2B-NBCR', 'NBCR 2B', 8),
(9, 1, '3B', 'Autobotte 3B', 9),
(10, 1, '4B', 'Autobotte 4B', 10),
(11, 1, '1SMZ', 'Autoscala 1SMZ', 11),
(12, 1, '1FUN-AUTORADIO', 'Funzionale/Autoradio', 12),
(13, 1, '1SOP-AUTORIM', 'SOP/Autorimessa', 13),
(14, 2, 'ML-1A', 'APS Multedo 1A', 1),
(15, 2, 'ML-1NAU', 'Nautica Multedo', 2),
(16, 3, 'GA-1NAU', 'Gommone Nautica', 1),
(17, 4, 'GE-1A', 'APS Genova Est', 1),
(18, 5, 'BL-1A', 'APS Bolzaneto', 1),
(19, 6, 'BS-1A', 'APS Busalla', 1),
(20, 7, 'RP-1A', 'APS Rapallo', 1),
(21, 8, 'CH-1A', 'APS Chiavari 1A', 1),
(22, 8, 'CH-1B', 'APS Chiavari 1B', 2),
(23, 9, 'AP-TEL', 'Telefonista', 1),
(24, 9, 'AP-1ROS', 'Rosenbauer 1', 2),
(25, 9, 'AP-1ASA', 'ASA 1', 3),
(26, 9, 'AP-1VI', 'Veicolo Int. 1', 4),
(27, 9, 'AP-2VI', 'Veicolo Int. 2', 5),
(28, 10, 'EL-1SMZ', 'Elicottero SMZ', 1);

-- --------------------------------------------------------

--
-- Struttura della tabella `qualifiche`
--

CREATE TABLE `qualifiche` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `codice` varchar(5) NOT NULL,
  `nome` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `qualifiche`
--

INSERT INTO `qualifiche` (`id`, `codice`, `nome`) VALUES
(1, 'Vp', 'Vigile del Fuoco'),
(2, 'Cs', 'Capo Squadra'),
(3, 'Cr', 'Capo Reparto');

-- --------------------------------------------------------

--
-- Struttura della tabella `salti_turno`
--

CREATE TABLE `salti_turno` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `codice` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `salti_turno`
--

INSERT INTO `salti_turno` (`id`, `codice`) VALUES
(1, 'B1'),
(2, 'B2'),
(3, 'B3'),
(4, 'B4'),
(5, 'B5'),
(6, 'B6'),
(7, 'B7'),
(8, 'B8');

-- --------------------------------------------------------

--
-- Struttura della tabella `salto_servizio`
--

CREATE TABLE `salto_servizio` (
  `id` int(10) UNSIGNED NOT NULL,
  `foglio_id` int(10) UNSIGNED NOT NULL,
  `vigile_id` int(10) UNSIGNED NOT NULL,
  `richiamato` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `salto_servizio`
--

INSERT INTO `salto_servizio` (`id`, `foglio_id`, `vigile_id`, `richiamato`) VALUES
(2, 7, 1, 0),
(3, 7, 8, 0),
(4, 7, 15, 0),
(10, 9, 10, 0),
(11, 9, 17, 0),
(12, 10, 3, 0),
(13, 10, 23, 0),
(15, 11, 10, 0),
(16, 11, 17, 0),
(17, 11, 21, 0),
(18, 11, 25, 0),
(19, 12, 13, 0);

-- --------------------------------------------------------

--
-- Struttura della tabella `sedi`
--

CREATE TABLE `sedi` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `codice` varchar(10) NOT NULL,
  `nome` varchar(60) NOT NULL,
  `ordine` tinyint(3) UNSIGNED DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `sedi`
--

INSERT INTO `sedi` (`id`, `codice`, `nome`, `ordine`) VALUES
(1, 'CENTR', 'Sede Centrale', 1),
(2, 'ML', 'Multedo', 2),
(3, 'GA', 'Nautica', 3),
(4, 'GE', 'Genova Est', 4),
(5, 'BL', 'Bolzaneto', 5),
(6, 'BS', 'Busalla', 6),
(7, 'RP', 'Rapallo', 7),
(8, 'CH', 'Chiavari', 8),
(9, 'AP', 'Aeroporto', 9),
(10, 'EL', 'Reparto Volo', 10);

-- --------------------------------------------------------

--
-- Struttura della tabella `tipo_assenza`
--

CREATE TABLE `tipo_assenza` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `codice` varchar(10) NOT NULL,
  `nome` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `tipo_assenza`
--

INSERT INTO `tipo_assenza` (`id`, `codice`, `nome`) VALUES
(1, 'FER', 'Ferie'),
(2, 'RC', 'Riposo Compensativo'),
(3, 'MISS', 'Missione'),
(4, 'PERM', 'Permesso'),
(5, 'MAL', 'Malattia'),
(6, 'INF', 'Infortunio');

-- --------------------------------------------------------

--
-- Struttura della tabella `utenti`
--

CREATE TABLE `utenti` (
  `id` smallint(5) UNSIGNED NOT NULL,
  `username` varchar(40) NOT NULL,
  `password` varchar(255) NOT NULL,
  `nome` varchar(100) DEFAULT NULL,
  `ruolo` enum('admin','responsabile') DEFAULT 'responsabile',
  `attivo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `utenti`
--

INSERT INTO `utenti` (`id`, `username`, `password`, `nome`, `ruolo`, `attivo`) VALUES
(1, 'admin', '$2y$12$placeholder_change_me', 'Amministratore', 'admin', 1);

-- --------------------------------------------------------

--
-- Struttura della tabella `vigili`
--

CREATE TABLE `vigili` (
  `id` int(10) UNSIGNED NOT NULL,
  `cognome` varchar(60) NOT NULL,
  `nome` varchar(60) DEFAULT NULL,
  `disambiguatore` smallint(5) UNSIGNED DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `qualifica_id` tinyint(3) UNSIGNED NOT NULL,
  `sede_id` tinyint(3) UNSIGNED NOT NULL,
  `salto_id` tinyint(3) UNSIGNED NOT NULL,
  `patente_id` tinyint(3) UNSIGNED DEFAULT NULL,
  `attivo` tinyint(1) DEFAULT 1,
  `note` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `vigili`
--

INSERT INTO `vigili` (`id`, `cognome`, `nome`, `disambiguatore`, `qualifica_id`, `sede_id`, `salto_id`, `patente_id`, `attivo`, `note`) VALUES
(1, 'MARCACCINI', 'Andrea', NULL, 1, 1, 6, NULL, 1, 'NBCR, SAF Basico, Tas2'),
(2, 'DONDERO', 'Claudio', NULL, 2, 1, 1, NULL, 1, ''),
(3, 'PIROTTA', 'Matteo', NULL, 1, 2, 5, NULL, 1, ''),
(4, 'CHIAPPORI', 'Luca', NULL, 2, 2, 3, NULL, 1, ''),
(5, 'LAGAZZI', 'Paolo', 2, 3, 4, 4, NULL, 1, ''),
(6, 'MURGIA', 'Paolo', 2, 1, 4, 8, NULL, 1, ''),
(7, 'SAMI', 'Paolo', NULL, 1, 9, 1, NULL, 1, ''),
(8, 'MENICAGLI', 'Alberto', NULL, 3, 9, 6, NULL, 1, ''),
(9, 'PITTALUGA', 'Fulvio', 4, 2, 5, 8, NULL, 1, ''),
(10, 'PARODI', 'Francesco', 19, 1, 5, 4, NULL, 1, ''),
(11, 'ABDEL', 'Amir', NULL, 3, 6, 8, NULL, 1, ''),
(12, 'PARODI', 'Andrea', 20, 1, 6, 1, NULL, 1, ''),
(13, 'GARBARINO', 'Federico', 5, 1, 6, 2, NULL, 1, ''),
(14, 'DI GENNARO', 'Andrea', NULL, 2, 8, 7, NULL, 1, ''),
(15, 'RAGGIO', 'Cristian', NULL, 2, 8, 6, NULL, 1, ''),
(16, 'SCHIANCHI', 'Gabriele', NULL, 1, 8, 1, NULL, 1, ''),
(17, 'SANNA', 'Yuri', NULL, 1, 8, 4, NULL, 1, ''),
(18, 'LAMBERTI', 'Marco', NULL, 2, 7, 8, NULL, 1, ''),
(19, 'ARTHEMALLE', 'Davide', NULL, 1, 7, 3, NULL, 1, ''),
(20, 'D\'AMATO', 'Simone', 3, 1, 7, 7, NULL, 1, ''),
(21, 'MOLINARI', 'Andrea', NULL, 2, 1, 4, NULL, 1, ''),
(22, 'MANASSERO', 'Claudio', NULL, 3, 1, 8, NULL, 1, ''),
(23, 'OBINU', 'Giovanni', NULL, 3, 1, 5, NULL, 1, ''),
(24, 'PASTORINO', 'Walter', 5, 3, 1, 7, NULL, 1, ''),
(25, 'VATTUONE', 'Filippo', NULL, 3, 1, 4, NULL, 1, '');

-- --------------------------------------------------------

--
-- Struttura della tabella `vigili_abilitazioni`
--

CREATE TABLE `vigili_abilitazioni` (
  `vigile_id` int(10) UNSIGNED NOT NULL,
  `abilitazione_id` tinyint(3) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `vigili_abilitazioni`
--

INSERT INTO `vigili_abilitazioni` (`vigile_id`, `abilitazione_id`) VALUES
(1, 1),
(1, 2),
(1, 6),
(1, 7),
(1, 8),
(2, 10),
(3, 6),
(6, 2),
(20, 4),
(20, 5),
(21, 10),
(22, 2),
(22, 3),
(22, 4),
(22, 5),
(23, 1);

-- --------------------------------------------------------

--
-- Struttura della tabella `vigili_patenti`
--

CREATE TABLE `vigili_patenti` (
  `vigile_id` int(10) UNSIGNED NOT NULL,
  `patente_id` tinyint(3) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dump dei dati per la tabella `vigili_patenti`
--

INSERT INTO `vigili_patenti` (`vigile_id`, `patente_id`) VALUES
(1, 1),
(2, 2),
(3, 1),
(4, 1),
(5, 1),
(6, 1),
(7, 1),
(8, 3),
(9, 2),
(10, 3),
(11, 1),
(12, 3),
(13, 1),
(14, 1),
(15, 1),
(16, 2),
(17, 2),
(18, 1),
(19, 1),
(20, 2),
(21, 1),
(22, 1),
(23, 2),
(24, 3),
(25, 2);

--
-- Indici per le tabelle scaricate
--

--
-- Indici per le tabelle `abilitazioni`
--
ALTER TABLE `abilitazioni`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `assegnazioni`
--
ALTER TABLE `assegnazioni`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_ass` (`foglio_id`,`vigile_id`),
  ADD KEY `posizione_id` (`posizione_id`),
  ADD KEY `vigile_id` (`vigile_id`);

--
-- Indici per le tabelle `assenze`
--
ALTER TABLE `assenze`
  ADD PRIMARY KEY (`id`),
  ADD KEY `foglio_id` (`foglio_id`),
  ADD KEY `vigile_id` (`vigile_id`),
  ADD KEY `tipo_assenza_id` (`tipo_assenza_id`);

--
-- Indici per le tabelle `foglio_furieri`
--
ALTER TABLE `foglio_furieri`
  ADD PRIMARY KEY (`foglio_id`,`vigile_id`),
  ADD KEY `vigile_id` (`vigile_id`);

--
-- Indici per le tabelle `fogli_servizio`
--
ALTER TABLE `fogli_servizio`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_foglio` (`data_servizio`,`tipo_turno`),
  ADD KEY `salto_riposo_id` (`salto_riposo_id`),
  ADD KEY `capo_servizio_id` (`capo_servizio_id`),
  ADD KEY `vice_capo_id` (`vice_capo_id`);

--
-- Indici per le tabelle `patenti`
--
ALTER TABLE `patenti`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `posizioni`
--
ALTER TABLE `posizioni`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sede_id` (`sede_id`);

--
-- Indici per le tabelle `qualifiche`
--
ALTER TABLE `qualifiche`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `salti_turno`
--
ALTER TABLE `salti_turno`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `salto_servizio`
--
ALTER TABLE `salto_servizio`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_salto` (`foglio_id`,`vigile_id`),
  ADD KEY `vigile_id` (`vigile_id`);

--
-- Indici per le tabelle `sedi`
--
ALTER TABLE `sedi`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `tipo_assenza`
--
ALTER TABLE `tipo_assenza`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `utenti`
--
ALTER TABLE `utenti`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indici per le tabelle `vigili`
--
ALTER TABLE `vigili`
  ADD PRIMARY KEY (`id`),
  ADD KEY `qualifica_id` (`qualifica_id`),
  ADD KEY `sede_id` (`sede_id`),
  ADD KEY `salto_id` (`salto_id`),
  ADD KEY `patente_id` (`patente_id`);

--
-- Indici per le tabelle `vigili_abilitazioni`
--
ALTER TABLE `vigili_abilitazioni`
  ADD PRIMARY KEY (`vigile_id`,`abilitazione_id`),
  ADD KEY `abilitazione_id` (`abilitazione_id`);

--
-- Indici per le tabelle `vigili_patenti`
--
ALTER TABLE `vigili_patenti`
  ADD PRIMARY KEY (`vigile_id`,`patente_id`),
  ADD KEY `patente_id` (`patente_id`);

--
-- AUTO_INCREMENT per le tabelle scaricate
--

--
-- AUTO_INCREMENT per la tabella `abilitazioni`
--
ALTER TABLE `abilitazioni`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT per la tabella `assegnazioni`
--
ALTER TABLE `assegnazioni`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=201;

--
-- AUTO_INCREMENT per la tabella `assenze`
--
ALTER TABLE `assenze`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

--
-- AUTO_INCREMENT per la tabella `fogli_servizio`
--
ALTER TABLE `fogli_servizio`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT per la tabella `patenti`
--
ALTER TABLE `patenti`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT per la tabella `posizioni`
--
ALTER TABLE `posizioni`
  MODIFY `id` smallint(5) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- AUTO_INCREMENT per la tabella `qualifiche`
--
ALTER TABLE `qualifiche`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `salti_turno`
--
ALTER TABLE `salti_turno`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT per la tabella `salto_servizio`
--
ALTER TABLE `salto_servizio`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT per la tabella `sedi`
--
ALTER TABLE `sedi`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT per la tabella `tipo_assenza`
--
ALTER TABLE `tipo_assenza`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT per la tabella `utenti`
--
ALTER TABLE `utenti`
  MODIFY `id` smallint(5) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT per la tabella `vigili`
--
ALTER TABLE `vigili`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- Limiti per le tabelle scaricate
--

--
-- Limiti per la tabella `assegnazioni`
--
ALTER TABLE `assegnazioni`
  ADD CONSTRAINT `assegnazioni_ibfk_1` FOREIGN KEY (`foglio_id`) REFERENCES `fogli_servizio` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `assegnazioni_ibfk_2` FOREIGN KEY (`posizione_id`) REFERENCES `posizioni` (`id`),
  ADD CONSTRAINT `assegnazioni_ibfk_3` FOREIGN KEY (`vigile_id`) REFERENCES `vigili` (`id`);

--
-- Limiti per la tabella `assenze`
--
ALTER TABLE `assenze`
  ADD CONSTRAINT `assenze_ibfk_1` FOREIGN KEY (`foglio_id`) REFERENCES `fogli_servizio` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `assenze_ibfk_2` FOREIGN KEY (`vigile_id`) REFERENCES `vigili` (`id`),
  ADD CONSTRAINT `assenze_ibfk_3` FOREIGN KEY (`tipo_assenza_id`) REFERENCES `tipo_assenza` (`id`);

--
-- Limiti per la tabella `foglio_furieri`
--
ALTER TABLE `foglio_furieri`
  ADD CONSTRAINT `foglio_furieri_ibfk_1` FOREIGN KEY (`foglio_id`) REFERENCES `fogli_servizio` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `foglio_furieri_ibfk_2` FOREIGN KEY (`vigile_id`) REFERENCES `vigili` (`id`);

--
-- Limiti per la tabella `fogli_servizio`
--
ALTER TABLE `fogli_servizio`
  ADD CONSTRAINT `fogli_servizio_ibfk_1` FOREIGN KEY (`salto_riposo_id`) REFERENCES `salti_turno` (`id`),
  ADD CONSTRAINT `fogli_servizio_ibfk_2` FOREIGN KEY (`capo_servizio_id`) REFERENCES `vigili` (`id`),
  ADD CONSTRAINT `fogli_servizio_ibfk_3` FOREIGN KEY (`vice_capo_id`) REFERENCES `vigili` (`id`);

--
-- Limiti per la tabella `posizioni`
--
ALTER TABLE `posizioni`
  ADD CONSTRAINT `posizioni_ibfk_1` FOREIGN KEY (`sede_id`) REFERENCES `sedi` (`id`);

--
-- Limiti per la tabella `salto_servizio`
--
ALTER TABLE `salto_servizio`
  ADD CONSTRAINT `salto_servizio_ibfk_1` FOREIGN KEY (`foglio_id`) REFERENCES `fogli_servizio` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `salto_servizio_ibfk_2` FOREIGN KEY (`vigile_id`) REFERENCES `vigili` (`id`);

--
-- Limiti per la tabella `vigili`
--
ALTER TABLE `vigili`
  ADD CONSTRAINT `vigili_ibfk_1` FOREIGN KEY (`qualifica_id`) REFERENCES `qualifiche` (`id`),
  ADD CONSTRAINT `vigili_ibfk_2` FOREIGN KEY (`sede_id`) REFERENCES `sedi` (`id`),
  ADD CONSTRAINT `vigili_ibfk_3` FOREIGN KEY (`salto_id`) REFERENCES `salti_turno` (`id`),
  ADD CONSTRAINT `vigili_ibfk_4` FOREIGN KEY (`patente_id`) REFERENCES `patenti` (`id`);

--
-- Limiti per la tabella `vigili_abilitazioni`
--
ALTER TABLE `vigili_abilitazioni`
  ADD CONSTRAINT `vigili_abilitazioni_ibfk_1` FOREIGN KEY (`vigile_id`) REFERENCES `vigili` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `vigili_abilitazioni_ibfk_2` FOREIGN KEY (`abilitazione_id`) REFERENCES `abilitazioni` (`id`);

--
-- Limiti per la tabella `vigili_patenti`
--
ALTER TABLE `vigili_patenti`
  ADD CONSTRAINT `vigili_patenti_ibfk_1` FOREIGN KEY (`vigile_id`) REFERENCES `vigili` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `vigili_patenti_ibfk_2` FOREIGN KEY (`patente_id`) REFERENCES `patenti` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
