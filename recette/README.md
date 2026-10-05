# Stack de recette Codabli

Déploiement de l'environnement de recette sur la VM OVH (provisionnée par `../tofu`).
Périmètre V1 : **front + backend + Keycloak + PostgreSQL**. Le **service IA est hors
périmètre** (pas encore exposé en API). Accès **HTTP sur IP** ; le HTTPS viendra
avec le sous-domaine.

## Architecture

Un seul point d'entrée public : **Caddy sur le port 80**, routage par chemin :

| Chemin    | Service        | Détail |
|-----------|----------------|--------|
| `/`       | front (nginx)  | SPA Angular statique |
| `/api/*`  | backend:8082   | Spring Boot, contrôleurs déjà mappés sous `/api` |
| `/auth/*` | keycloak:8080  | Keycloak en mode prod, relative path `/auth` |

- **PostgreSQL** héberge deux bases : `codabli` (appli) et `keycloak` (créée à l'init).
- L'**issuer Keycloak** = `${PUBLIC_URL}/auth/realms/codabli`. Le backend valide le
  `iss` des jetons contre cette URL, et récupère les clés en interne
  (`http://keycloak:8080/...`) — pas d'appel sortant au démarrage.
- Une **seule variable** `PUBLIC_URL` bascule tout de l'IP vers le domaine plus tard.

## Premier déploiement (manuel, pour valider la stack)

Pas encore de CI : on build directement sur la VM à partir du code. Le plus simple,
sans configurer d'accès GitHub sur la VM, est de **copier le code depuis ton poste**.

**1. Copier le code sur la VM** (depuis ton poste WSL) :
```sh
rsync -av --exclude node_modules --exclude target --exclude .git --exclude .venv \
  ~/inside/codabli/ ubuntu@51.178.223.90:~/codabli/
```

**2. Configurer les secrets** (sur la VM) :
```sh
ssh ubuntu@51.178.223.90
cd ~/codabli/codabli-infra/recette
cp .env.example .env
nano .env          # renseigner les mots de passe + KEYCLOAK_CLIENT_SECRET
```

**3. Lancer** (sur la VM) :
```sh
docker compose up -d --build     # full stack ; première fois : plusieurs min (build Java 25 + Angular)
docker compose ps                # tout doit être "running"/"healthy"
docker compose logs -f backend   # vérifier le démarrage Spring Boot
```

## Vérifier

- Front : `http://51.178.223.90/`  → l'appli Angular s'affiche.
- Keycloak : `http://51.178.223.90/auth/`  → console d'admin (login = KEYCLOAK_ADMIN).
- API : `http://51.178.223.90/api/...`  → répond (401 sur les routes protégées, c'est normal).

## Exploitation

```sh
docker compose down            # arrêter (données conservées dans les volumes)
docker compose pull && docker compose up -d   # (plus tard) déployer les images CI
docker compose logs -f <service>
```

## Ce qui reste à faire (prochaines étapes)

- **CI GitHub Actions** : build → GHCR → déploiement auto sur push `develop`.
- **HTTPS** : brancher le sous-domaine (DNS en IaC) + basculer le Caddyfile.
- **Sauvegarde / restauration** PostgreSQL (Scénario 4 de REC-US02).
- **Jeu de données de test** anonymisé (Scénario 3).
- **Durcissement** : mots de passe forts, secret client Keycloak régénéré, realm en
  `redirectUris`/`webOrigins` restreints (aujourd'hui `*`), quand le front aura l'auth.

## Points de vigilance

- Le realm `keycloak/realm-codabli.json` est une **copie** de celui du backend. En cas
  de modif côté backend, resynchroniser (ou automatiser plus tard).
- Build lourd (Java 25 + Angular) sur une d2-8 : la première fois prend plusieurs
  minutes. Les suivantes sont plus rapides (cache Docker).
