import tweepy
import time
import schedule
import requests
from dotenv import load_dotenv
import os
import anthropic
import random
import json
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Update the client initialization to use OAuth 2.0 authentication
user = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET_KEY,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

try:
    user.get_me()
    print("Authentication OK")
except tweepy.TweepyException as e:
    print("Error during authentication:", e)

print(f"Anthropic version: {anthropic.__version__}")

# File to store previous tweets
TWEET_HISTORY_FILE = 'tweet_history.json'

def load_tweet_history():
    if os.path.exists(TWEET_HISTORY_FILE):
        with open(TWEET_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_tweet_history(history):
    with open(TWEET_HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def generate_tweet():
    topics = ["software engineering", "AI", "Machine Learning", "Neural networks", "computer science", 
              "blockchain", "cybersecurity", "quantum computing", "robotics", "IoT", "5G", "edge computing", 
              "augmented reality", "virtual reality", "data science", "cloud computing"]
    
    tweet_history = load_tweet_history()
    
    # Remove tweets older than 30 days
    cutoff_date = datetime.now() - timedelta(days=30)
    tweet_history = [tweet for tweet in tweet_history if datetime.fromisoformat(tweet['date']) > cutoff_date]
    
    # Get topics not used in the last 7 days
    recent_topics = set(tweet['topic'] for tweet in tweet_history[-7:])
    available_topics = [topic for topic in topics if topic not in recent_topics]
    
    if not available_topics:
        available_topics = topics
    
    chosen_topic = random.choice(available_topics)
    
    prompt = f"""
    Create a simple, factual tweet about {chosen_topic}. The tweet should:
    1. Be a straightforward news update or fact
    2. Be based on current developments in the field
    3. Max 280 characters
    4. Use clear, concise language
    5. Avoid technical jargon where possible
    6. Include a relevant and working link to a reputable source if possible
    
    Avoid:
    - Attempts at humor or wit
    - Pop culture references or memes
    - Overly complex explanations
    - Content similar to these recent tweets: {[tweet['content'] for tweet in tweet_history[-5:]]}
    
    Format: Write as if you're a tech news outlet sharing a brief update. If you include a link, make sure it's a real, working link to a reputable source.
    """
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        temperature=0.7,
        system="You're a tech news outlet that shares brief, factual updates about technology topics. Include relevant and working links when possible.",
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
    
    # Save the new tweet to history
    tweet_history.append({
        'date': datetime.now().isoformat(),
        'topic': chosen_topic,
        'content': tweet
    })
    save_tweet_history(tweet_history)
    
    return tweet

def tweet_fact():
    tweet = generate_tweet()
    print(tweet)
    try:
        user.create_tweet(text=tweet)
        print(f"Tweeted: {tweet}")
    except Exception as e:
        print(f"An error occurred while tweeting: {e}")

def respond_to_tweet():
    try:
        # Get the most recent tweet mentioning the user
        me = user.get_me()
        mentions = user.get_users_mentions(id=me.data.id, max_results=5)
        if mentions.data:
            latest_mention = mentions.data[0]
            
            # Generate a response
            prompt = f"""
            Create a brief, friendly response to this tweet: "{latest_mention.text}"
            The response should:
            1. Be relevant to the mention
            2. Be polite and professional
            3. Max 280 characters
            4. Avoid controversial topics
            """
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                temperature=0.7,
                system="You're a friendly tech news outlet responding to mentions on Twitter. Keep responses brief, relevant, and professional.",
                messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            )
            
            reply = response.content[0].text if isinstance(response.content, list) else response.content
            
            if len(reply) > 280:
                reply = reply[:280].rsplit(' ', 1)[0]
            
            # Post the reply
            user.create_tweet(text=reply, in_reply_to_tweet_id=latest_mention.id)
            print(f"Replied to tweet: {reply}")
    except Exception as e:
        print(f"An error occurred while responding to tweet: {e}")

# Test authentication and permissions
try:
    me = user.get_me()
    print(f"Authenticated as: {me.data.username}")
    
    # Test tweet creation
    test_tweet = user.create_tweet(text="This is a test tweet. It will be deleted shortly.")
    print("Test tweet created successfully")
    
    # Delete the test tweet
    user.delete_tweet(test_tweet.data['id'])
    print("Test tweet deleted successfully")
    
except tweepy.TweepyException as e:
    print(f"Error during API test: {e}")
    if "403 Forbidden" in str(e):
        print("It seems your app doesn't have the necessary permissions. Please check your Twitter Developer Portal and ensure your app has Read and Write permissions.")

# Comment out the immediate function calls for testing
#respond_to_tweet()
# tweet_fact()

schedule.every().day.at("12:00").do(tweet_fact)
#schedule.every().day.at("18:00").do(respond_to_tweet)

while True:
    schedule.run_pending()
    time.sleep(1)
