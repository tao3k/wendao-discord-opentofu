output "category" {
  description = "Managed knowledge category."
  value = {
    id         = discord_category_channel.knowledge.id
    channel_id = discord_category_channel.knowledge.channel_id
    name       = discord_category_channel.knowledge.name
  }
}

output "channels" {
  description = "Managed text channels keyed by input channel key."
  value = {
    for key, channel in discord_text_channel.managed : key => {
      id         = channel.id
      channel_id = channel.channel_id
      name       = channel.name
    }
  }
}

output "forum_channels" {
  description = "Managed forum channels keyed by input forum channel key."
  value = {
    for key, channel in discord_forum_channel.managed : key => {
      id         = channel.id
      channel_id = channel.channel_id
      name       = channel.name
    }
  }
}

output "all_channels" {
  description = "Managed text and forum channels keyed by input channel key."
  value = merge(
    {
      for key, channel in discord_text_channel.managed : key => {
        id         = channel.id
        channel_id = channel.channel_id
        name       = channel.name
        kind       = "text"
      }
    },
    {
      for key, channel in discord_forum_channel.managed : key => {
        id         = channel.id
        channel_id = channel.channel_id
        name       = channel.name
        kind       = "forum"
      }
    }
  )
}

output "roles" {
  description = "Managed roles keyed by input role key."
  value = {
    for key, role in discord_role.managed : key => {
      id   = role.id
      name = role.name
    }
  }
}
