# Configuration du provider OVH.
#
# Les CLÉS API ne sont volontairement PAS ici : elles sont lues dans
# l'environnement pour ne jamais finir dans le dépôt. Avant `tofu plan` :
#
#   export OVH_ENDPOINT=ovh-eu
#   export OVH_APPLICATION_KEY=...
#   export OVH_APPLICATION_SECRET=...
#   export OVH_CONSUMER_KEY=...
#
# Générer ces clés sur https://api.ovh.com/createToken/ (droits sur
# /cloud/project/{serviceName}/* au minimum).
provider "ovh" {
  endpoint = var.ovh_endpoint
}
