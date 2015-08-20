import sys
import os
import sqlite3 as lite
import datetime

import pandas as pd
from textblob import TextBlob
import re

def copy_db():
    os.system("cp ~/Library/Messages/chat.db .")


# Retrieves texts from database
def fetch_data(cmd):
    db = 'chat.db'
    con = lite.connect(db)
    cur = con.cursor()
    cur.execute(cmd)
    data = cur.fetchall()
    return data


# SQL commands to fetch data for received texts
def r_cmd(number):
    return ('select chat.chat_identifier, text, is_from_me, date '
            'from message, handle, chat, chat_handle_join '
            'where chat.ROWID = chat_handle_join.chat_id '
            'and handle.ROWID = chat_handle_join.handle_id '
            'and message.handle_id = handle.ROWID '
            'and is_from_me = 0 '
            'and chat.room_name is null '
            'and handle.id = "%s" ' % number)


# SQL commands to fetch data for sent texts
def s_cmd(number):
    return ('select chat.chat_identifier, text, is_from_me, date '
            'from message, handle, chat, chat_handle_join '
            'where chat.ROWID = chat_handle_join.chat_id '
            'and handle.ROWID = chat_handle_join.handle_id '
            'and message.handle_id = handle.ROWID '
            'and is_from_me = 1 '
            'and chat.room_name is null '
            'and handle.id = "%s" ' % number)


def create_raw_dataframe(to_or_from, phone_number):
    copy_db()
    if to_or_from == "to":
        cmd = r_cmd(phone_number)
    elif to_or_from == "from":
        cmd = s_cmd(phone_number)
    else:
        print ("Please input either 'to' or 'from' into function")
    data = fetch_data(cmd)
    df = pd.DataFrame(data)
    return df


def clean_dataframe(df):
    # Fix column names
    df.columns = ["num", "text", "from", "time"]

    # Fix awful Apple dates (apparently time only started in 2001)
    d = datetime.datetime.strptime("01-01-2001", "%m-%d-%Y")
    tzoffset = datetime.timedelta(seconds=(4 * 3600))
    df['date'] = df['time'].map(lambda x: (d + datetime.timedelta(seconds=x) - tzoffset).strftime("%a, %d %b %Y"))

    # Add polarity and subjectivity columns
    df['polarity'] = df['text'].map(lambda x: TextBlob(x).sentiment.polarity)
    df['subjectivity'] = df['text'].map(lambda x: TextBlob(x).sentiment.subjectivity)

    # Create length of text column
    df['length'] = df['text'].map(lambda x: len(x))

    # Throw out what we don't need
    new_df = df[['text', 'date', 'polarity', 'subjectivity', 'length']]
    return new_df


def diagnostics(name):
    #Attitude measure
    your_polarity = s_df.polarity.mean()
    their_polarity = r_df.polarity.mean()
    if your_polarity > their_polarity:
        print "You have a better attitude than %s by %0.1f percent" % (name, (your_polarity/their_polarity)*100)
    else:
        print "%s has a better attitude than you by %0.1f percent" % (name, (their_polarity/your_polarity)*100)
    
    #Number of messages
    min_date = min(min(s_df.date), min(r_df.date))
    print 
    print "Since", min_date, "you have sent", len(s_df), "texts to", name
    print "and", name, "has sent", len(r_df), "texts to you,"
    if len(s_df) < len(r_df):
        print "You should probably message %s more." % name
    else:
        print "%s doesn't answer you a lot.  How come?" % name
        
    #Selfish factor
    s_blob = ' '.join(s_df['text'])
    r_blob = ' '.join(r_df['text'])
    s_selfish = selfish_metric(s_blob)
    r_selfish  = selfish_metric(r_blob)
    difference = s_selfish-r_selfish
    print 
    if s_selfish > 1.5:
        print "You talk about yourself a lot.  You should ask about %s more often" % name
    elif s_selfish < 0.5:
        print "You're a good listener"
    else:
        print "You do a good job of balancing talking about yourself and talking about %s" % name
    
    if difference > 0.5:
        print "%s is a much better listener than you"
        
def selfish_metric(blob):
    me = re.compile("i", re.IGNORECASE)
    you = re.compile("u", re.IGNORECASE)
    u = re.compile("you", re.IGNORECASE)
    me_count = len(re.findall(me, blob))
    you_count = len(re.findall(you, blob)) + len(re.findall(u, blob))
    return (me_count/you_count)

if __name__ == '__main__':
    copy_db()
    if len(sys.argv) > 1:
        number = sys.argv[1]
    else:
        print "Need phone number as argument, e.g. '+14356401672'"
        sys.exit()
    name = sys.argv[2]
    r_raw_df = create_raw_dataframe("to", number)
    s_raw_df = create_raw_dataframe("from", number)
    r_df = clean_dataframe(r_raw_df)
    s_df = clean_dataframe(s_raw_df)
    diagnostics(name)