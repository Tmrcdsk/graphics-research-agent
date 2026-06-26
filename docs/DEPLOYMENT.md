# Deployment

## VPS Prerequisites

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
```

## Clone and Configure

```bash
mkdir -p ~/services
cd ~/services
git clone git@github.com:<your-user>/graphics-research-agent.git
cd graphics-research-agent
cp .env.example .env
nano .env
```

Set:

- `APP_ENV=production`
- `DRY_RUN=false`
- `DEEPSEEK_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Volumes

The compose file mounts `./data:/app/data`. SQLite files are stored under `data/` and ignored by Git.

## Start and Restart

```bash
docker compose build
docker compose up -d
docker compose restart graphics-agent
```

## Logs

```bash
docker compose logs -f graphics-agent
```

Logs must not include full API keys or bot tokens.

## Manual Run

```bash
docker compose run --rm graphics-agent python -m app.main run-once
```

Run this with `DRY_RUN=true` first, then switch to `DRY_RUN=false` after checking the rendered Telegram messages.

## Update After GitHub Push

```bash
cd ~/services/graphics-research-agent
git pull
docker compose build
docker compose up -d
```
