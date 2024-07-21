import tweepy
import time
import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials from environment variables
API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
API_NINJAS_KEY = os.getenv('API_NINJAS_KEY')

# Authenticate to Twitter
client = tweepy.Client(bearer_token=BEARER_TOKEN, 
                       consumer_key=API_KEY, 
                       consumer_secret=API_SECRET_KEY, 
                       access_token=ACCESS_TOKEN, 
                       access_token_secret=ACCESS_TOKEN_SECRET)

# Verify the authentication
try:
    client.get_me()
    print("Authentication OK")
except tweepy.TweepyException as e:
    print("Error during authentication:", e)

def get_philosophical_quote():
    url = "https://api.api-ninjas.com/v1/quotes?category=inspirational"
    headers = {'X-Api-Key': API_NINJAS_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        quote = data[0]['quote']
        author = data[0]['author']
        return f"{quote} - {author}"
    else:
        print(f"Failed to get quote: {response.status_code}, {response.text}")
    return None

def tweet(text):
    try:
        client.create_tweet(text=text)
        print("Tweeted successfully:", text)
    except tweepy.TweepyException as e:
        print("Error tweeting:", e)

def main():
    while True:
        quote = get_philosophical_quote()
        if quote:
            tweet(quote)
        else:
            print("No new quote found at this time")
        time.sleep(28800)  # Sleep for 1 hour

if __name__ == "__main__":
    main()
