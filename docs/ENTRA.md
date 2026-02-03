# Entra provisioning (Graph)

## Required app permissions
Use an app registration with client credentials and permissions:
- `User.ReadWrite.All`
- `Group.ReadWrite.All`
- `Directory.ReadWrite.All`

Provide:
- `ENTRA_TENANT_ID`
- `ENTRA_CLIENT_ID`
- `ENTRA_CLIENT_SECRET`

## Generate a roster
```bash
notion-synth roster generate --seed 2026 --users 50 --output roster.csv
```
Fill in `upn` and `email` for each user.

## Provision users + groups
```bash
notion-synth entra apply --roster roster.csv \
  --mode create \
  --tenant-id "$ENTRA_TENANT_ID" \
  --client-id "$ENTRA_CLIENT_ID" \
  --client-secret "$ENTRA_CLIENT_SECRET" \
  --company "Acme Robotics"
```

## Notes
- This assumes the Notion SCIM provisioning app is already configured in Entra.
- Use `--mode sync` to only map existing users/groups (no creation).
