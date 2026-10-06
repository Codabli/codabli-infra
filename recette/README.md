# Stack de recette Codabli

Déploiement de l'environnement de recette sur la VM OVH (provisionnée par `../tofu`).
Périmètre V1 : **front + backend + Keycloak + PostgreSQL**. Le **service IA est hors
périmètre** (pas encore exposé en API). Accès en **HTTPS sur
`https://recette.codabli.com`** (certificat Let's Encrypt obtenu et renouvelé par Caddy).

Les déploiements courants sont **automatiques** : un push sur `develop` du front ou du
backend construit l'image, la publie sur GHCR et relance le service sur la VM (voir
[../docs/DEPLOIEMENT_RECETTE.md](../docs/DEPLOIEMENT_RECETTE.md)). La procédure manuelle
ci-dessous sert à monter la stack sur une VM neuve ou à dépanner.

## Architecture

Un seul point d'entrée public : **Caddy sur les ports 80 et 443** (le 80 redirige vers
le HTTPS et sert au challenge Let's Encrypt), routage par chemin :

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

On build directement sur la VM à partir du code. Le plus simple, sans configurer
d'accès GitHub sur la VM, est de **copier le code depuis ton poste**.

> ⚠️ Le contexte de build du backend dans `docker-compose.yml` pointe vers
> `../../Codabli_Backend_` : il faut que le dossier copié porte ce nom

**1. Copier le code sur la VM** (depuis ton poste WSL) :
```sh
rsync -av --exclude node_modules --exclude target --exclude .git --exclude .venv \
  ~/inside/codabli/ ubuntu@51.178.223.90:~/codabli/
```

`rsync` n'existe pas sous Windows : passer par WSL (commande ci-dessus), ou faire une
archive sans les dossiers lourds puis l'envoyer avec `scp` (fourni avec Windows) :
```powershell
# depuis le dossier qui contient codabli-frontend, codabli-backend et codabli-infra
tar -czf codabli.tgz --exclude=node_modules --exclude=target --exclude=.git --exclude=.venv `
  codabli-frontend codabli-backend codabli-infra
scp codabli.tgz ubuntu@51.178.223.90:~/
ssh ubuntu@51.178.223.90 "mkdir -p ~/codabli && tar -xzf ~/codabli.tgz -C ~/codabli && rm ~/codabli.tgz"
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

- Front : `https://recette.codabli.com/`  → l'appli Angular s'affiche.
- Keycloak : `https://recette.codabli.com/auth/`  → console d'admin (login = KEYCLOAK_ADMIN).
- API : `https://recette.codabli.com/api/...`  → répond (401 sur les routes protégées, c'est normal).

## Exploitation

```sh
docker compose down            # arrêter (données conservées dans les volumes)
docker compose pull && docker compose up -d --no-build   # redéployer les images publiées par la CI
docker compose logs -f <service>
```

## Ce qui reste à faire (prochaines étapes)

- **DNS en IaC** : décrire l'enregistrement de `recette.codabli.com` dans `../tofu`.
- **Sauvegarde / restauration** PostgreSQL (Scénario 4 de REC-US02).
- **Jeu de données de test** anonymisé (Scénario 3).
- **Durcissement** : mots de passe forts, secret client Keycloak régénéré, realm en
  `redirectUris`/`webOrigins` restreints (aujourd'hui `*`), quand le front aura l'auth.

## Points de vigilance

- Le realm `keycloak/realm-codabli.json` est une **copie** de celui du backend. En cas
  de modif côté backend, resynchroniser (ou automatiser plus tard).
- Build lourd (Java 25 + Angular) sur une d2-8 : la première fois prend plusieurs
  minutes. Les suivantes sont plus rapides (cache Docker).
