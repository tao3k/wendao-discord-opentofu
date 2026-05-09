variable "server_id" {
  description = "Discord server ID where the knowledge space will be managed."
  type        = string
}

variable "category" {
  description = "Top-level Discord category for Wendao knowledge channels."
  type = object({
    name     = optional(string, "Wendao Knowledge")
    position = optional(number, 0)
  })
  default = {}
}

variable "categories" {
  description = "Additional Discord categories managed with this knowledge space."
  type = map(object({
    name     = string
    position = optional(number)
  }))
  default = {}
}

variable "channels" {
  description = "Text channels to create under the knowledge category."
  type = map(object({
    name                     = string
    topic                    = optional(string)
    position                 = optional(number)
    nsfw                     = optional(bool, false)
    category_id              = optional(string)
    category_key             = optional(string)
    sync_perms_with_category = optional(bool, true)
  }))
  default = {
    papers = {
      name                     = "papers"
      topic                    = "Paper announcements and durable reading notes."
      position                 = 0
      sync_perms_with_category = true
    }
    discussion = {
      name                     = "paper-discussion"
      topic                    = "Discussion threads and follow-up questions for papers."
      position                 = 1
      sync_perms_with_category = true
    }
    knowledge = {
      name                     = "knowledge"
      topic                    = "Curated Wendao knowledge updates."
      position                 = 2
      sync_perms_with_category = true
    }
  }
}

variable "forum_channels" {
  description = "Forum channels to create under the knowledge category."
  type = map(object({
    name                     = string
    topic                    = optional(string)
    position                 = optional(number)
    nsfw                     = optional(bool, false)
    category_id              = optional(string)
    category_key             = optional(string)
    tags                     = optional(list(string), [])
    sync_perms_with_category = optional(bool, true)
  }))
  default = {}
}

variable "roles" {
  description = "Optional Discord roles managed with this knowledge space."
  type = map(object({
    name        = string
    color       = optional(number)
    hoist       = optional(bool, false)
    mentionable = optional(bool, false)
    permissions = optional(number)
    position    = optional(number)
  }))
  default = {}
}

variable "channel_permission_overrides" {
  description = "Optional permission overrides for managed channels."
  type = map(object({
    channel_key  = string
    type         = optional(string, "role")
    role_key     = optional(string)
    overwrite_id = optional(string)
    everyone     = optional(bool, false)
    allow        = optional(number)
    deny         = optional(number)
  }))
  default = {}

  validation {
    condition = alltrue([
      for override in values(var.channel_permission_overrides) :
      contains(concat(keys(var.channels), keys(var.forum_channels)), override.channel_key)
    ])
    error_message = "Each channel permission override must reference an existing channels key."
  }

  validation {
    condition = alltrue([
      for override in values(var.channel_permission_overrides) :
      override.role_key != null || override.overwrite_id != null || override.everyone
    ])
    error_message = "Each permission override must set role_key, overwrite_id, or everyone."
  }

  validation {
    condition = alltrue([
      for override in values(var.channel_permission_overrides) :
      contains(["role", "user"], override.type)
    ])
    error_message = "Each permission override type must be role or user."
  }

  validation {
    condition = alltrue([
      for override in values(var.channel_permission_overrides) :
      override.role_key == null || contains(keys(var.roles), override.role_key)
    ])
    error_message = "Each role_key permission override must reference an existing roles key."
  }

  validation {
    condition = alltrue([
      for override in values(var.channel_permission_overrides) :
      override.allow != null || override.deny != null
    ])
    error_message = "Each permission override must set allow, deny, or both."
  }
}

locals {
  text_channel_category_keys = [
    for channel in values(var.channels) : channel.category_key
    if channel.category_key != null
  ]
  forum_channel_category_keys = [
    for channel in values(var.forum_channels) : channel.category_key
    if channel.category_key != null
  ]
  allowed_category_keys = concat(["knowledge"], keys(var.categories))
}

check "channel_category_keys" {
  assert {
    condition = alltrue([
      for key in concat(local.text_channel_category_keys, local.forum_channel_category_keys) :
      contains(local.allowed_category_keys, key)
    ])
    error_message = "Each channel category_key must reference knowledge or an existing categories key."
  }
}
