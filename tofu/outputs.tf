output "instance_id" {
  description = "ID de l'instance créée."
  value       = ovh_cloud_project_instance.recette.id
}

# Attribut `addresses` confirmé par le plan. On sort l'ensemble des adresses
# (l'IP publique s'y trouve) — la structure exacte (ip / version) sera visible
# après le premier apply.
output "instance_addresses" {
  description = "Adresses réseau de l'instance (contient l'IP publique)."
  value       = ovh_cloud_project_instance.recette.addresses
}
