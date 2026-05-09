output "knowledge_category" {
  description = "Created knowledge category."
  value       = module.knowledge_space.category
}

output "knowledge_channels" {
  description = "Created knowledge channels."
  value       = module.knowledge_space.channels
}

output "knowledge_forum_channels" {
  description = "Created knowledge forum channels."
  value       = module.knowledge_space.forum_channels
}

output "knowledge_all_channels" {
  description = "Created knowledge text and forum channels."
  value       = module.knowledge_space.all_channels
}

output "knowledge_roles" {
  description = "Created knowledge roles."
  value       = module.knowledge_space.roles
}

output "example_paper_message" {
  description = "Created example paper announcement message."
  value       = module.example_paper_announcement.message
}
