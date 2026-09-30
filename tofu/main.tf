# Instance de recette Codabli sur OVH Public Cloud.
#
# Elle est bootstrappée par cloud-init (cloud-init.yaml) : installation de
# Docker + Docker Compose et ouverture du pare-feu (22/80/443). À l'issue du
# `tofu apply`, la machine est prête à recevoir la stack (docker compose).
resource "ovh_cloud_project_instance" "recette" {
  service_name   = var.service_name
  region         = var.region
  billing_period = var.billing_period
  name           = var.instance_name

  boot_from {
    image_id = var.image_id
  }

  flavor {
    flavor_id = var.flavor_id
  }

  # Crée la clé SSH côté OVH à partir de ta clé publique et l'injecte
  # dans l'utilisateur par défaut de l'image (ex. `ubuntu` pour Ubuntu).
  ssh_key_create {
    name       = "${var.instance_name}-key"
    public_key = var.ssh_public_key
  }

  # IP publique (nécessaire pour SSH et, plus tard, le DNS du sous-domaine).
  network {
    public = true
  }

  # Script de première initialisation (Docker, pare-feu…).
  user_data = file("${path.module}/cloud-init.yaml")
}
