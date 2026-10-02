-- Permite que Django cree y borre la base temporal de las pruebas (test_mudanzas_db).
-- MySQL corre este archivo solo la primera vez, cuando el volumen está vacío.
GRANT ALL PRIVILEGES ON `test\_%`.* TO 'mudanzas_user'@'%';
FLUSH PRIVILEGES;
