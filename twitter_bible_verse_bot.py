import tweepy
import scriptures
import requests
import time
import ast

# Initialization code
auth = tweepy.OAuth1UserHandler("API_KEY", "API_SECRET_KEY")

# TODO store credentials as environment variables
auth.set_access_token("ACCESS_TOKEN", "SECRET_ACCESS_TOKEN")
api = tweepy.API(auth)

url = "http://getbible.net/json"


def reply_to_tweet():
    message_when_verse_found = "Hello @{0} thanks for the mention,  here is your bible text: {1}"
    message_when_verse_not_found = "Hello @{0} sorry we couldn't find a bible verse in the tweet."

    mentions = api.mentions_timeline()  # Finding mention tweets
    for mention in mentions:
        mention_id = mention.id

        if mention.in_reply_to_status_id:

            try:

                # fetching the status
                original_tweet_id = mention.in_reply_to_status_id
                original_tweet = api.get_status(id=original_tweet_id)

                # fetching the text from the original tweet
                text = original_tweet.text
                print(f"text>>>>${text}")

                bible_verses_and_text = process_bible_verse(text)

                # TODO logic needs to be updated
                if bool(bible_verses_and_text):
                    print(f"bible_verses_and_text>>>>{bible_verses_and_text}")
                    print(f"bible_verses_and_text>>>>{bible_verses_and_text}")

                    for verse, text in bible_verses_and_text.items():
                        print(f"original_tweet>>>>>{original_tweet.screen_name}")
                        print(message_when_verse_found.format(mention.author.screen_name, text))
                        res = api.update_status(
                            status=message_when_verse_found.format(mention.author.screen_name, text),
                            in_reply_to_status_id=original_tweet_id)
                        print(f"response from request {res}")
                else:
                    print(f"There was not bible verse in the tweet: ${bible_verses_and_text}")

            except Exception as e:
                print(f"An error occurred while trying to reply to tweet, error message: {e}")


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

    try:
        PARAMS = {'passage': verse}

        # sending get request and saving the response as response object
        r = requests.get(url=url, params=PARAMS)

        # extracting data in json format
        data = r.text
        return format_response(data)

    except Exception as e:
        print(f"An error occurred when trying to get bible verse: {verse}, exception {e}")


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


while True:
    reply_to_tweet()
    time.sleep(15)
