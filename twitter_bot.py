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
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
import feedparser
import pytz

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

anthropic_client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)
ts = TimeSeries(key=ALPHA_VANTAGE_KEY, output_format='pandas')

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

TWEET_HISTORY_FILE = 'tweet_history.json'

def load_tweet_history():
    if os.path.exists(TWEET_HISTORY_FILE):
        with open(TWEET_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_tweet_history(history):
    with open(TWEET_HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def get_market_data():
    # Full list of popular tickers to track
    all_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'SPY', 'JPM', 'V', 'MA', 'DIS', 'NFLX', 'PYPL', 'CRM', 'ADBE', 'COST', 'WMT', 'PEP', 'KO', 'BAC', 'XOM', 'CVX']
    
    # Randomly select 3 tickers
    tickers = random.sample(all_tickers, 3)
    market_data = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # Add a small delay between requests
            time.sleep(1)
            info = stock.info
            market_data[ticker] = {
                'price': info.get('regularMarketPrice'),
                'volume': info.get('volume'),
                'previous_close': info.get('previousClose')
            }
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            # If we hit rate limits, wait longer before next request
            if "429" in str(e):
                time.sleep(5)
            continue
            
    return market_data

def get_economic_news():
    # RSS feeds for economic news
    feeds = [
        'https://www.cnbc.com/id/10001147/device/rss/rss.html',  # CNBC Economy News
        'https://www.economist.com/finance-and-economics/rss.xml',  # The Economist
        'https://www.bloomberg.com/feeds/economics.rss',  # Bloomberg Economics
        'https://www.wsj.com/xml/rss/3_7031.xml',  # Wall Street Journal Economy
        'https://www.ft.com/rss/markets',  # Financial Times Markets
        'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',  # Dow Jones Markets
        'https://www.reuters.com/rssFeed/businessNews',  # Reuters Business
        'https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml',  # NY Times Economy
        'https://www.marketwatch.com/rss/topstories',  # MarketWatch Top Stories
        'https://www.investing.com/rss/news.rss'  # Investing.com News
    ]
    
    news_items = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            news_items.extend(feed.entries[:5])  # Get latest 5 stories from each feed
        except Exception as e:
            print(f"Error fetching news feed {feed_url}: {e}")
    
    return news_items

def generate_tweet():
    tweet_history = load_tweet_history()
    last_tweet = tweet_history[-1] if tweet_history else None
    
    # Only fetch market data if we're going to use it
    content_types = ["market_data", "economic_news"]
    chosen_content = random.choice(content_types)
    
    if chosen_content == "market_data":
        market_data = get_market_data()
        if not market_data:  # If we couldn't get market data, fall back to news
            chosen_content = "economic_news"
    
    if chosen_content == "market_data":
        market_data = get_market_data()
        tweet_types = [
            "unusual_volume",
            "price_movement",
            "market_insight",
            "trend_analysis", 
            "sector_performance",
            "earnings_updates",
            "dividend_news",
            "market_sentiment",
            "industry_trends",
            "market_leadership"
        ]
        
        chosen_type = random.choice(tweet_types)
        
        # Avoid tweeting about the same stock as the last tweet
        last_ticker = None
        if last_tweet and 'content' in last_tweet:
            for ticker in market_data.keys():
                if f"${ticker}" in last_tweet['content']:
                    last_ticker = ticker
                    break
        
        prompt = f"""
        Generate an engaging financial market tweet based on this real-time data: {market_data}
        
        Tweet Type: {chosen_type}
        
        Additional Context:
        Last mentioned ticker: {last_ticker} (please avoid mentioning this ticker)
        
        Key Requirements:
        1. Be attention-grabbing and informative
        2. Include relevant $TICKER symbols (but not {last_ticker})
        3. Use emojis strategically (1-2 max)
        4. Add intrigue without speculation
        5. Include percentage changes or notable numbers
        6. Keep under 280 characters
        7. Use a confident, authoritative tone
        8. Include relevant hashtags like #FinTwit #Trading
        
        Style Guide:
        - Write like a market insider sharing exclusive insights
        - Create urgency without being alarmist
        - Use phrases like "Unusual activity" "Breaking" "Alert" strategically
        - End with an engaging hook or thought-provoking observation
        
        Avoid:
        - Direct investment advice
        - Speculative predictions
        - Overly technical jargon
        - Political commentary
        """
    else:
        news_items = get_economic_news()
        recent_news = random.choice(news_items) if news_items else None
        
        prompt = f"""
        Generate an engaging tweet about economic news or trends.
        
        Latest Economic News: {recent_news.title if recent_news else 'Focus on general economic trends'}
        
        Key Requirements:
        1. Be informative and insightful
        2. Include relevant economic indicators or statistics if applicable
        3. Use emojis strategically (1-2 max)
        4. Keep under 280 characters
        5. Use a confident, authoritative tone
        6. Include relevant hashtags like #Economy #Markets #GlobalTrade
        
        Style Guide:
        - Focus on macro trends and economic impacts
        - Highlight key economic indicators
        - Connect news to market implications
        - End with thought-provoking observation
        
        Avoid:
        - Political bias
        - Alarmist language
        - Overly technical terms
        - Speculative predictions
        """
    
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        temperature=0.8,
        system="You are a financial market analyst creating tweets. Follow these rules strictly:\n1. NEVER include meta-text like 'Here's a tweet about...' or 'I'm going to tweet...'\n2. Return ONLY the tweet content itself\n3. Ensure the complete thought fits within 260 characters (leaving room for hashtags)\n4. Always end with a complete sentence\n5. Use relevant hashtags and emojis strategically\n6. Maintain a professional, authoritative tone\n7. Focus on facts and data-driven insights",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extract the text content from the response
    tweet = response.content[0].text if isinstance(response.content, list) else response.content
    
    # Improved tweet length handling
    if len(tweet) > 280:
        # Try to find a natural break point
        last_period = tweet[:280].rfind('.')
        last_exclamation = tweet[:280].rfind('!')
        last_question = tweet[:280].rfind('?')
        
        # Find the last complete sentence
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > 0:
            tweet = tweet[:last_sentence_end + 1]
        else:
            # If no natural break point, regenerate the tweet
            return generate_tweet()
    
    # Ensure tweet ends with a complete sentence
    if not any(tweet.endswith(c) for c in ['.', '!', '?']):
        tweet = tweet.rstrip() + '.'
    
    tweet_history = load_tweet_history()
    tweet_history.append({
        'date': datetime.now().isoformat(),
        'type': chosen_content,
        'content': tweet
    })
    save_tweet_history(tweet_history)
    
    return tweet

def tweet_fact():
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            tweet = generate_tweet()
            print(tweet)
            user.create_tweet(text=tweet)
            print(f"Tweeted: {tweet}")
            break
        except Exception as e:
            print(f"An error occurred while tweeting (attempt {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            if retry_count < max_retries:
                print("Waiting 30 seconds before retrying...")
                time.sleep(30)
            else:
                print("Max retries reached. Could not post tweet.")

def respond_to_tweet():
    try:
        me = user.get_me()
        mentions = user.get_users_mentions(id=me.data.id, max_results=5)
        if mentions.data:
            latest_mention = mentions.data[0]
            
            prompt = f"""
            Create an engaging response to this tweet: "{latest_mention.text}"
            
            Guidelines:
            1. Show market expertise while being approachable
            2. Add value through insights or context
            3. Use relevant $TICKER symbols if applicable
            4. Keep it under 280 characters
            5. Maintain professional yet friendly tone
            6. Include an emoji if appropriate
            """
            
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                temperature=0.7,
                system="You're a market analyst engaging with your audience. Be helpful and insightful while maintaining credibility.",
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
            
            user.create_tweet(text=reply, in_reply_to_tweet_id=latest_mention.id)
            print(f"Replied to tweet: {reply}")
    except Exception as e:
        print(f"An error occurred while responding to tweet: {e}")

# Get Pacific timezone
pacific_tz = pytz.timezone('America/Los_Angeles')
current_time = datetime.now(pacific_tz)
print(f"Current time (Pacific): {current_time.strftime('%I:%M %p %Z')}")

# Remove the continuous polling and just run once
if __name__ == "__main__":
    try:
        me = user.get_me()
        print(f"Authenticated as: {me.data.username}")
        tweet_fact()
    except tweepy.TweepyException as e:
        print(f"Error during API test: {e}")
        if "403 Forbidden" in str(e):
            print("It seems your app doesn't have the necessary permissions. Please check your Twitter Developer Portal and ensure your app has Read and Write permissions.")

# Schedule the bot to tweet daily at 7:00 AM Pacific Time
schedule.every().day.at("07:00").do(tweet_fact)


while True:
    schedule.run_pending()
    time.sleep(1)
