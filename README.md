# AI Influencer Project

This project automates content generation, review, and posting to LinkedIn for an AI influencer. It generates both tech news summaries and ML engineering tips, sends them for review via email, and posts approved content to LinkedIn.

## Project Structure

```
.
├── src/
│   ├── content_generators/    # Content generation modules
│   │   ├── ml_tips.py        # ML tips generator
│   │   └── tech_news.py      # Tech news generator
│   ├── automation/           # Automation modules
│   │   ├── linkedin_poster.py # LinkedIn posting automation
│   │   ├── email_listener.py  # Email monitoring
│   │   └── email_options.py   # Email content handling
│   ├── utils/               # Utility functions
│   │   ├── utils.py         # Common utilities
│   │   └── scheduler.py     # Content scheduling
│   └── config/              # Configuration files
├── data/
│   ├── news_posts/         # Generated news posts
│   ├── tips_posts/         # Generated ML tips
│   └── logs/              # Log files
├── scripts/               # Utility scripts
│   ├── run_ml_tips.py    # ML tips generator script
│   ├── run_tech_news.py  # Tech news generator script
│   └── setup_launchd.sh  # Launchd setup script
├── config/               # Configuration files
│   ├── credentials.json  # Google OAuth credentials
│   └── token.json       # OAuth token
└── requirements.txt      # Python dependencies
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   LINKEDIN_EMAIL=your_linkedin_email
   LINKEDIN_PASSWORD=your_linkedin_password
   EMAIL_TO=reviewer_email
   EMAIL_FROM=your_email
   ```

3. Set up Google OAuth credentials:
   - Download credentials from Google Cloud Console
   - Save as `config/credentials.json`

## Usage

1. Generate content:
   ```bash
   python scripts/run_ml_tips.py  # Generate ML tips
   python scripts/run_tech_news.py  # Generate tech news
   ```

2. The system will:
   - Generate new content
   - Send it for review via email
   - Monitor for approval
   - Post approved content to LinkedIn

## Automation

The project includes Launchd configuration files for automated scheduling:
- `config/com.alexfarner.mltips.plist`: ML tips generation
- `config/com.alexfarner.technews.plist`: Tech news generation

To set up automation:
```bash
./scripts/setup_launchd.sh
```

## Directory Structure

- `data/news_posts/`: Generated tech news posts
- `data/tips_posts/`: Generated ML tips
- `posts.csv`: Metadata for tech news posts
- `ml_engineering_tips.csv`: Metadata for ML tips

## Files

- `scheduler.py`: Main scheduler for content generation
- `email_listener.py`: Monitors email for approvals
- `linkedin_poster.py`: Handles LinkedIn automation
- `tech_news.py`: Generates tech news content
- `ml_tips.py`: Generates ML tips content
- `email_options.py`: Handles email functionality
