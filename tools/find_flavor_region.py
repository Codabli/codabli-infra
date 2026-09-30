#!/usr/bin/env python3
"""Scanne les régions OVH pour trouver où un flavor est EN STOCK.

Répond à l'erreur "Flavor out of stock" : liste, pour chaque région du projet,
si le flavor voulu (def. d2-8) existe et est disponible, et l'UUID du flavor +
de l'image pour cette région (les deux sont spécifiques à la région).

Utilise les mêmes clés que get_ovh_ids.py :
    OVH_ENDPOINT, OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY

Usage :
    python find_flavor_region.py
    python find_flavor_region.py --flavor d2-8 --image "Ubuntu 24.04"
    python find_flavor_region.py --project <ID>
"""
import argparse
import os
import sys

try:
    import ovh
except ImportError:
    sys.exit("La lib 'ovh' n'est pas installée : .venv/bin/pip install ovh")

# Régions FR (souveraineté) mises en avant.
FR_PREFIXES = ("GRA", "SBG", "RBX")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--flavor", default="d2-8")
    parser.add_argument("--image", default="Ubuntu 24.04")
    parser.add_argument("--project", default=None)
    parser.add_argument("--fr-only", action="store_true", help="Ne scanner que les régions FR")
    args = parser.parse_args()

    for var in ("OVH_ENDPOINT", "OVH_APPLICATION_KEY", "OVH_APPLICATION_SECRET", "OVH_CONSUMER_KEY"):
        if not os.environ.get(var):
            sys.exit(f"Variable d'environnement manquante : {var}")

    client = ovh.Client()

    projects = client.get("/cloud/project")
    project = args.project or (projects[0] if len(projects) == 1 else None)
    if not project:
        sys.exit(f"Plusieurs projets {projects} : relance avec --project <ID>.")

    regions = client.get(f"/cloud/project/{project}/region")
    if args.fr_only:
        regions = [r for r in regions if r.startswith(FR_PREFIXES)]
    # FR d'abord.
    regions.sort(key=lambda r: (not r.startswith(FR_PREFIXES), r))

    print(f"Projet : {project}")
    print(f"Recherche du flavor '{args.flavor}' + image '{args.image}'\n")
    print(f"{'région':10} {'FR':3} {'flavor':8} {'dispo':6} flavor_id")
    print("-" * 78)

    candidates = []
    for region in regions:
        fr = "oui" if region.startswith(FR_PREFIXES) else ""
        try:
            flavors = client.get(f"/cloud/project/{project}/flavor", region=region)
        except Exception as exc:
            print(f"{region:10} {fr:3} (erreur: {exc})")
            continue
        match = next((f for f in flavors if f.get("name") == args.flavor), None)
        if not match:
            print(f"{region:10} {fr:3} {'absent':8}")
            continue
        # Le champ 'available' n'est pas toujours renseigné → '?'.
        avail = match.get("available")
        avail_str = {True: "oui", False: "NON", None: "?"}[avail]
        print(f"{region:10} {fr:3} {'présent':8} {avail_str:6} {match.get('id')}")
        if avail is not False:  # on retient si dispo ou inconnu
            candidates.append((region, match.get("id"), fr == "oui"))

    if not candidates:
        sys.exit("\nAucune région avec ce flavor. Essaie un autre flavor (ex. --flavor b3-8).")

    # Choix : première région FR dispo, sinon première dispo.
    candidates.sort(key=lambda c: not c[2])
    region, flavor_id, _ = candidates[0]

    # Image pour CETTE région.
    images = client.get(f"/cloud/project/{project}/image", region=region, osType="linux")
    img = next((i for i in images if i.get("name") == args.image), None)
    if not img:
        img = next((i for i in images if args.image.lower() in (i.get("name") or "").lower()), None)
    image_id = img["id"] if img else "INTROUVABLE"

    print(f"\n>>> Suggestion : région {region}")
    print("--- À reporter dans terraform.tfvars ---")
    print(f'service_name = "{project}"')
    print(f'region       = "{region}"')
    print(f'flavor_id    = "{flavor_id}"')
    print(f'image_id     = "{image_id}"')


if __name__ == "__main__":
    main()
