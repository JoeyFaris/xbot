import tweepy
import time
import schedule
import requests
from dotenv import load_dotenv
import os
import anthropic
import random

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

user = tweepy.Client(bearer_token=BEARER_TOKEN, 
                       consumer_key=API_KEY, 
                       consumer_secret=API_SECRET_KEY, 
                       access_token=ACCESS_TOKEN, 
                       access_token_secret=ACCESS_TOKEN_SECRET)

try:
    user.get_me()
    print("Authentication OK")
except tweepy.TweepyException as e:
    print("Error during authentication:", e)

print(f"Anthropic version: {anthropic.__version__}")

def generate_tweet():
    topics = ["software engineering", "AI", "Machine Learning", "Neural networks", "computer science"]
    chosen_topic = random.choice(topics)
    
    prompt = f"""
    Create an informative tweet about recent news or developments in {chosen_topic}. The tweet should:
    1. Be factual and based on current events or recent advancements
    2. Be engaging and interesting to tech-savvy Twitter users
    3. Max 280 characters, including any relevant hashtags
    4. Provide a brief insight, statistic, or implication of the news
    5. Include a relevant and reputable link to the source of the information, if available
    
    Avoid:
    - Speculation or unverified information
    
    Format: [Brief news headline] [Key point or implication] [Relevant link if available] [Relevant hashtag]
    
    Note: If no relevant link is available, omit it from the tweet.
    """
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        temperature=0.9,
        system="You're a user trying to go viral on Twitter. Respond with a tweet that has a chance to go viral.",
        messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{prompt}"
                }
            ]
        }
    ]
    )
    
    tweet = response.content[0].text if isinstance(response.content, list) else response.content
    
    if len(tweet) > 280:
        tweet = tweet[:280].rsplit(' ', 1)[0]
    
    return tweet

def tweet_fact():
    tweet = generate_tweet()
    print(tweet)
    try:
        user.create_tweet(text=tweet)
        print(f"Tweeted: {tweet}")
    except Exception as e:
        print(f"An error occurred: {e}")

tweet_fact()

schedule.every().day.at("12:00").do(tweet_fact)

while True:
    schedule.run_pending()
    time.sleep(1)
