# MarketMeNow Marketing Skills

You have access to the MarketMeNow agentic marketing framework through the `mmn` CLI. Use these tools to create and publish marketing content across social media platforms.

## Available Platforms

| Platform | CLI Namespace | Capabilities |
|----------|--------------|--------------|
| Instagram | `mmn instagram` | Reels (AI-generated from templates), Carousels (Figma export or AI-generated) |
| Twitter/X | `mmn twitter` | Engagement automation (discover posts, generate replies, post replies) |

## Common Workflows

### Generate and publish an Instagram reel

```bash
mmn instagram reel create --assignment ./image.png --template can_ai_grade_this --publish
```

### Generate an AI carousel and publish it

```bash
mmn instagram carousel generate --publish
```

### Export a Figma design as a carousel

```bash
mmn instagram carousel export --file-key <FIGMA_KEY> --publish
```

### Run Twitter/X engagement

```bash
mmn twitter login        # one-time interactive login
mmn twitter engage       # discover and reply to relevant posts
mmn twitter discover     # preview discovered posts without replying
```

### List supported platforms

```bash
mmn platforms
```

## Tips

- Always run `mmn platforms` first to check which platforms are available.
- For Instagram publishing, make sure the `.env` file has `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_BUSINESS_ACCOUNT_ID`.
- For Twitter/X, run `mmn twitter login` once to create a browser session.
- Use `--dry-run` flags when testing to avoid posting live content.
