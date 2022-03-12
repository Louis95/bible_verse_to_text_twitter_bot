import os
import tweepy
import scriptures
import requests
import time
import ast
import logging
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def create_api():
    API_KEY = os.environ.get("API_KEY")
    API_SECRET_KEY = os.environ.get("API_SECRET_KEY")
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY)

    ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
    SECRET_ACCESS_TOKEN = os.environ.get("SECRET_ACCESS_TOKEN")
    auth.set_access_token(ACCESS_TOKEN, SECRET_ACCESS_TOKEN)
    api = tweepy.API(auth)

    BEARER_TOKEN = os.environ.get("BEARER_TOKEN")

    # authentication using twitter API v2
    client = tweepy.Client(BEARER_TOKEN)

    return api


def reply_to_tweet(since_id):
    api = create_api()

    message_when_verse_found = "Hello @{0} thanks for the mention,  here is your bible text: {1}"
    message_when_verse_not_found = "Hello @{0} sorry we couldn't find a bible verse in the tweet."

    new_since_id = since_id

    mentions = tweepy.Cursor(api.mentions_timeline, since_id=since_id).items()  # Finding mention tweets
    for mention in mentions:
        new_since_id = max(mention.id, since_id)
        mention_id = mention.id

        if mention.in_reply_to_status_id:

            # fetching original tweet
            original_tweet = api.get_status(mention.in_reply_to_status_id, tweet_mode='extended')

            bible_verses_and_text = process_bible_verse(original_tweet.full_text)

            # TODO logic needs to be updated
            if bool(bible_verses_and_text):

                for verse, text in bible_verses_and_text.items():
                    tweet_reply = message_when_verse_found.format(mention.author.screen_name, text)
                    res = api.update_status(
                        status=smart_truncate(text),
                        in_reply_to_status_id=mention_id, auto_populate_reply_metadata=True)
                    logging.info('response from request %s', res)
            else:
                logging.warning('There was not bible verse in the tweet %s', original_tweet.full_text)

    return new_since_id


def process_bible_verse(tweet):
    """
    extract bible verse from a given tweet and return a map of different bible verses and their text
    ex: tweet = scriptures.extract('Please read Romans 3:23 ')

    return
    {Romans 3:23 : "For all have sinned, and come short of the glory of God"}

    """
    bible_verses = scriptures.extract(tweet)

    bible_verse_text_map = {}

    for bible_verse in bible_verses:
        # check if the bible book contains a roman numeral
        bible_book_array = bible_verse[0].split(' ')

        book = bible_verse[0] if len(bible_book_array) == 1 else '{0}{1}'.format(
            romanToInt(bible_book_array[0]), bible_book_array[1])

        verse = '{0} {1}:{2}-{3}'.format(book, bible_verse[1], bible_verse[2], bible_verse[4])
        bible_text = make_request_to_get_bible_text(verse)

        bible_verse_text_map[verse] = bible_text

    return bible_verse_text_map


def make_request_to_get_bible_text(verse):
    """
    @params: bible verse. ex: romans3:23
    make a request to bible api sample response: ({"book":[{"book_ref":"Ro","book_name":"Romans","book_nr":"45",
    "chapter_nr":"3","chapter":{"23":{"verse_nr":"23","verse":"For all have sinned, and come short of the glory of
    God;\r\n"}}}],"direction":"LTR","type":"verse","version":"kjv"});
    """
    url = "http://getbible.net/json"

    try:

        # sending get request and saving the response as response object
        r = requests.get(url=url, params={'passage': verse})

        # extracting data in json format
        data = r.text
        return format_response(data)

    except Exception as e:
        logging.warning('An error occurred when trying to get bible verse: %s exception %s', verse, e)


def format_response(data):
    # remove semi-colon at the end
    data = data[:-1]
    # remove the last bracket
    data = data[:-1]
    # remove the first bracket
    data = data[1:]

    # convert response to dictionary
    data = ast.literal_eval(data)

    bible_book = data["book"]

    bible_name = bible_book[0]["book_name"]

    chapter_number = bible_book[0]["chapter_nr"]

    chapters = bible_book[0]["chapter"]

    text_ = ''

    for key, value in chapters.items():
        text_ += '[{0} {1}:{2}]  {3}'.format(bible_name, chapter_number, key, value['verse'][:-1])

    return text_


def romanToInt(roman_numeral):
    """
      :type roman_numeral: str
      :rtype: int
      """
    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000, 'IV': 4, 'IX': 9, 'XL': 40, 'XC': 90,
             'CD': 400, 'CM': 900}
    i = 0
    num = 0
    while i < len(roman_numeral):
        if i + 1 < len(roman_numeral) and roman_numeral[i:i + 2] in roman:
            num += roman[roman_numeral[i:i + 2]]
            i += 2
        else:
            num += roman[roman_numeral[i]]
            i += 1
    return num


def smart_truncate(content, length=277, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length + 1].split(' ')[0:-1]).rstrip() + suffix


# def main():
#     since_id = 1
#     while True:
#         try:
#             since_id = reply_to_tweet(since_id)
#             time.sleep(15)

#         except Exception as e:
#             logging.warning('An error occurred when trying to reply tweet: exception %s', e)


# if __name__ == "__main__":
#     main()
