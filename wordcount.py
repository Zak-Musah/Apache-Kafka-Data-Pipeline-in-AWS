
import faust
import asyncio
from boto3.session import Session
import boto3
import json
import os
from confluent_kafka import Consumer, Producer
from json import dumps, load
from kafka import KafkaProducer
import boto
import botocore
import re
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
S3_BUCKET = os.environ.get("S3_BUCKET")

session = Session(aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY)
s3 = session.resource('s3')
s3_bucket = s3.Bucket(S3_BUCKET)
print(s3_bucket)
# parsed_files keeps track of files already processed.
fname = "parsed.json"
parsed_files = json.load(open(fname, "r")) if os.path.isfile(fname) else []

# The faust app creates the topic word-count

app = faust.App('word-count',
                broker='kafka://localhost:9092',
                version=1,
                topic_partitions=1,
                )

# topic() method creates a topic for stream processors to read from and how the keys/values are serialization

word_count_topic = app.topic('words', value_type=str)

# Table() to define a new distributed dictionary

word_counts = app.Table('word_counts', default=int,
                        help='Keep count of words (str to int).')

#  agent() decorator to define an asynchronous stream processor. In this case the sender() feeds the word_count_topic with words
@app.agent(word_count_topic)
async def count_word_read(reads):
    async for read in reads:
        for word in read.split():
            await count_words.send(key=word, value=word)


@app.agent(value_type=str)
async def count_words(words):
    async for word in words:
        word_counts[word] += 1

#   the time decorator invokes the task at intervals of 30 seconds. sender() produces data to the output topic
@app.timer(interval=30.0)
@app.task
async def sender():
    WORDS = []
    for s3_file in s3_bucket.objects.all():

        print(s3_file.key)
        if s3_file.key in parsed_files:
            continue
        parsed_files.append(s3_file.key)
        print(parsed_files)
        obj = s3.Object(S3_BUCKET, s3_file.key)
        print(obj)
        body = obj.get()['Body'].read()
        for word in re.findall(r'\w+', body.decode('ISO-8859-1')):
            if word.isalpha():
                WORDS.append(word)

    json.dump(parsed_files, open(fname, "w+"))

    await word_count_topic.maybe_declare()
    for word in WORDS:
        await count_word_read.send(value=word)

    await asyncio.sleep(0.1)

    print(word_counts.as_ansitable(
        key='word',
        value='count',
        title='$$ TALLY $$',
        sort=True,
    ))


@app.on_rebalance_complete.connect
async def on_rebalance_complete(sender, **kwargs):
    print(word_counts.as_ansitable(
        key='word',
        value='count',
        title='$$ TALLY - after rebalance $$',
        sort=True,
    ))


if __name__ == '__main__':
    app.main()
