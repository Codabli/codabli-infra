# Mini-tuto OpenTofu (pour démarrer sur l'infra de recette)

Tuto d'introduction pour piloter l'infrastructure de recette Codabli en **IaC**.
Aucune connaissance préalable de Terraform/OpenTofu requise. Les commandes
concrètes du projet sont en section 6. Le code se trouve dans `../tofu/`.

---

## 1. L'idée en une phrase

Tu **décris l'infra que tu veux** dans des fichiers `.tf`, et l'outil **fait en
sorte que la réalité corresponde**. Tu ne dis pas « crée une VM » (impératif), tu
dis « je veux qu'il existe une VM comme ça » (déclaratif) — l'outil calcule quoi
créer, modifier ou détruire.

> **Analogie Kubernetes** : c'est l'esprit de `kubectl apply` sur des manifests
> YAML. Tu déclares un état désiré, le système réconcilie. OpenTofu fait pareil,
> mais pour l'infra (VM, réseau, DNS…) au lieu des pods.

---

## 2. Le vocabulaire minimal

- **Provider** : le plugin qui sait parler à un fournisseur. Ici `ovh`.
  (≈ le cloud-controller de Kube.)
- **Resource** : une chose à créer. Ici `ovh_cloud_project_instance` = l'instance.
  (≈ une ressource K8s.)
- **Variables** : les valeurs qu'on ne code pas en dur (ID projet, clé SSH…).
  Déclarées dans `variables.tf`, renseignées dans `terraform.tfvars`.
- **State** : la mémoire de l'outil — voir section 3.

---

## 3. Le *state* — la seule partie à vraiment comprendre

Après un `apply`, l'outil écrit **`terraform.tfstate`** : sa **mémoire** de ce
qu'il a créé (l'ID de l'instance chez OVH, etc.). C'est ce qui lui permet, au
prochain `apply`, de savoir « l'instance existe déjà, je n'en recrée pas une
deuxième ».

Trois règles sur le state :
- **Ne pas le supprimer** → sinon l'outil « oublie » l'instance et voudra en
  recréer une (on paierait deux fois).
- **Ne pas le committer** dans git → il peut contenir des infos sensibles.
  (Le `.gitignore` du projet le bloque déjà.)
- En **solo**, le garder en local suffit. À plusieurs, on le mettra sur un
  stockage partagé (ex. OVH Object Storage S3-compatible) — plus tard.

---

## 4. Le cycle de travail : 4 commandes

```sh
tofu init      # 1. télécharge le provider ovh (une fois, ou si la version change)
tofu plan      # 2. montre CE QU'IL VA FAIRE, sans rien toucher — l'aperçu
tofu apply     # 3. exécute réellement (demande une confirmation "yes")
tofu destroy   # 4. supprime tout ce qu'il a créé (quand on veut tout raser)
```

Le **`plan`** est le filet de sécurité : il liste chaque action avec un symbole —
- `+` = va être **créé**
- `~` = va être **modifié**
- `-` = va être **détruit**

> **Toujours lire le `plan` avant de taper `apply`.** C'est là qu'on repère une
> bêtise avant qu'elle coûte quelque chose. Rien n'est facturé tant que `apply`
> n'a pas tourné (l'instance démarre à ce moment-là).

---

## 5. Installer OpenTofu (WSL / Ubuntu)

```sh
curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh
chmod +x install-opentofu.sh
./install-opentofu.sh --install-method deb
rm install-opentofu.sh
tofu version   # vérifie l'installation
```

(Alternative Terraform : dépôt apt HashiCorp + commande `terraform`. Le code du
projet est compatible avec les deux ; on a retenu `tofu`.)

---

## 6. Le premier déploiement, pas à pas

```sh
# 1. Les clés API OVH, dans le terminal courant (elles ne sont pas stockées dans le repo) :
export OVH_ENDPOINT=ovh-eu
export OVH_APPLICATION_KEY=...
export OVH_APPLICATION_SECRET=...
export OVH_CONSUMER_KEY=...

# 2. Les variables du projet :
cd codabli-infra/tofu
cp terraform.tfvars.example terraform.tfvars
#   puis éditer terraform.tfvars : service_name, flavor_id, image_id, ssh_public_key
#   (obtention des UUID flavor/image : voir ../README.md)

# 3. Le cycle :
tofu init      # doit se terminer par "OpenTofu has been successfully initialized!"
tofu plan      # doit annoncer "Plan: 1 to add, 0 to change, 0 to destroy"
tofu apply     # taper "yes" → OVH crée la machine (~1-2 min)
```

Récupérer l'IP publique et se connecter :
```sh
tofu state show ovh_cloud_project_instance.recette   # y lire l'adresse publique
ssh ubuntu@<IP>                                       # cloud-init a déjà installé Docker
```

Tout raser (pratique tant qu'on itère, surtout en facturation `hourly`) :
```sh
tofu destroy
```

---

## 7. Les 3 réflexes de sécurité

1. **Lire le `plan`** avant chaque `apply`.
2. **Ne jamais committer** `terraform.tfstate` ni `terraform.tfvars` (déjà protégés
   par `.gitignore`).
3. `destroy` **supprime pour de vrai** — pas de corbeille. À utiliser en
   connaissance de cause.

---

## Voir aussi

- **[README.md](../README.md)** — prérequis OVH, obtention des UUID, coûts, points de vigilance.
- **[DEPLOIEMENT_RECETTE.md](DEPLOIEMENT_RECETTE.md)** — une fois la VM créée :
  l'architecture complète et comment GitHub déploie automatiquement les images dessus.
