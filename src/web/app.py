from flask import Flask, render_template, jsonify, request, redirect, url_for
import sys
import os
from datetime import datetime
import importlib.util
import glob
import csv
import logging
import json
import asyncio
from bs4 import BeautifulSoup
import yaml
from pathlib import Path

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Add src directory to Python path
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(src_dir)

# from agents.strategy_agent import StrategyAgent

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to track generation status
generation_progress = {
    'ml_tips': {'status': 'idle', 'progress': 0, 'message': ''},
    'tech_news': {'status': 'idle', 'progress': 0, 'message': ''}
}

# Initialize strategy agent
# strategy_agent = StrategyAgent()

def load_script(script_name):
    try:
        logger.debug(f"Loading script: {script_name}")
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                'scripts', f'{script_name}.py')
        logger.debug(f"Script path: {script_path}")
        
        if not os.path.exists(script_path):
            logger.error(f"Script file not found: {script_path}")
            raise FileNotFoundError(f"Script file not found: {script_path}")
            
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        logger.debug(f"Successfully loaded script: {script_name}")
        return module
    except Exception as e:
        logger.error(f"Error loading script {script_name}: {str(e)}")
        raise

def get_posts():
    posts = []
    
    # Get ML Tips posts
    tips_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                           'data', 'tips_posts')
    tips_metadata = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'data', 'ml_engineering_tips.csv')
    
    if os.path.exists(tips_metadata):
        with open(tips_metadata, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                post_id = row['ID']
                post_file = os.path.join(tips_dir, f"{post_id}.txt")
                if os.path.exists(post_file):
                    with open(post_file, 'r', encoding='utf-8') as pf:
                        content = pf.read()
                        posts.append({
                            'id': post_id,
                            'type': 'ML Tip',
                            'content': content,
                            'timestamp': row.get('Timestamp', ''),
                            'posted': row.get('Posted', '').lower() == 'true'
                        })
    
    # Get Tech News posts
    news_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                           'data', 'news_posts')
    news_metadata = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'data', 'posts.csv')
    
    if os.path.exists(news_metadata):
        with open(news_metadata, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                post_id = row['ID']
                post_file = os.path.join(news_dir, f"{post_id}.txt")
                if os.path.exists(post_file):
                    with open(post_file, 'r', encoding='utf-8') as pf:
                        content = pf.read()
                        posts.append({
                            'id': post_id,
                            'type': 'Tech News',
                            'content': content,
                            'title': row.get('Title', ''),
                            'source': row.get('Source', ''),
                            'timestamp': row.get('Timestamp', ''),
                            'posted': row.get('Posted', '').lower() == 'true'
                        })
    
    return sorted(posts, key=lambda x: x.get('timestamp', ''), reverse=True)

# Load content strategies
def load_strategies():
    try:
        config_path = Path("src/config/content_strategies.yaml")
        if not config_path.exists():
            return {}
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading strategies: {str(e)}")
        return {}

# Save content strategies
def save_strategies(strategies):
    try:
        config_path = Path("src/config/content_strategies.yaml")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(strategies, f, default_flow_style=False)
        return True
    except Exception as e:
        logging.error(f"Error saving strategies: {str(e)}")
        return False

@app.route('/')
def index():
    """Home page showing strategy cards."""
    strategies = load_strategies()
    return render_template('index.html', 
                         content_types=strategies.get('content_types', {}),
                         posting_schedule=strategies.get('posting_schedule', {}))

@app.route('/strategy/<strategy_name>')
def view_strategy(strategy_name):
    """Detailed view of a specific strategy."""
    strategies = load_strategies()
    strategy = strategies.get('content_types', {}).get(strategy_name, {})
    return render_template('strategy_detail.html', 
                         strategy_name=strategy_name,
                         strategy=strategy,
                         posting_schedule=strategies.get('posting_schedule', {}),
                         content_guidelines=strategies.get('content_guidelines', {}))

@app.route('/strategy/<strategy_name>/edit', methods=['GET', 'POST'])
def edit_strategy(strategy_name):
    """Edit a specific strategy."""
    strategies = load_strategies()
    
    if request.method == 'POST':
        # Update strategy
        strategy_data = request.form.to_dict()
        strategies[strategy_name] = strategy_data
        
        if save_strategies(strategies):
            return redirect(url_for('view_strategy', strategy_name=strategy_name))
        else:
            return "Error saving strategy", 500
    
    strategy = strategies.get('content_types', {}).get(strategy_name, {})
    return render_template('edit_strategy.html', 
                         strategy_name=strategy_name, 
                         strategy=strategy,
                         posting_schedule=strategies.get('posting_schedule', {}))

@app.route('/strategy/<strategy_name>/content')
def view_content(strategy_name):
    """View content for a specific strategy."""
    content_items = []
    
    # Map strategy names to their respective directories and metadata files
    strategy_configs = {
        'ml_tips': {
            'content_dir': 'data/tips_posts',
            'metadata_file': 'data/ml_engineering_tips.csv'
        },
        'tech_news': {
            'content_dir': 'data/news_posts',
            'metadata_file': 'data/posts.csv'
        }
    }
    
    config = strategy_configs.get(strategy_name)
    if not config:
        return "Strategy not found", 404
    
    # Load content from the appropriate directory
    content_dir = Path(config['content_dir'])
    metadata_file = Path(config['metadata_file'])
    
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                post_id = row['ID']
                post_file = content_dir / f"{post_id}.txt"
                
                if post_file.exists():
                    with open(post_file, 'r', encoding='utf-8') as pf:
                        content = pf.read()
                        content_items.append({
                            'id': post_id,
                            'title': row.get('Title', 'Untitled'),
                            'content': content,
                            'created_at': row.get('Timestamp', ''),
                            'status': 'posted' if row.get('Posted', '').lower() == 'true' else 'draft',
                            'source': row.get('Source', '') if strategy_name == 'tech_news' else None
                        })
    
    return render_template('content_list.html', 
                         strategy_name=strategy_name, 
                         content_items=content_items)

@app.route('/strategy/<strategy_name>/post', methods=['POST'])
def post_content(strategy_name):
    """Post content for a specific strategy."""
    content_id = request.form.get('content_id')
    if not content_id:
        return "No content ID provided", 400
    
    # TODO: Implement posting logic using the appropriate agent
    return jsonify({"status": "success", "message": "Content posted successfully"})

@app.route('/trigger/<script_name>')
def trigger_script(script_name):
    try:
        logger.debug(f"Triggering script: {script_name}")
        script = load_script(script_name)
        
        # Check if the script has a main function
        if not hasattr(script, 'main'):
            error_msg = f"Script {script_name} does not have a main function"
            logger.error(error_msg)
            return jsonify({'status': 'error', 'message': error_msg}), 500
            
        # Run the script's main function
        logger.debug(f"Running main function of {script_name}")
        try:
            script.main()
        except Exception as e:
            error_msg = f"Error executing main function of {script_name}: {str(e)}"
            logger.error(error_msg)
            return jsonify({'status': 'error', 'message': error_msg}), 500
        
        logger.info(f"Successfully executed script: {script_name}")
        return jsonify({'status': 'success', 'message': f'{script_name} executed successfully'})
    except Exception as e:
        error_msg = f"Error executing script {script_name}: {str(e)}"
        logger.error(error_msg)
        return jsonify({'status': 'error', 'message': error_msg}), 500

@app.route('/posts')
def get_posts_route():
    return jsonify(get_posts())

@app.route('/post/<post_id>', methods=['POST'])
def post_to_linkedin_endpoint(post_id):
    try:
        logger.debug(f"Attempting to post {post_id} to LinkedIn")
        
        # Get the post content
        post_type = 'ML Tip' if post_id.startswith('TIP_') else 'Tech News'
        content_type = "Tip" if post_type == 'ML Tip' else "News"
        
        # Get the content from the request
        data = request.get_json()
        if data and 'content' in data:
            # Use the edited content
            content = data['content']
            # Save the edited content to the file
            posts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                   'data', 'tips_posts' if post_type == 'ML Tip' else 'news_posts')
            post_file = os.path.join(posts_dir, f"{post_id}.txt")
            
            # Convert HTML content to plain text
            soup = BeautifulSoup(content, 'html.parser')
            plain_text = '\n'.join([p.get_text() for p in soup.find_all('p')])
            
            with open(post_file, 'w', encoding='utf-8') as f:
                f.write(plain_text)
            
            logger.info(f"Saved edited content for {post_id}")
        
        # Post to LinkedIn using the existing function
        success = asyncio.run(post_to_linkedin(post_id, content_type))
        
        if not success:
            error_msg = f"Failed to post {post_id} to LinkedIn"
            logger.error(error_msg)
            return jsonify({'status': 'error', 'message': error_msg}), 500
            
        # Mark the post as posted in the metadata
        metadata_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                   'data', 'ml_engineering_tips.csv' if post_type == 'ML Tip' else 'posts.csv')
        
        # Read the CSV file
        rows = []
        with open(metadata_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['ID'] == post_id:
                    row['Posted'] = 'true'
                rows.append(row)
        
        # Write back to CSV
        with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"Successfully posted {post_id} to LinkedIn")
        return jsonify({
            'status': 'success',
            'message': f'Successfully posted {post_id} to LinkedIn'
        })
    except Exception as e:
        error_msg = f"Error posting to LinkedIn: {str(e)}"
        logger.error(error_msg)
        return jsonify({'status': 'error', 'message': error_msg}), 500

