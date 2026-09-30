# Versions requises. OpenTofu (fork open source de Terraform) — commande `tofu`.
# `tofu init` téléchargera le provider OVH. Si une contrainte de version pose
# problème, vérifier la dernière version publiée du provider ovh/ovh.
terraform {
  required_version = ">= 1.6"

  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = ">= 1.2"
    }
  }
}
