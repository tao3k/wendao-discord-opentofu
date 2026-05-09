# Vertical Community Profile Example

This example applies a `vertical_community_profile` to Discord by using the
`vertical_community` module.

Generate a tfvars file from a user-layer profile:

```shell
direnv exec . just render-profile-tfvars examples/intents/vertical_community.healthcare.toml
```

Plan the projected community:

```shell
direnv exec . just plan-vertical-profile-example examples/intents/vertical_community.healthcare.toml
```

Apply the projected HCL structure:

```shell
direnv exec . just apply-vertical-profile-example examples/intents/vertical_community.healthcare.toml
```

The generated `.run/tfvars/vertical_community.tfvars.json` file is a runtime
artifact. Review and commit the source profile, module, and receipts instead.
