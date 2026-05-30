-- ============================================================
-- Allinea tutto al CSV "Turno B nuovo.csv" come fonte di verità
-- Eseguire una sola volta su phpMyAdmin o MySQL CLI
-- ============================================================

-- 1. Rinomina sedi esistenti (uppercase = nomi CSV)
UPDATE sedi SET nome = 'CENTRALE'  WHERE id = 1;
UPDATE sedi SET nome = 'MULTEDO'   WHERE id = 2;
UPDATE sedi SET nome = 'GADDA'     WHERE id = 3;
UPDATE sedi SET nome = 'GEEST'     WHERE id = 4;
UPDATE sedi SET nome = 'BOLZANETO' WHERE id = 5;
UPDATE sedi SET nome = 'BUSALLA'   WHERE id = 6;
UPDATE sedi SET nome = 'RAPALLO'   WHERE id = 7;
UPDATE sedi SET nome = 'CHIAVARI'  WHERE id = 8;
UPDATE sedi SET nome = 'AEROPORTO' WHERE id = 9;
-- id 10 = Reparto Volo (EL) — non nel CSV, lasciato invariato

-- 2. Aggiungi sedi mancanti
INSERT INTO sedi (id, codice, nome, ordine) VALUES (11, 'MN',   'MLNAU', 11);
INSERT INTO sedi (id, codice, nome, ordine) VALUES (12, 'SMZT', 'SMZT',  12);

