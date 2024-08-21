import tweepy
import time
import schedule
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)  

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
    #prompt = "Share an interesting or niche piece of news about software engineering or computer science and include a link where you got that information. Please include the URL at the very end of the response. Do not start it with `Did you know?` Also make it within 280 characters"
    prompt = """
    Share a fascinating, recent development or insight in software engineering or computer science. 
    Your tweet should be:
    1. Engaging and thought-provoking
    2. Concise and Twitter-friendly (max 280 characters)
    3. Include a brief explanation of why it's significant
    5. Use hashtags sparingly and relevantly (max 2)
    
    Avoid:
    - Starting with phrases like "Did you know?" or "Interesting fact:"
    - Using clickbait language
    - Mentioning a link if you can't provide a valid URL
    
    Format: [Insight/News] [Brief explanation] [Significance] [Link] [Hashtags]
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  
        messages=[
            {"role": "system", "content": "You are an expert in software engineering and computer science. Create engaging and Twitter-friendly content."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=100, 
        n=1,
        stop=None,
        temperature=0.7,
    )
    
    message_content = response.choices[0].message.content
    tweet = message_content.strip() if message_content else "Error: No response content"

    print(tweet)

    if tweet.startswith('"') and tweet.endswith('"'):
        tweet = tweet[1:]
        tweet = tweet[:-1]
    
    if tweet.startswith('[Insight]'):
        tweet = tweet[10:]

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


# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
