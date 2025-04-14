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
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

logger.info("Starting application initialization...")

API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

# Log environment variable status
logger.info("Checking environment variables...")
env_vars = {
    'API_KEY': bool(API_KEY),
    'API_SECRET_KEY': bool(API_SECRET_KEY),
    'ACCESS_TOKEN': bool(ACCESS_TOKEN),
    'ACCESS_TOKEN_SECRET': bool(ACCESS_TOKEN_SECRET),
    'BEARER_TOKEN': bool(BEARER_TOKEN),
    'ANTHROPIC_API_KEY': bool(ANTHROPIC_API_KEY),
    'ALPHA_VANTAGE_KEY': bool(ALPHA_VANTAGE_KEY)
}
logger.info(f"Environment variables status: {env_vars}")

try:
    anthropic_client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY
    )
    logger.info("Anthropic client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Anthropic client: {e}")

try:
    ts = TimeSeries(key=ALPHA_VANTAGE_KEY, output_format='pandas')
    logger.info("Alpha Vantage client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Alpha Vantage client: {e}")

try:
    user = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY,
        consumer_secret=API_SECRET_KEY,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )
    logger.info("Twitter client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Twitter client: {e}")

try:
    user.get_me()
    logger.info("Twitter authentication successful")
except tweepy.TweepyException as e:
    logger.error(f"Twitter authentication failed: {e}")

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
    logger.info("Fetching market data...")
    all_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'SPY', 'JPM', 'V', 'MA', 'DIS', 'NFLX', 'PYPL', 'CRM', 'ADBE', 'COST', 'WMT', 'PEP', 'KO', 'BAC', 'XOM', 'CVX']
    tickers = random.sample(all_tickers, 3)
    logger.info(f"Selected tickers: {tickers}")
    market_data = {}
    
    for ticker in tickers:
        try:
            logger.info(f"Fetching data for {ticker}...")
            # Get the latest quote data from Alpha Vantage
            data, meta_data = ts.get_quote_endpoint(symbol=ticker)
            
            if data.empty:
                logger.warning(f"No data available for {ticker}")
                continue
                
            # Extract the relevant data
            price = float(data['05. price'].iloc[0])
            volume = int(data['06. volume'].iloc[0])
            previous_close = float(data['08. previous close'].iloc[0])
            
            market_data[ticker] = {
                'price': price,
                'volume': volume,
                'previous_close': previous_close
            }
            logger.info(f"Successfully fetched data for {ticker}")
            
            # Add a small delay between requests to avoid rate limits
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            if "429" in str(e) or "Too Many Requests" in str(e):
                logger.warning(f"Rate limit hit for {ticker}, waiting 60 seconds...")
                time.sleep(60)
            continue
            
    if not market_data:
        logger.warning("No market data available, using fallback data")
        fallback_tickers = random.sample(all_tickers, 3)
        for ticker in fallback_tickers:
            market_data[ticker] = {
                'price': random.uniform(100, 500),
                'volume': random.randint(1000000, 5000000),
                'previous_close': random.uniform(100, 500)
            }
            
    return market_data

def get_economic_news():
    logger.info("Fetching economic news...")
    feeds = [
        'https://www.cnbc.com/id/10001147/device/rss/rss.html',
        'https://www.economist.com/finance-and-economics/rss.xml',
        'https://www.bloomberg.com/feeds/economics.rss',
        'https://www.wsj.com/xml/rss/3_7031.xml',
        'https://www.ft.com/rss/markets',
        'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
        'https://www.reuters.com/rssFeed/businessNews',
        'https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml',
        'https://www.marketwatch.com/rss/topstories',
        'https://www.investing.com/rss/news.rss'
    ]
    
    news_items = []
    for feed_url in feeds:
        try:
            logger.info(f"Fetching news from {feed_url}")
            feed = feedparser.parse(feed_url)
            news_items.extend(feed.entries[:5])
            logger.info(f"Successfully fetched {len(feed.entries[:5])} items from {feed_url}")
        except Exception as e:
            logger.error(f"Error fetching news feed {feed_url}: {e}")
    
    return news_items

def generate_tweet():
    logger.info("Starting tweet generation...")
    tweet_history = load_tweet_history()
    last_tweet = tweet_history[-1] if tweet_history else None
    
    content_types = ["market_data", "economic_news"]
    chosen_content = random.choice(content_types)
    logger.info(f"Chosen content type: {chosen_content}")
    
    if chosen_content == "market_data":
        market_data = get_market_data()
        if not market_data:
            logger.warning("No market data available, switching to economic news")
            chosen_content = "economic_news"
    
    try:
        if chosen_content == "market_data":
            prompt = f"""
            Generate an engaging financial market tweet based on this real-time data: {market_data}
            
            Tweet Type: {random.choice(['unusual_volume', 'price_movement', 'market_insight', 'trend_analysis', 'sector_performance', 'earnings_updates', 'dividend_news', 'market_sentiment', 'industry_trends', 'market_leadership'])}
            
            Additional Context:
            Last mentioned ticker: {last_tweet['content'] if last_tweet else 'None'} (please avoid mentioning this ticker)
            
            Key Requirements:
            1. Be attention-grabbing and informative
            2. Include relevant $TICKER symbols (but not {last_tweet['content'] if last_tweet else 'None'})
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
        
        logger.info("Generating tweet with Claude API...")
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            temperature=0.8,
            system="You are a financial market analyst creating tweets. Follow these rules strictly:\n1. NEVER include meta-text like 'Here's a tweet about...' or 'I'm going to tweet...'\n2. Return ONLY the tweet content itself\n3. Ensure the complete thought fits within 260 characters (leaving room for hashtags)\n4. Always end with a complete sentence\n5. Use relevant hashtags and emojis strategically\n6. Maintain a professional, authoritative tone\n7. Focus on facts and data-driven insights",
            messages=[{"role": "user", "content": prompt}]
        )
        
        tweet = response.content[0].text if isinstance(response.content, list) else response.content
        logger.info(f"Successfully generated tweet: {tweet[:50]}...")
        
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
        
    except Exception as e:
        logger.error(f"Error generating tweet: {e}")
        return None

def tweet_fact():
    logger.info("Starting tweet_fact function...")
    try:
        tweet = generate_tweet()
        if not tweet:
            logger.error("Failed to generate tweet")
            return
            
        logger.info("Attempting to post tweet...")
        response = user.create_tweet(text=tweet)
        logger.info(f"Successfully posted tweet: {response.data['id']}")
        
        # Update tweet history
        tweet_history = load_tweet_history()
        tweet_history.append({
            'content': tweet,
            'timestamp': datetime.now().isoformat(),
            'tweet_id': response.data['id']
        })
        save_tweet_history(tweet_history)
        logger.info("Tweet history updated successfully")
        
    except Exception as e:
        logger.error(f"Error in tweet_fact: {e}")

# Get Pacific timezone
pacific_tz = pytz.timezone('America/Los_Angeles')
current_time = datetime.now(pacific_tz)
print(f"Current time (Pacific): {current_time.strftime('%I:%M %p %Z')}")

def run_bot():
    logger.info("Starting bot scheduler...")
    try:
        # Schedule tweets at specific times throughout the day
        schedule.every().day.at("07:00").do(tweet_fact)  # 7 AM
        schedule.every().day.at("15:00").do(tweet_fact)  # 3 PM
        logger.info("Scheduled tweets for 7 AM and 3 PM Pacific Time")
        
        # Run the scheduler
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
                
    except Exception as e:
        logger.error(f"Fatal error in run_bot: {e}")

if __name__ == "__main__":
    logger.info("Starting main execution...")
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
