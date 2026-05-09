variable "channel_id" {
  description = "Discord channel ID where the paper announcement message will be created."
  type        = string
}

variable "title" {
  description = "Paper title."
  type        = string
}

variable "url" {
  description = "Canonical paper URL, such as arXiv, DOI, project page, or PDF."
  type        = string
}

variable "summary" {
  description = "Short paper summary for the Discord embed description."
  type        = string
}

variable "authors" {
  description = "Paper author names."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Knowledge or topic tags for the paper."
  type        = list(string)
  default     = []
}

variable "source_label" {
  description = "Source label rendered in the message footer."
  type        = string
  default     = "wendao-discord-opentofu"
}

variable "content" {
  description = "Optional plain-text message content placed above the embed."
  type        = string
  default     = null
}

variable "color" {
  description = "Discord embed integer color code."
  type        = number
  default     = 3447003
}

variable "pinned" {
  description = "Whether the paper announcement message should be pinned."
  type        = bool
  default     = false
}

variable "tts" {
  description = "Whether this message triggers TTS."
  type        = bool
  default     = false
}
