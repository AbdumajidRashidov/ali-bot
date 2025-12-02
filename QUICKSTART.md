# Quick Start Guide

Get your AI-powered Excel analysis bot running in 5 minutes!

## Step 1: Install Dependencies (1 min)

```bash
cd /Users/mac/Desktop/ali-bot
pip install -r requirements.txt
```

## Step 2: Set Up Your .env File (2 min)

1. Copy the example:
```bash
cp .env.example .env
```

2. Edit `.env` and add your keys:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
```

### Where to get these keys:

**Telegram Bot Token:**
- Message [@BotFather](https://t.me/botfather) on Telegram
- Send: `/newbot`
- Follow prompts
- Copy the token

**OpenAI API Key:**
- Go to: https://platform.openai.com/api-keys
- Click "Create new secret key"
- Copy the key (starts with `sk-`)

## Step 3: Run the Bot (1 min)

```bash
python bot.py
```

You should see:
```
🤖 AI-Powered Bot is running...
📊 Features: Smart Excel Analysis, Multi-Category Reports
```

## Step 4: Test It! (1 min)

1. Open Telegram
2. Find your bot (search for the name you gave it)
3. Send: `/start`
4. Upload `May.xlsx`
5. Follow the prompts!

## Example Interaction

```
You: [upload May.xlsx]

Bot: 📥 Analyzing your file...

Bot: 📊 Analysis Options Detected:
     1️⃣ 📋 Dispatcher Earnings (6 dispatchers)
     2️⃣ 🚗 Driver Payments (15 drivers)

     Select: /analyze 1

You: /analyze 1

Bot: 💡 Configuration needed for Dispatcher Earnings
     Recommend: Percentage-based
     Accept? Reply 'yes' or send custom config

You: yes

Bot: ✅ Please provide percentages:
     Java: ?
     Baxa: ?
     ...

You: Java: 1.5
     Baxa: 1.3
     Jasur: 1.3

Bot: ✅ Configuration saved!
     🔄 Running analysis...

     [Sends weekly reports]
     [Sends overall summary]

     ✅ Analysis Complete!
```

## Troubleshooting

**"TELEGRAM_BOT_TOKEN not found"**
- Make sure `.env` file exists in `/Users/mac/Desktop/ali-bot/`
- Check that the token is on the correct line
- No quotes needed around the token

**"OpenAI API key not found"**
- Bot will still work with rule-based detection
- Add key to `.env` for AI features
- Make sure key starts with `sk-`

**Bot doesn't respond**
- Check bot is running (`python bot.py` in terminal)
- Verify token is correct
- Make sure you're messaging the right bot

## Next Steps

- Check out [README.md](README.md) for full documentation
- Try uploading different Excel files
- Configure multiple categories
- Explore `/analyze all` to run everything

## Need Help?

- Check the logs in your terminal
- Review [README.md](README.md) Troubleshooting section
- Make sure Excel files have clear column names

Happy analyzing! 📊
