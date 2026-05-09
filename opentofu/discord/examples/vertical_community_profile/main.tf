module "vertical_community" {
  source = "../../modules/vertical_community"

  server_id = local.discord_server_id
  profile   = var.community_profile
}
