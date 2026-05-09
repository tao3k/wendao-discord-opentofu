locals {
  embed_fields = concat(
    length(var.authors) > 0 ? [
      {
        name   = "Authors"
        value  = join(", ", var.authors)
        inline = false
      }
    ] : [],
    length(var.tags) > 0 ? [
      {
        name   = "Tags"
        value  = join(", ", var.tags)
        inline = false
      }
    ] : []
  )
}

resource "discord_message" "paper" {
  channel_id = var.channel_id
  content    = var.content
  pinned     = var.pinned
  tts        = var.tts

  embed {
    title       = var.title
    url         = var.url
    description = var.summary
    color       = var.color

    dynamic "fields" {
      for_each = local.embed_fields

      content {
        name   = fields.value.name
        value  = fields.value.value
        inline = fields.value.inline
      }
    }

    footer {
      text = var.source_label
    }
  }
}
