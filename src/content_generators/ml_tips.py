import os
import csv
import logging
import openai
import random
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import uuid

from src.utils.utils import (
    setup_logging,
    setup_environment,
    ensure_directory,
    validate_config,
    with_retry,
    handle_api_error
)

# --- SETUP ---
setup_logging("data/logs/ml_tips.log")
setup_environment()

@dataclass
class Config:
    """Configuration settings for the ML tips generator."""
    output_file: str = "data/ml_engineering_tips.csv"
    tips_dir: str = "data/tips_posts"
    model: str = "gpt-4"
    temperature: float = 0.8
    max_retries: int = 3
    batch_size: int = 5

# --- TOPIC AREAS ---
TOPIC_AREAS = {
    "Data Engineering": [
        "Advanced feature engineering techniques",
        "Data pipeline optimization",
        "Data quality monitoring",
        "Real-time data processing",
        "Data versioning strategies",
        "Data validation frameworks",
        "Streaming data architectures"
    ],
    "Model Development": [
        "Model architecture optimization",
        "Hyperparameter tuning strategies",
        "Model interpretability techniques",
        "Ensemble methods in production",
        "Transfer learning patterns",
        "Model compression techniques",
        "Custom loss function design"
    ],
    "MLOps & Deployment": [
        "Production deployment patterns",
        "Model serving optimization",
        "A/B testing frameworks",
        "Canary deployment strategies",
        "Model rollback mechanisms",
        "Infrastructure as code for ML",
        "Container orchestration for ML"
    ],
    "Monitoring & Observability": [
        "Advanced model monitoring",
        "Performance metrics tracking",
        "Anomaly detection in ML systems",
        "Drift detection strategies",
        "Resource utilization monitoring",
        "Cost optimization techniques",
        "Security monitoring for ML"
    ],
    "System Design": [
        "Scalable ML architecture",
        "High-availability ML systems",
        "Fault-tolerant ML pipelines",
        "Caching strategies for ML",
        "Load balancing for ML services",
        "Multi-region ML deployments",
        "Edge ML deployment patterns"
    ],
    "Security & Compliance": [
        "ML model security",
        "Data privacy techniques",
        "Model explainability for compliance",
        "Audit trail implementation",
        "Access control for ML systems",
        "Secure model serving",
        "Compliance monitoring"
    ]
}

def get_random_topic() -> str:
    """Get a random topic from the topic areas."""
    area = random.choice(list(TOPIC_AREAS.keys()))
    topic = random.choice(TOPIC_AREAS[area])
    return f"{area}: {topic}"

# --- PROMPT ---
PROMPT_TEMPLATE = """
You're Alex Farner, a senior ML architect with 10+ years of experience. Share a high-signal, no-fluff tip about {topic}, as if speaking to another senior engineer.

- Share a non-obvious insight — something learned the hard way
- Frame it as a tradeoff or pattern, not a tutorial
- Make it punchy: ideally <200 words
- Anchor it in real production experience
- Call out subtle failure modes or hidden complexity
- Add relevant emojis to make the post engaging
- End with 3-5 relevant hashtags

Format your response like this:
[Your tip content with emojis sprinkled throughout]

#MachineLearning #MLOps #[relevant_hashtag] #[relevant_hashtag]

Avoid basic truths or generic advice. You're not trying to explain ML — you're sharing what actually matters when building and operating real-world systems.
"""

class MLTipsGenerator:
    """A class to generate and manage ML engineering tips."""
    
    def __init__(self, config: Config = Config()):
        self.config = config
        validate_config(self.config.__dict__)
        ensure_directory(self.config.tips_dir)
    
    @with_retry(max_tries=3)
    @handle_api_error
    def generate_tip(self) -> Optional[str]:
        """
        Generate a single ML engineering tip using OpenAI's API.
        
        Returns:
            Optional[str]: The generated tip or None if generation failed
        """
        topic = get_random_topic()
        prompt = PROMPT_TEMPLATE.format(topic=topic)
        
        response = openai.chat.completions.create(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are Alex Farner, a senior ML architect with 10+ years of experience in production ML systems. You share concise, high-level insights about architectural patterns and design decisions that have proven valuable in real-world scenarios. You use emojis strategically to make your posts engaging and add relevant hashtags to increase visibility.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
        )
        return response.choices[0].message.content.strip()

    def save_tips(self, tips: List[str]) -> None:
        """
        Save the generated tips to individual text files and metadata to CSV.
        
        Args:
            tips (List[str]): List of tips to save
        """
        if not tips:
            logging.warning("No tips to save.")
            return

        write_header = not os.path.exists(self.config.output_file)
        timestamp = datetime.now().isoformat()
        
        try:
            # Save metadata to CSV
            with open(self.config.output_file, "a", newline="\n", encoding="utf-8") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                if write_header:
                    writer.writerow(["ID", "Posted", "Timestamp"])
                
                # Save each tip to a separate file and record metadata
                for tip in tips:
                    tip_id = f"TIP_{uuid.uuid4().hex[:8]}"
                    tip_path = os.path.join(self.config.tips_dir, f"{tip_id}.txt")
                    
                    # Save tip content to text file
                    with open(tip_path, "w", encoding="utf-8") as tip_file:
                        tip_file.write(tip)
                    
                    # Write metadata to CSV
                    writer.writerow([tip_id, "false", timestamp])
                    
            logging.info(f"Successfully saved {len(tips)} tips to {self.config.tips_dir}")
        except IOError as e:
            logging.error(f"Failed to save tips: {str(e)}")
            raise

    def generate_batch(self, n: int) -> List[str]:
        """
        Generate a batch of ML engineering tips.
        
        Args:
            n (int): Number of tips to generate
            
        Returns:
            List[str]: List of generated tips
        """
        logging.info(f"Generating {n} ML engineering tips...")
        tips = []
        for i in range(n):
            try:
                tip = self.generate_tip()
                if tip:
                    tips.append(tip)
                    logging.debug(f"Generated tip {i+1}/{n}")
            except Exception as e:
                logging.error(f"Failed to generate tip {i+1}: {str(e)}")
                continue
        return tips

def main(n: int = 3) -> None:
    """
    Main function to generate and save ML engineering tips.
    
    Args:
        n (int): Number of tips to generate
    """
    try:
        generator = MLTipsGenerator()
        tips = generator.generate_batch(n)
        generator.save_tips(tips)
    except Exception as e:
        logging.error(f"Program failed: {str(e)}")
        raise

if __name__ == "__main__":
    main(n=3)  # Generate 3 new tips per run
