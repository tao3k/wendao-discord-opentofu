variable "server_id" {
  description = "Discord server ID where the vertical knowledge community will be managed."
  type        = string
}

variable "profile" {
  description = "Vertical community profile projected into Discord knowledge-space structure."
  type = object({
    kind        = optional(string, "vertical_community_profile")
    name        = string
    domain      = string
    review_mode = optional(string, "plan_then_apply")
    category = object({
      name     = string
      position = optional(number, 0)
    })
    categories = optional(map(object({
      name     = string
      position = optional(number)
    })), {})
    text_channels = optional(map(object({
      name                     = string
      topic                    = optional(string)
      position                 = optional(number)
      nsfw                     = optional(bool, false)
      category_id              = optional(string)
      category_key             = optional(string)
      sync_perms_with_category = optional(bool, true)
    })), {})
    forum_channels = optional(map(object({
      name                     = string
      topic                    = optional(string)
      position                 = optional(number)
      nsfw                     = optional(bool, false)
      category_id              = optional(string)
      category_key             = optional(string)
      tags                     = optional(list(string), [])
      sync_perms_with_category = optional(bool, true)
    })), {})
    roles = optional(map(object({
      name        = string
      color       = optional(number)
      hoist       = optional(bool, false)
      mentionable = optional(bool, false)
      permissions = optional(number)
      position    = optional(number)
    })), {})
    channel_permission_overrides = optional(map(object({
      channel_key  = string
      type         = optional(string, "role")
      role_key     = optional(string)
      overwrite_id = optional(string)
      everyone     = optional(bool, false)
      allow        = optional(number)
      deny         = optional(number)
    })), {})
    policies  = optional(map(string), {})
    workflows = optional(map(string), {})
  })

  validation {
    condition     = var.profile.kind == "vertical_community_profile"
    error_message = "profile.kind must be vertical_community_profile."
  }

  validation {
    condition     = length(var.profile.text_channels) + length(var.profile.forum_channels) > 0
    error_message = "profile must define at least one text or forum channel."
  }
}