@app.route('/strategy/<strategy_name>/generate', methods=['POST'])
def generate_content(strategy_name):
    """Generate new content for a specific strategy."""
    try:
        if strategy_name not in ['ml_tips', 'tech_news']:
            return jsonify({
                'status': 'error',
                'message': f'Unknown strategy: {strategy_name}'
            }), 400

        # Reset status
        generation_progress[strategy_name] = {
            'status': 'in_progress',
            'progress': 0,
            'message': 'Starting content generation...'
        }

        if strategy_name == 'ml_tips':
            from src.content_generators.ml_tips import main as generate_ml_tips
            # Update status for each tip
            for i in range(3):
                generation_progress[strategy_name].update({
                    'progress': (i + 1) * 33,
                    'message': f'Generating tip {i + 1}/3...'
                })
                generate_ml_tips(n=1)
        else:  # tech_news
            from src.content_generators.tech_news import generate_tech_news_content
            generation_progress[strategy_name].update({
                'progress': 20,
                'message': 'Fetching articles...'
            })
            generate_tech_news_content()

        generation_progress[strategy_name].update({
            'status': 'completed',
            'progress': 100,
            'message': 'Content generation completed!'
        })

        return jsonify({
            'status': 'success',
            'message': f'Successfully generated new content for {strategy_name}'
        })
    except Exception as e:
        logging.error(f"Error generating content: {str(e)}")
        generation_progress[strategy_name].update({
            'status': 'error',
            'message': f'Error: {str(e)}'
        })
        return jsonify({
            'status': 'error',
            'message': f'Error generating content: {str(e)}'
        }), 500

