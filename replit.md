# Moonlight Discord Bot

## Overview
A Discord bot with gambling features using discord.py. Includes a Flask keep-alive server for uptime monitoring.

## Project Structure
- `bot.py` - Main bot entry point
- `keep_alive.py` - Flask server for keep-alive functionality (runs on port 5000)
- `cogs/gambling.py` - Gambling commands (coinflip, daily rewards)
- `moonlight/database.py` - SQLite database operations for user balances

## Environment Variables
- `DISCORD_TOKEN` - Required. Your Discord bot token from the Discord Developer Portal.

## Running the Bot
The bot runs via `python bot.py` which:
1. Starts the Flask keep-alive server on port 5000
2. Connects to Discord using the bot token

## Commands
- `!ping` - Check if bot is alive
- `!daily` - Claim daily reward (24h cooldown)
- `!coinflip <amount> h/t` or `!cf <amount> h/t` - Flip a coin to gamble MoonShards

## Database
Uses SQLite (`moonlight.db`) to store:
- User balances
- Daily claim timestamps
