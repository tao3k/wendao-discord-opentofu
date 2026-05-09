output "community_category" {
  description = "Created vertical community category."
  value       = module.vertical_community.category
}

output "community_channels" {
  description = "Created vertical community text channels."
  value       = module.vertical_community.channels
}

output "community_categories" {
  description = "Created vertical community categories."
  value       = module.vertical_community.categories
}

output "community_forum_channels" {
  description = "Created vertical community forum channels."
  value       = module.vertical_community.forum_channels
}

output "community_all_channels" {
  description = "Created vertical community text and forum channels."
  value       = module.vertical_community.all_channels
}

output "community_roles" {
  description = "Created vertical community roles."
  value       = module.vertical_community.roles
}

output "community_profile_projection" {
  description = "Profile metadata and managed Discord object references for Wendao receipts."
  value       = module.vertical_community.profile_projection
}
