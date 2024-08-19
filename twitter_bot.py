import tweepy
import time
import schedule
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials from environment variables
API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)  # Import OpenAI

# Authenticate to Twitter
user = tweepy.Client(bearer_token=BEARER_TOKEN, 
                       consumer_key=API_KEY, 
                       consumer_secret=API_SECRET_KEY, 
                       access_token=ACCESS_TOKEN, 
                       access_token_secret=ACCESS_TOKEN_SECRET)

# Verify the authentication
try:
    user.get_me()
    print("Authentication OK")
except tweepy.TweepyException as e:
    print("Error during authentication:", e)

# Function to generate a tweet
def generate_tweet():
    prompt = "Share an engaging and recent fact or piece of news about software engineering or computer science. Make it Twitter-friendly: fluent, concise, and include a relevant link if possible."
    print(prompt)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  
        messages=[
            {"role": "system", "content": "You are an expert in software engineering and computer science. Create engaging and Twitter-friendly content."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=100,  # Adjust token limit to fit within character limits
        n=1,
        stop=None,
        temperature=0.7,
    )
    
    print("OpenAI Response:", response)  # Debugging output
    
    # Correctly accessing the content
    message_content = response.choices[0].message.content
    print("Message Content:", message_content)
    tweet = message_content.strip() if message_content else "Error: No response content"

    # Ensure tweet length is within the 280 character limit
    if len(tweet) > 280:
        tweet = tweet[:277] + '...'  # Trim and add ellipsis if necessary
    
    return tweet

# Function to tweet the generated content
def tweet_fact():
    tweet = generate_tweet()
    print(tweet)
    try:
        # Posting the tweet using the correct method
        user.create_tweet(text=tweet)
        print(f"Tweeted: {tweet}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Schedule the tweet_fact function to run once every 12 hours
schedule.every(12).hours.do(tweet_fact)

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
