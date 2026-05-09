resource "discord_category_channel" "knowledge" {
  name      = var.category.name
  server_id = var.server_id
  position  = var.category.position
}

resource "discord_role" "managed" {
  for_each = var.roles

  server_id   = var.server_id
  name        = each.value.name
  color       = each.value.color
  hoist       = each.value.hoist
  mentionable = each.value.mentionable
  permissions = each.value.permissions
  position    = each.value.position
}

resource "discord_text_channel" "managed" {
  for_each = var.channels

  name                     = each.value.name
  server_id                = var.server_id
  category                 = each.value.category_id != null ? each.value.category_id : discord_category_channel.knowledge.id
  position                 = each.value.position
  topic                    = each.value.topic
  nsfw                     = each.value.nsfw
  sync_perms_with_category = each.value.sync_perms_with_category
}

resource "discord_forum_channel" "managed" {
  for_each = var.forum_channels

  name                     = each.value.name
  server_id                = var.server_id
  category                 = each.value.category_id != null ? each.value.category_id : discord_category_channel.knowledge.id
  position                 = each.value.position
  topic                    = each.value.topic
  nsfw                     = each.value.nsfw
  sync_perms_with_category = each.value.sync_perms_with_category
}

resource "discord_channel_permission" "managed" {
  for_each = var.channel_permission_overrides

  channel_id   = try(discord_text_channel.managed[each.value.channel_key].id, discord_forum_channel.managed[each.value.channel_key].id)
  type         = each.value.type
  overwrite_id = each.value.overwrite_id != null ? each.value.overwrite_id : discord_role.managed[each.value.role_key].id
  allow        = each.value.allow
  deny         = each.value.deny
}
