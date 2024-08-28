import tweepy
import time
import schedule
import requests
from dotenv import load_dotenv
import os
import anthropic

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

def generate_tweet():
    prompt = """
    Create a tweet that would go viral among young tech people on Twitter. It should be:
    1. Hilarious and borderline shitpost-y
    2. Related to software engineering, coding, or tech culture
    3. Max 280 characters, including emojis
    4. Potentially include a relatable coding struggle, tech joke, or industry satire, or curses and insults
    
    Avoid:
    - Being too formal or professional
    - Using outdated references or memes
    
    Format: [Meme/Joke/Observation] [Punchline/Twist] [Emojis]
    """
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        temperature=0.9,
        system="You're a witty, sarcastic dev who's always up on the latest tech memes and Twitter trends.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    tweet = response.content[0].text.strip()
    
    tweet = tweet.strip('"')
    
    if len(tweet) > 280:
        tweet = tweet[:277] + '...'
    
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

schedule.every(8).hours.do(tweet_fact)


while True:
    schedule.run_pending()
    time.sleep(1)
