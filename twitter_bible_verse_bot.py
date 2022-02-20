import tweepy
import scriptures
import requests
import time

# Initialization code
auth = tweepy.OAuth1UserHandler("API_KEY", "API_SECRET_KEY")

# TODO store credentials as environment variables
auth.set_access_token("ACCESS_TOKEN", "SECRET_ACCESS_TOKEN")
api = tweepy.API(auth)
url = "http://getbible.net/json"


def reply_to_tweet():
    message_when_verse_found = "Hello @{0} here is your bible text: {1}"
    message_when_verse_not_found = "Hello @{0} we can't find the bible verse, sorry!!"

    mentions = api.mentions_timeline()  # Finding mention tweets
    for mention in mentions:
        print(f"{mention.author.screen_name} - {mention.text}")
        mention_id = mention.id

        if mention.in_reply_to_status_id:
            # fetching the status
            original_tweet = api.get_status(mention.in_reply_to_status_id)

            # fetching the text from the original tweet
            text = original_tweet.text

            bible_verses_and_text = process_bible_verse(text)

            # TODO logic needs to be updated
            if bible_verses_and_text:
                for verse, text in bible_verses_and_text.items():
                    api.update_status(status=message_when_verse_found.format(mention.author.screen_name, text),
                                      in_reply_to_status_id=mention.in_reply_to_status_id,
                                      auto_populate_reply_metadata=True)
            else:
                api.update_status(status=message_when_verse_not_found.format(mention.author.screen_name),
                                  in_reply_to_status_id=mention.in_reply_to_status_id,
                                  auto_populate_reply_metadata=True)


def process_bible_verse(tweet):
    """
    extract bible verse from a given tweet and return a map of different bible verses and their text
    ex: tweet = scriptures.extract('Please read Romans 3:23 ')

    return
    {Romans 3:23 : "For all have sinned, and come short of the glory of God"}

    """
    bible_verses = scriptures.extract(tweet)

    if len(bible_verses) == 0:
        return ''

    bible_verse_text_map = {}

    for bible_verse in bible_verses:
        verse = '{0} {1}:{2}-{3}'.format(bible_verse[0][0], bible_verse[0][1], bible_verse[0][2], bible_verse[0][4])
        bible_verse_text_map[verse] = make_request_to_get_bible_text(verse)

    return bible_verse_text_map


def make_request_to_get_bible_text(verse):
    """
    @params: bible verse. ex: romans3:23
    make a request to bible api sample response: ({"book":[{"book_ref":"Ro","book_name":"Romans","book_nr":"45",
    "chapter_nr":"3","chapter":{"23":{"verse_nr":"23","verse":"For all have sinned, and come short of the glory of
    God;\r\n"}}}],"direction":"LTR","type":"verse","version":"kjv"});
    """
    PARAMS = {'passage': verse}

    # sending get request and saving the response as response object
    r = requests.get(url=url, params=PARAMS)

    # extracting data in json format
    data = r.json()
    return format_response(data)


def format_response(data):
    bible_book = data["book"]
    bible_name = bible_book[0]["bible_name"]
    chapter_number = bible_book[0]["chapter_nr"]

    chapters = bible_book[0]["chapter"]

    text_ = ''

    for key, value in chapters.iterms():
        text_ += '[{0} {1}:{2}]  {3}'.format(bible_name, key, chapter_number, value["verse'"])

    return text_


while True:
    reply_to_tweet()
    time.sleep(15)
