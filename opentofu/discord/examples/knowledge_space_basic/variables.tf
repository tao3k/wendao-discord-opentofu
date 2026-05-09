variable "DISCORD_BOT_TOKEN" {
  description = "Discord bot token without the Bot prefix. Prefer TF_VAR_DISCORD_BOT_TOKEN for local use."
  type        = string
  sensitive   = true
  default     = null
}

variable "DISCORD_SERVER_ID" {
  description = "Discord server ID to manage. Prefer TF_VAR_DISCORD_SERVER_ID for local use."
  type        = string
  default     = null
}

variable "server_id" {
  description = "Deprecated compatibility input for the Discord server ID to manage."
  type        = string
  default     = null
}
