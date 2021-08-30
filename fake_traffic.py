from random import uniform, choice, randint, sample
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from time import sleep

import requests
from lxml import html
from duckduckgo_search import ddg
from google_searching import ggl
from google_trends import realtime_trends


__version__ = 0.9

THREADS = 1
MIN_WAIT = 1
MAX_WAIT = 30
DEBUG = False

BLACKLIST = ("https://t.co", "t.umblr.com", "messenger.com",
             "itunes.apple.com", "l.facebook.com", "bit.ly",
             "mediawiki", ".css", ".ico", ".xml", "intent/tweet",
             "twitter.com/share", "signup", "login", "dialog/feed?",
             ".json", ".svg", ".gif", "zendesk", "clickserve",
             "mailto:", "smart-captcha/", "Login", "mail.google.com",
             ".jpg", ".jpeg", ".png", ".iso", ".js", "s.click",
             "javascript:", "whatsapp://", "tel:", "tg://", "/#",
             "showcaptcha?", "/share.php?", "_click_", "/authorize?",
             "/join?", ".cs", "/joinchat", "/auth/", "t.me/share",
             "Special:",)

def debug_print(*agrs, **kwargs):
    if DEBUG:
        print(*agrs, **kwargs)

def real_trends(country='US', language='en-US'):
    while True:
        try:
            trends = realtime_trends(country=country, language=language, category='h', num_results=20)
            return trends
        except:
            print(f'Google trends error. Sleep 25-35 sec')
            sleep(uniform(25, 35))

def get_url(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0"}
    if 'https://' not in url and 'http://' not in url:
        url = f"https://{url}"
    try:
      url = url[:url.rindex('#')]
    except:
      pass
    debug_print(f'{url}, STATUS: request')
    try:
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            debug_print(f'{resp.url}, STATUS: {resp.status_code}')
            if any(x in resp.url for x in BLACKLIST):
                debug_print(f'{resp.url}, STATUS: in BLACKLIST')
                return None            
            return resp
        debug_print(resp.raise_for_status())      
    except requests.ConnectionError:
        debug_print(f'{url}, STATUS: Connection error. Sleep 25-35 sec')
        sleep(uniform(25, 35))
    except:
        debug_print(f'{url}, STATUS: ERROR')

def google_search(word, max_results=20):
    query  = word.replace(' ','+')
    search_ggl = ggl(query, max_results=max_results)
    urls = [x['href'].lstrip('https://') for x in search_ggl]
    return urls

def ddg_search(word, max_results=20):
    query  = word.replace(' ','+')
    search_ddg = ddg(query, max_results=max_results)
    urls = [x['href'].lstrip('https://') for x in search_ddg]
    return urls

def parse_urls(response):
    try:
        tree = html.fromstring(response.text)
        tree.make_links_absolute(response.url)
        urls = tree.xpath('//a/@href')
        urls = [url for url in urls if not any(x in url for x in BLACKLIST)]
        return urls
    except:
        return []

def recursive_browse(url, depth=randint(0, 5)):
    if not depth:
        get_url(url)
        return
    resp = get_url(url)
    if resp:
        recursive_urls = parse_urls(resp)
        if recursive_urls:
            url = choice(recursive_urls)
            sleep(uniform(MIN_WAIT, MAX_WAIT))
            recursive_browse(url, depth-1)

def _thread(trend):
    word = ' '.join(sample(trend['entity_names'], 2))
    article_urls = trend['article_urls']
    print(f"*** Trend = {word} ***")
       
    google_urls, ddg_urls = [], []
    try:
        google_urls = google_search(word)
        print(f"'{word}': google_urls len = {len(google_urls)}")
        article_urls.extend(url for url in google_urls if url not in article_urls)
    except:
        print('google search error')
    try:
        ddg_urls = ddg_search(word)
        print(f"'{word}': ddg_urls len = {len(ddg_urls)}")
        article_urls.extend(url for url in ddg_urls if url not in article_urls)
    except:
        print('ddg search error')
        
    print(f"Recursive browsing {len(article_urls)} urls. Wait...", end='\n\n')    
    for i, url in enumerate(article_urls, start=1):
        debug_print(f"{i}/{len(article_urls)} recursive browse")
        recursive_browse(url, depth=randint(max(0, 9-i), max(5, 11-i)))    
    
def fake_traffic(country='US', language='en-US', threads=THREADS, min_wait=MIN_WAIT, max_wait=MAX_WAIT, debug=DEBUG):
    """
    Imitating an Internet user by mimicking popular web traffic (internet traffic generator).
    
    country = country code ISO 3166-1 Alpha-2 code (https://www.iso.org/obp/ui/),
    language = country-language code ISO-639 and ISO-3166 (https://www.fincher.org/Utilities/CountryLanguageList.shtml),
    threads = number of threads (defaults to 1),
    min_wait = minimal delay between requests (defaults to 1),
    max_wait = maximum delay between requests (defaults to 30),
    debug = if True, then print the details of the requests (defaults to False).
    """
  
    global THREADS, MIN_WAIT, MAX_WAIT, DEBUG
    THREADS = threads
    MIN_WAIT = min_wait
    MAX_WAIT = max_wait
    DEBUG = debug
    
    print('*** Fake traffic ***')
    while True:
        print(f'\n{datetime.now()}')
        print(f'---GET TRENDS IN {country=} {language=}---')
        trends = real_trends(country=country, language=language)
        trends = sample(trends, threads)        
        with ThreadPoolExecutor(threads) as executor:
            for i, trend in enumerate(trends, start=1):
                print(f"Thread {i} start.")
                executor.submit(_thread, trend)
                sleep(uniform(25, 35))      

if __name__ == '__main__':
    fake_traffic(country='US', language='en-US')
