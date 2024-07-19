import tweepy
import time
import requests

# Replace these with your own credentials
API_KEY = '2NIs89yoBYrRYdRegx4PSceG3'
API_SECRET_KEY = 'YByjH5yBoxJyYbjYT8gWZh1HYSlgaHEM5j5vicjhyX3I90NTY6'
ACCESS_TOKEN = '1813340014383886336-t4H2en8OgL5cWGvcwD764evjZzXSRm'
ACCESS_TOKEN_SECRET = 'mNyX5fTY5iyotoWGlbHG2FUYdujLM5VJBEnPXfJxwu8PO'
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAFeGuwEAAAAA4wIyathNxIVHthjYS4VKfLn9yI8%3D80G9L67SqH3OJjDT7fGEBTfyro0APLMD0PBARANMsAznmhECDX'

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
    headers = {'X-Api-Key': 'dQzp8yXeCGkVExsyZn7hGQ==AMBAWBx89bmtr4Ci'}
    response = requests.get(url, headers=headers)
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        quote = data[0]['quote']
        author = data[0]['author']
        return f"{quote} - {author}"
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
        time.sleep(3600)  # Sleep for 1 hour

if __name__ == "__main__":
    main()
