module "knowledge_space" {
  source = "../knowledge_space"

  server_id                    = var.server_id
  category                     = var.profile.category
  categories                   = var.profile.categories
  channels                     = var.profile.text_channels
  forum_channels               = var.profile.forum_channels
  roles                        = var.profile.roles
  channel_permission_overrides = var.profile.channel_permission_overrides
}
