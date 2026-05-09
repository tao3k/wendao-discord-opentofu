data "discord_permission" "publisher" {
  view_channel         = "allow"
  read_message_history = "allow"
  send_messages        = "allow"
  embed_links          = "allow"
}

module "knowledge_space" {
  source = "../../modules/knowledge_space"

  server_id = local.discord_server_id

  category = {
    name     = "Wendao Knowledge"
    position = 0
  }

  channels = {
    papers = {
      name                     = "papers"
      topic                    = "Paper announcements and durable reading notes."
      position                 = 0
      sync_perms_with_category = false
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

  forum_channels = {
    paper_discussion_forum = {
      name                     = "paper-discussion-forum"
      topic                    = "Forum posts for focused paper discussions."
      position                 = 3
      sync_perms_with_category = true
    }
  }

  roles = {
    paper_publisher = {
      name        = "Paper Publisher"
      mentionable = true
    }
  }

  channel_permission_overrides = {
    papers_publishers = {
      channel_key = "papers"
      role_key    = "paper_publisher"
      allow       = data.discord_permission.publisher.allow_bits
    }
  }
}

module "example_paper_announcement" {
  source = "../../modules/paper_announcement"

  channel_id   = module.knowledge_space.channels["papers"].id
  title        = "Attention Is All You Need"
  url          = "https://arxiv.org/abs/1706.03762"
  summary      = "A transformer architecture paper used here as a durable Discord announcement fixture."
  authors      = ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"]
  tags         = ["transformer", "attention", "paper"]
  source_label = "wendao-discord-opentofu example"
  pinned       = false
}
