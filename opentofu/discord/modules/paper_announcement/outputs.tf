output "message" {
  description = "Managed Discord paper announcement message."
  value = {
    id         = discord_message.paper.id
    channel_id = discord_message.paper.channel_id
    server_id  = discord_message.paper.server_id
    timestamp  = discord_message.paper.timestamp
    pinned     = discord_message.paper.pinned
  }
}
