-- Crée la base dédiée à Keycloak (le service applicatif utilise POSTGRES_DB).
-- Exécuté une seule fois, à l'initialisation du volume PostgreSQL (data dir vide).
CREATE DATABASE keycloak;