@app.route('/strategy/<strategy_name>/status')
def get_generation_status(strategy_name):
    """Get the current status of content generation."""
    if strategy_name not in generation_progress:
        return jsonify({
            'status': 'error',
            'message': f'Unknown strategy: {strategy_name}'
        }), 400
    
    return jsonify(generation_progress[strategy_name])

@app.route('/strategy/new', methods=['GET', 'POST'])
def new_strategy():
    """Create a new content strategy."""
    if request.method == 'POST':
        try:
            strategies = load_strategies()
            strategy_name = request.form.get('strategy_name', '').lower().replace(' ', '_')
            
            if not strategy_name:
                return jsonify({
                    'status': 'error',
                    'message': 'Strategy name is required'
                }), 400
                
            if strategy_name in strategies.get('content_types', {}):
                return jsonify({
                    'status': 'error',
                    'message': f'Strategy "{strategy_name}" already exists'
                }), 400
            
            # Create new strategy with default values
            new_strategy = {
                'engagement_metrics': {
                    'min_comments': 3,
                    'min_likes': 30
                },
                'format': 'article',
                'frequency': 'weekly',
                'hashtags': [None, None, None, None],
                'prompts': {
                    'system': 'You are Alex Farner, an experienced machine learning engineer and software architect who shares interesting ideas and takeaways on LinkedIn.',
                    'user': 'Write a thoughtful LinkedIn post about {topic} that feels human and conversational.'
                },
                'target_audience': 'tech professionals',
                'tone': 'professional',
                'topics': ['AI/ML', 'Cloud Computing', 'Data Engineering']
            }
            
            # Add to content types
            if 'content_types' not in strategies:
                strategies['content_types'] = {}
            strategies['content_types'][strategy_name] = new_strategy
            
            # Add to posting schedule
            if 'posting_schedule' not in strategies:
                strategies['posting_schedule'] = {}
            strategies['posting_schedule'][strategy_name] = [
                {'day': 'monday', 'time': '09:00'},
                {'day': 'wednesday', 'time': '09:00'},
                {'day': 'friday', 'time': '09:00'}
            ]
            
            if save_strategies(strategies):
                return jsonify({
                    'status': 'success',
                    'message': f'Successfully created strategy "{strategy_name}"',
                    'redirect': url_for('view_strategy', strategy_name=strategy_name)
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to save strategy'
                }), 500
                
        except Exception as e:
            logging.error(f"Error creating strategy: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error creating strategy: {str(e)}'
            }), 500
            
    return render_template('new_strategy.html')

@app.route('/strategy/chat', methods=['POST'])
def strategy_chat():
    """Handle chat messages for the strategy assistant."""
    try:
        data = request.get_json()
        message = data.get('message')
        strategy_name = data.get('strategy_name')
        current_form_data = data.get('current_form_data', {})
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
            
        # Process message with strategy agent
        # response = strategy_agent.process_message(
        #     message=message,
        #     strategy_name=strategy_name,
        #     current_form_data=current_form_data
        # )
        response = "Hello, how can I help you today?"
        
        return jsonify({
            'status': 'success',
            'message': response
        })
        
    except Exception as e:
        logger.error(f"Error in strategy chat: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing message: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003) 