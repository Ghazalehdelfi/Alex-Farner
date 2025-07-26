# AI Influencer Project

An automated content generation and LinkedIn posting system that creates tech news summaries and ML engineering tips. The system uses AI agents to generate engaging content, analyze trends, and automate social media posting.

## Features

- **Content Generation**: Automated creation of ML tips and tech news posts
- **LinkedIn Automation**: Automated posting to LinkedIn using Playwright
- **AI Agents**: Multiple specialized agents for content creation and analysis
- **Performance Analytics**: Track and analyze post performance
- **Trend Analysis**: Monitor industry trends for content optimization
- **Strategy Optimization**: AI-powered content strategy recommendations

## Project Structure

```
.
├── src/
│   ├── content_generators/    # Content generation modules
│   │   ├── ml_tips.py        # ML engineering tips generator
│   │   └── tech_news.py      # Tech news content generator
│   ├── automation/           # LinkedIn automation
│   │   ├── linkedin_agents.py # LinkedIn agent classes
│   │   └── linkedin_poster.py # LinkedIn posting automation
│   ├── web/                 # Web interface
│   │   ├── app.py           # Flask web application
│   │   └── templates/       # HTML templates
│   └── config/              # Configuration files
│       └── content_strategies.yaml # Content generation strategies
├── data/
│   ├── news_posts/         # Generated tech news posts
│   ├── tips_posts/         # Generated ML tips posts
│   ├── logs/              # Application logs
│   ├── articles.csv       # Article metadata
│   ├── posts.csv          # Post metadata
│   ├── ml_engineering_tips.csv # ML tips data
│   └── top_performing_posts.csv # Performance analytics
├── tests/                 # Test files
├── config/               # Additional configuration
└── requirements.txt      # Python dependencies
```

## Setup

1. Clone the repository and navigate to the project directory

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install in development mode:
   ```bash
   pip install -e .
   ```

3. Set up environment variables in `.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   LINKEDIN_EMAIL=your_linkedin_email_here
   LINKEDIN_PASSWORD=your_linkedin_password_here
   ```

4. Install Playwright browsers (required for LinkedIn automation):
   ```bash
   playwright install
   ```

## Usage

### Content Generation

1. **Generate ML Tips**:
   ```bash
   python -m src.content_generators.ml_tips
   ```

2. **Generate Tech News**:
   ```bash
   python -m src.content_generators.tech_news
   ```

### Web Interface

Launch the Flask web application for a user-friendly interface:

```bash
python -m src.web.app
```

The web interface provides:
- **Strategy Management**: Create and edit content generation strategies
- **Content Overview**: View generated content and performance metrics
- **Real-time Generation**: Trigger content generation with progress tracking
- **Content Scheduling**: Manage posting schedules for different content types

Access the interface at `http://localhost:5000` after starting the server.

### LinkedIn Automation

1. **Post content to LinkedIn**:
   ```bash
   python -m src.automation.linkedin_poster
   ```

2. **Use LinkedIn agents for advanced automation**:
   ```bash
   python -m src.automation.linkedin_agents
   ```

### Running Tests

```bash
pytest tests/
```

## Key Components

### Content Generators
- **`src/content_generators/ml_tips.py`**: Generates ML engineering tips using OpenAI GPT models
- **`src/content_generators/tech_news.py`**: Scrapes and summarizes tech news from various sources

### Automation
- **`src/automation/linkedin_agents.py`**: LinkedIn agent classes for automated interactions
- **`src/automation/linkedin_poster.py`**: Automated LinkedIn posting using Playwright

### Web Interface
- **`src/web/app.py`**: Flask web application for content management
- **`src/web/templates/`**: HTML templates for the web interface

### Configuration
- **`src/config/content_strategies.yaml`**: Content generation strategies 

## Development
The project uses:
- **OpenAI GPT models** for content generation
- **Playwright** for web automation
- **FastAPI** for potential web interface
- **Pandas** for data management

