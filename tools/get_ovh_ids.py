#!/usr/bin/env python3
"""Récupère les IDs OVH nécessaires au terraform.tfvars (projet, flavor, image).

Utilise TES clés API OVH (les mêmes que pour OpenTofu), lues dans l'environnement :
    OVH_ENDPOINT, OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY

Usage :
    python get_ovh_ids.py                 # région GRA11 par défaut
    python get_ovh_ids.py --region SBG5
    python get_ovh_ids.py --project <ID>  # si tu as plusieurs projets
    python get_ovh_ids.py --flavor d2-8 --image "Ubuntu 24.04"
"""
import argparse
import os
import sys

try:
    import ovh
except ImportError:
    sys.exit("La lib 'ovh' n'est pas installée. Voir les instructions : pip install ovh")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="GRA11", help="Région Public Cloud (def. GRA11)")
    parser.add_argument("--project", default=None, help="ID de projet (sinon auto si un seul)")
    parser.add_argument("--flavor", default="d2-8", help="Nom du flavor recherché (def. d2-8)")
    parser.add_argument("--image", default="Ubuntu 24.04", help="Nom d'image recherché (def. 'Ubuntu 24.04')")
    args = parser.parse_args()

    # Le client lit les OVH_* dans l'environnement. Vérifie qu'elles sont exportées.
    for var in ("OVH_ENDPOINT", "OVH_APPLICATION_KEY", "OVH_APPLICATION_SECRET", "OVH_CONSUMER_KEY"):
        if not os.environ.get(var):
            sys.exit(f"Variable d'environnement manquante : {var}. As-tu fait les `export ...` ?")

    client = ovh.Client()

    # --- Projet(s) ---
    projects = client.get("/cloud/project")
    if not projects:
        sys.exit("Aucun projet Public Cloud trouvé sur ce compte.")

    print("Projets Public Cloud trouvés :")
    for pid in projects:
        try:
            desc = client.get(f"/cloud/project/{pid}").get("description", "")
        except Exception:
            desc = ""
        print(f"  - {pid}  {desc}")

    project = args.project or (projects[0] if len(projects) == 1 else None)
    if not project:
        sys.exit("\nPlusieurs projets : relance avec --project <ID> pour en choisir un.")
    print(f"\n>>> Projet utilisé : {project}")
    print(f">>> Région        : {args.region}\n")

    # --- Flavor ---
    flavors = client.get(f"/cloud/project/{project}/flavor", region=args.region)
    match = next((f for f in flavors if f.get("name") == args.flavor), None)
    if match:
        print(f"Flavor '{args.flavor}' : id={match['id']}  "
              f"({match.get('vcpus')} vCPU / {match.get('ram')} Mo RAM)")
        flavor_id = match["id"]
    else:
        flavor_id = "INTROUVABLE"
        print(f"⚠ Flavor '{args.flavor}' introuvable en {args.region}. "
              f"Flavors ~4 vCPU / 8 Go disponibles :")
        for f in flavors:
            if f.get("vcpus") == 4 and 7000 <= (f.get("ram") or 0) <= 9000:
                print(f"    {f.get('name'):12} id={f.get('id')}  "
                      f"({f.get('vcpus')} vCPU / {f.get('ram')} Mo)")

    # --- Image ---
    images = client.get(f"/cloud/project/{project}/image", region=args.region, osType="linux")
    match = next((i for i in images if i.get("name") == args.image), None)
    if not match:  # tolérance : match partiel (ex. "Ubuntu 24.04" présent dans le nom)
        match = next((i for i in images if args.image.lower() in (i.get("name") or "").lower()), None)
    if match:
        print(f"Image  '{match['name']}' : id={match['id']}")
        image_id = match["id"]
    else:
        image_id = "INTROUVABLE"
        print(f"⚠ Image '{args.image}' introuvable. Images Ubuntu disponibles :")
        for i in images:
            if "ubuntu" in (i.get("name") or "").lower():
                print(f"    {i.get('name'):24} id={i.get('id')}")

    # --- Bloc prêt à coller ---
    print("\n--- À reporter dans terraform.tfvars ---")
    print(f'service_name = "{project}"')
    print(f'region       = "{args.region}"')
    print(f'flavor_id    = "{flavor_id}"')
    print(f'image_id     = "{image_id}"')


if __name__ == "__main__":
    main()
