# codabli-infra — Infrastructure de recette (IaC)

Provisionnement de l'environnement de **recette** Codabli sur **OVH Public Cloud**,
en **OpenTofu** (fork open source de Terraform). Décision d'hébergeur : voir
`../docs/NOTE_DECISION_HEBERGEUR_RECETTE.md` (US `REC-US01`). Mise en place : `REC-US02`.

Périmètre V1 : une instance qui accueillera **front + back + PostgreSQL + Keycloak**
via Docker Compose. Le **service IA est hors périmètre** pour l'instant (pas encore
exposé en API). La recette est servie en HTTPS sur **`https://recette.codabli.com`** ;
l'enregistrement DNS n'est pas encore géré par ce code.

---

## 📚 Documentation du repo

- **README.md** (ce fichier) — prérequis OVH, obtention des UUID, lancer Tofu, coûts.
- **[docs/TUTO_OPENTOFU.md](docs/TUTO_OPENTOFU.md)** — prise en main d'OpenTofu (concepts, state,
  cycle `init/plan/apply/destroy`) pour qui débute en IaC.
- **[docs/DEPLOIEMENT_RECETTE.md](docs/DEPLOIEMENT_RECETTE.md)** — architecture complète
  avec schémas : construction du serveur, **pipeline CI/CD GitHub → GHCR → VM**, stack
  Docker/Caddy, secrets.

---

## Ce que contient le repo

**Le serveur** (`tofu/`, ce README) :
- crée **une instance** OVH Public Cloud `d2-8` (4 vCPU / 8 Go), IP publique ;
- la bootstrappe via **cloud-init** : Docker + Docker Compose + pare-feu (22/80/443).

**Ce qui tourne dessus** (`recette/`, voir [recette/README.md](recette/README.md)) :
- `docker-compose.yml` : front, backend, Keycloak, PostgreSQL et Caddy ;
- `Caddyfile` : reverse-proxy HTTPS (certificat Let's Encrypt automatique) sur
  `recette.codabli.com`, qui route `/api/*` vers le backend, `/auth/*` vers
  Keycloak et le reste vers le front.

**Le déploiement automatique** n'est pas dans ce repo : chaque repo applicatif a
son workflow `.github/workflows/deploy-recette.yml` (front et backend). Un push sur
`develop` construit l'image, la publie sur GHCR et relance le service sur la VM.
Détails : [docs/DEPLOIEMENT_RECETTE.md](docs/DEPLOIEMENT_RECETTE.md).

**Pas encore fait** : l'enregistrement DNS du sous-domaine en IaC (aucune
ressource DNS dans `tofu/` pour l'instant).

---

## Installer OpenTofu

- **Windows (PowerShell)** : `winget install OpenTofu.Tofu`, puis fermer et rouvrir
  le terminal.
- **Linux / WSL** : voir [docs/TUTO_OPENTOFU.md](docs/TUTO_OPENTOFU.md#5-installer-opentofu).

Vérifier avec `tofu version`.

> Les commandes de ce README sont écrites pour un terminal Linux / WSL. Les
> équivalents **PowerShell** sont donnés juste en dessous quand la syntaxe change.

---

## Prérequis (une fois, côté OVH, à faire à la mano)

1. **Projet Public Cloud** : le créer dans le manager OVH si absent
   (Public Cloud > Create a project). Noter son **ID** → `service_name`.
2. **Clés API OVH** : les générer sur https://api.ovh.com/createToken/
   (droits sur `/cloud/project/{serviceName}/*`), puis les exporter :
   ```sh
   export OVH_ENDPOINT=ovh-eu
   export OVH_APPLICATION_KEY=...
   export OVH_APPLICATION_SECRET=...
   export OVH_CONSUMER_KEY=...
   ```
   En PowerShell (valables seulement dans la fenêtre ouverte) :
   ```powershell
   $env:OVH_ENDPOINT = "ovh-eu"
   $env:OVH_APPLICATION_KEY = "..."
   $env:OVH_APPLICATION_SECRET = "..."
   $env:OVH_CONSUMER_KEY = "..."
   ```
3. **Clé SSH** : avoir une paire (`ssh-keygen -t ed25519`, même commande sous
   Windows). On met la clé **publique** dans `ssh_public_key`. Pour l'afficher :
   `cat ~/.ssh/id_ed25519.pub`, ou en PowerShell
   `Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub`.

### Obtenir les UUID `flavor_id` et `image_id`

Le provider référence le flavor et l'image par **UUID** (spécifiques à la région).
Avec tes clés API exportées, tu peux les lister via l'API OVH
(console https://api.ovh.com/console/ ou un appel signé) :

- Flavors : `GET /cloud/project/{serviceName}/flavor?region=GRA11` → repérer le
  `name` **`d2-8`**, prendre son `id`.
- Images : `GET /cloud/project/{serviceName}/image?region=GRA11&osType=linux` →
  repérer **Ubuntu 24.04**, prendre son `id`.

(Alternative : la console OVH affiche aussi ces identifiants.)

---

## Lancer

```sh
cd tofu
cp terraform.tfvars.example terraform.tfvars   # puis renseigner
tofu init
tofu plan
tofu apply
```

En PowerShell, seule la copie change :
```powershell
cd tofu
Copy-Item terraform.tfvars.example terraform.tfvars   # puis renseigner (notepad terraform.tfvars)
tofu init
tofu plan
tofu apply
```

Récupérer l'IP publique après création :
```sh
tofu state show ovh_cloud_project_instance.recette   # cherche l'adresse publique
```
puis se connecter : `ssh ubuntu@<IP>`.

Détruire (utile tant qu'on itère, surtout en facturation `hourly`) :
```sh
tofu destroy
```

---

## Coût & points de vigilance

- **d2-8 (4 vCPU / 8 Go)** : ~**25 $/mois** (monthly) ou ~**33 $/mois** si allumé
  h24 en hourly. Base PostgreSQL auto-hébergée sur l'instance → 0 € de plus.
  Dans l'enveloppe de contrôle de REC-US01 (~70 €/mois).
- ⚠️ **Nouveaux tarifs Public Cloud OVH au 1er octobre 2026** : revérifier le prix
  au moment de commander.
- ⚠️ **State OpenTofu** : `terraform.tfstate` reste **local** ici (ignoré par git).
  Pour un travail à plusieurs, prévoir un backend distant (ex. OVH Object Storage
  S3-compatible). À décider si l'équipe grossit.
- `billing_period = hourly` par défaut pour pouvoir `destroy`/recréer librement
  pendant la mise au point ; passer en `monthly` une fois la recette stable.

---

## État des fichiers

| Fichier | Rôle |
|---|---|
| `tofu/versions.tf` | Versions OpenTofu + provider OVH |
| `tofu/providers.tf` | Config provider OVH (clés via l'environnement) |
| `tofu/variables.tf` | Variables d'entrée |
| `tofu/main.tf` | L'instance + cloud-init |
| `tofu/outputs.tf` | Sorties (id ; IP à confirmer via `tofu state show`) |
| `tofu/cloud-init.yaml` | Bootstrap Docker + pare-feu |
| `tofu/terraform.tfvars.example` | Modèle de variables à copier |