-- 3. Correggi sede_id di tutti i vigili (fonte: email dal CSV)
UPDATE vigili SET sede_id =  6 WHERE email = 'amir.abdelmohsenhafez@vigilfuoco.it';  -- BUSALLA
UPDATE vigili SET sede_id =  3 WHERE email = 'domenico.api@vigilfuoco.it';  -- GADDA
UPDATE vigili SET sede_id =  7 WHERE email = 'francesco.arata@vigilfuoco.it';  -- RAPALLO
UPDATE vigili SET sede_id =  1 WHERE email = 'gabriele.armelin@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  7 WHERE email = 'davide.arthemalle@vigilfuoco.it';  -- RAPALLO
UPDATE vigili SET sede_id =  1 WHERE email = 'fabio.barabino@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  8 WHERE email = 'luca.barbanti@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id =  1 WHERE email = 'diego.barbieri@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  4 WHERE email = 'fabrizio.bario@vigilfuoco.it';  -- GEEST
UPDATE vigili SET sede_id =  1 WHERE email = 'davide.bruno@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'davide.campanino@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  2 WHERE email = 'claudio.canneva@vigilfuoco.it';  -- MULTEDO
UPDATE vigili SET sede_id =  9 WHERE email = 'gabriele.carcerano@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  1 WHERE email = 'alessio.carenzo@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'carpi.elex@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  2 WHERE email = 'enrico.casagrande@vigilfuoco.it';  -- MULTEDO
UPDATE vigili SET sede_id =  8 WHERE email = 'massimiliano.cassinelli@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id = 11 WHERE email = 'francesco.caviglia@vigilfuoco.it';  -- MLNAU
UPDATE vigili SET sede_id =  2 WHERE email = 'luca.chiappori@vigilfuoco.it';  -- MULTEDO
UPDATE vigili SET sede_id =  2 WHERE email = 'francesco1.chila@vigilfuoco.it';  -- MULTEDO
UPDATE vigili SET sede_id =  1 WHERE email = 'andrea.cilia@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  9 WHERE email = 'pierluigi.civardi@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  6 WHERE email = 'andrea4.costa@vigilfuoco.it';  -- BUSALLA
UPDATE vigili SET sede_id =  1 WHERE email = 'giuseppe.cremisi@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  9 WHERE email = 'cucinotta.stefano@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  5 WHERE email = 'roberto.cuda@vigilfuoco.it';  -- BOLZANETO
UPDATE vigili SET sede_id =  9 WHERE email = 'giovanni.curto@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  7 WHERE email = 'simone.damato@vigilfuoco.it';  -- RAPALLO
UPDATE vigili SET sede_id =  1 WHERE email = 'alberto.dagnino@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  7 WHERE email = 'matteo.derosa@vigilfuoco.it';  -- RAPALLO
UPDATE vigili SET sede_id =  8 WHERE email = 'andrea.digennaro@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id = 11 WHERE email = 'stefano.dionisi@vigilfuoco.it';  -- MLNAU
UPDATE vigili SET sede_id =  1 WHERE email = 'claudio.dondero@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id = 12 WHERE email = 'massimo.durante@vigilfuoco.it';  -- SMZT
UPDATE vigili SET sede_id =  1 WHERE email = 'maurizio.esposito@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  2 WHERE email = 'tommaso.ferrari@vigilfuoco.it';  -- MULTEDO
UPDATE vigili SET sede_id =  9 WHERE email = 'cristiano.ferrari@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id = 12 WHERE email = 'paolo.ferraris@vigilfuoco.it';  -- SMZT
UPDATE vigili SET sede_id =  6 WHERE email = 'federicoedoardo.garbarino@vigilfuoco.it';  -- BUSALLA
UPDATE vigili SET sede_id =  3 WHERE email = 'aurelio.genovese@vigilfuoco.it';  -- GADDA
UPDATE vigili SET sede_id =  1 WHERE email = 'emanuele.genovesi@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  9 WHERE email = 'bernardo.ghigliotti@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id = 12 WHERE email = 'lorenzo.ghigliotti@vigilfuoco.it';  -- SMZT
UPDATE vigili SET sede_id =  1 WHERE email = 'massimo.giovinazzo@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  5 WHERE email = 'igor.giovinazzo@vigilfuoco.it';  -- BOLZANETO
UPDATE vigili SET sede_id =  8 WHERE email = 'moreno.grillo@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id = 12 WHERE email = 'samir.jaibi@vigilfuoco.it';  -- SMZT
UPDATE vigili SET sede_id =  4 WHERE email = 'paolo.lagazzi@vigilfuoco.it';  -- GEEST
UPDATE vigili SET sede_id =  7 WHERE email = 'marco.lamberti@vigilfuoco.it';  -- RAPALLO
UPDATE vigili SET sede_id =  1 WHERE email = 'marioorazio.lizio@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'andrea.loffredo@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  9 WHERE email = 'carlo.longo@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  1 WHERE email = 'stefano.longobardi@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  9 WHERE email = 'luca.lurani@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  1 WHERE email = 'riccardo.madaro@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'ciro.magnetti@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'claudio.manassero@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'luca.manzi@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'andrea.marcaccini@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  8 WHERE email = 'daniele.marinelli@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id =  1 WHERE email = 'luca.marini@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  4 WHERE email = 'mario.masino@vigilfuoco.it';  -- GEEST
UPDATE vigili SET sede_id =  9 WHERE email = 'giovanni.mauro@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  9 WHERE email = 'alberto.menicagli@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  1 WHERE email = 'salvatore.merulla@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'stelvio.minafra@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'andrea.molinari@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  2 WHERE email = 'alberto.mostes@vigilfuoco.it';  -- MULTEDO
UPDATE vigili SET sede_id =  6 WHERE email = 'marco.mucchi@vigilfuoco.it';  -- BUSALLA
UPDATE vigili SET sede_id =  4 WHERE email = 'paolo.murgia@vigilfuoco.it';  -- GEEST
UPDATE vigili SET sede_id =  1 WHERE email = 'rodolfo.murru@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  4 WHERE email = 'matteo.musante@vigilfuoco.it';  -- GEEST
UPDATE vigili SET sede_id =  1 WHERE email = 'mattia.neni@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  4 WHERE email = 'alessandro.novelli@vigilfuoco.it';  -- GEEST
UPDATE vigili SET sede_id =  1 WHERE email = 'giovanni.obinu@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'simone.oneto@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'raffaele.palagonia@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  5 WHERE email = 'francesco1.parodi@vigilfuoco.it';  -- BOLZANETO
UPDATE vigili SET sede_id =  6 WHERE email = 'andrea.parodi@vigilfuoco.it';  -- BUSALLA
UPDATE vigili SET sede_id =  1 WHERE email = 'giorgio.parodi@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'walter.pastorino@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'alessio.pastorino@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  9 WHERE email = 'stefano.penserini@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  1 WHERE email = 'laura.piazzi@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  5 WHERE email = 'marco.piga@vigilfuoco.it';  -- BOLZANETO
UPDATE vigili SET sede_id =  4 WHERE email = 'fabrizio.pirlo@vigilfuoco.it';  -- GEEST
UPDATE vigili SET sede_id =  2 WHERE email = 'matteo.pirotta@vigilfuoco.it';  -- MULTEDO
UPDATE vigili SET sede_id =  5 WHERE email = 'fulvio.pittaluga@vigilfuoco.it';  -- BOLZANETO
UPDATE vigili SET sede_id =  1 WHERE email = 'andrea.poire@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  8 WHERE email = 'davide.porro@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id =  9 WHERE email = 'andrea.priano@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  8 WHERE email = 'christian.raggio@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id =  1 WHERE email = 'alessio1.romano@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'roberto.ronco@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id = 12 WHERE email = 'andrea1.russo@vigilfuoco.it';  -- SMZT
UPDATE vigili SET sede_id =  1 WHERE email = 'andrea.salvadori@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  9 WHERE email = 'mario.sami@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  8 WHERE email = 'yuri.sanna@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id =  8 WHERE email = 'gabriele.schianchi@vigilfuoco.it';  -- CHIAVARI
UPDATE vigili SET sede_id =  1 WHERE email = 'mario.scutifero@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  9 WHERE email = 'fabio.semino@vigilfuoco.it';  -- AEROPORTO
UPDATE vigili SET sede_id =  1 WHERE email = 'luca.siri@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id = 12 WHERE email = 'simone.solinas@vigilfuoco.it';  -- SMZT
UPDATE vigili SET sede_id =  6 WHERE email = 'vincenzo.surace@vigilfuoco.it';  -- BUSALLA
UPDATE vigili SET sede_id =  1 WHERE email = 'fabrizio.tavella@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'filippo.vattuone@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'vittorio.ventura@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'luca.zanicchi@vigilfuoco.it';  -- CENTRALE
UPDATE vigili SET sede_id =  1 WHERE email = 'francesco.zanza@vigilfuoco.it';  -- CENTRALE

-- 4. Fix duplicato RAGGIO Christian/Cristian
--    Il dump originale aveva id=15 senza email; l'import ha creato un secondo record con email.
--    Copia email e odt_label sul record originale, poi elimina il duplicato.
UPDATE vigili v1
JOIN vigili v2 ON v2.cognome = 'RAGGIO' AND v2.email = 'christian.raggio@vigilfuoco.it'
SET v1.email     = v2.email,
    v1.odt_label = v2.odt_label,
    v1.nome      = 'Christian'
WHERE v1.id = 15;

DELETE FROM vigili
WHERE cognome = 'RAGGIO'
  AND email = 'christian.raggio@vigilfuoco.it'
  AND id != 15;

-- 5. Verifica post-migrazione: vigili con stesso cognome+nome (veri doppi, non omonimi)
SELECT cognome, nome, COUNT(*) AS n
FROM vigili
GROUP BY cognome, nome
HAVING n > 1
ORDER BY cognome;
