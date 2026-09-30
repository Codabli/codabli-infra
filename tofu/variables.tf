variable "ovh_endpoint" {
  description = "Endpoint API OVH (ovh-eu pour l'Europe)."
  type        = string
  default     = "ovh-eu"
}

variable "service_name" {
  description = "ID du projet Public Cloud OVH (Public Cloud > Project Management)."
  type        = string
}

variable "region" {
  description = "Région Public Cloud. Choisir une région FR pour la souveraineté (ex. GRA11, SBG5)."
  type        = string
  default     = "GRA11"
}

variable "flavor_id" {
  description = "UUID du flavor. d2-8 = 4 vCPU / 8 Go (le dimensionnement REC-US01). Voir README pour obtenir l'UUID."
  type        = string
}

variable "image_id" {
  description = "UUID de l'image système (ex. Ubuntu 24.04). Voir README pour obtenir l'UUID."
  type        = string
}

variable "instance_name" {
  description = "Nom de l'instance."
  type        = string
  default     = "codabli-recette"
}

variable "billing_period" {
  description = "hourly (souple : destroy/recreate à volonté, ~33 $/mois si allumé h24) ou monthly (~25 $/mois mais engagement au mois)."
  type        = string
  default     = "hourly"

  validation {
    condition     = contains(["hourly", "monthly"], var.billing_period)
    error_message = "billing_period doit valoir 'hourly' ou 'monthly'."
  }
}

variable "ssh_public_key" {
  description = "Contenu de ta clé PUBLIQUE SSH (ex. 'ssh-ed25519 AAAA... toi@poste'). Sert à te connecter à l'instance."
  type        = string
}
