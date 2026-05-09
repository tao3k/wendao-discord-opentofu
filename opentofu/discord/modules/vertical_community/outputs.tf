output "category" {
  description = "Managed vertical community category."
  value       = module.knowledge_space.category
}

output "channels" {
  description = "Managed vertical community text channels."
  value       = module.knowledge_space.channels
}

output "categories" {
  description = "Managed vertical community categories."
  value       = module.knowledge_space.categories
}

output "forum_channels" {
  description = "Managed vertical community forum channels."
  value       = module.knowledge_space.forum_channels
}

output "all_channels" {
  description = "Managed vertical community text and forum channels."
  value       = module.knowledge_space.all_channels
}

output "roles" {
  description = "Managed vertical community roles."
  value       = module.knowledge_space.roles
}

output "profile_projection" {
  description = "Profile metadata and managed Discord object references for Wendao receipts."
  value = {
    kind           = var.profile.kind
    name           = var.profile.name
    domain         = var.profile.domain
    review_mode    = var.profile.review_mode
    category       = module.knowledge_space.category
    categories     = module.knowledge_space.categories
    channels       = module.knowledge_space.channels
    forum_channels = module.knowledge_space.forum_channels
    roles          = module.knowledge_space.roles
    policies       = var.profile.policies
    workflows      = var.profile.workflows
  }
}
