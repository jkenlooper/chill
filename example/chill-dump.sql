--- This file is loaded into the sqlite database when Chill starts.
--- 
--- This file is recreated each time when Chill exits. It will dump all tables
--- matching the pattern:
--- %
--- with the exception of Chill managed tables.
--- 
--- WARNING: Do not modify this file while Chill is running.
--- 
--- WARNING: Only make changes to the active sqlite database when Chill is running.

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE example (id integer primary key, something varchar);
INSERT INTO example VALUES(1,'one');
INSERT INTO example VALUES(2,'two');
COMMIT;
