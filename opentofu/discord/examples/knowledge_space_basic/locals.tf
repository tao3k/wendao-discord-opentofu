locals {
  discord_server_id = coalesce(var.DISCORD_SERVER_ID, var.server_id)
}
