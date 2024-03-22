# Importing Necessary modules
from fastapi import FastAPI
from uvicorn import run
import os
#os.chdir('..')

import numpy as np
import tensorflow as tf
from nn.models import Models
from bots import BotBid
from bidding import bidding
from util import hand_to_str
from deck52 import random_deal
 
# Declaring our FastAPI instance
app = FastAPI()

models = Models.load('../models')

def botBid(vul, hand, auction):
    bot_bid = BotBid(vul, hand, models)

    bid = bot_bid.bid(auction)
    return bid.bid


# Defining path operation for /name endpoint
@app.get("/")
async def root():
    hello = tf.constant("hello TensorFlow!")
    version = tf. __version__
    return {"message": f"Welcome to the Food Vision API! {hello}: {version}"}

@app.get("/bid/2o1/")
async def bid(ns, ew, hand, bids):
    vuln_ns = ns == 1
    vuln_ew = ew == 1
    vul = [vuln_ns, vuln_ew]

    try:
        auction = bids.split(',')
    except IndexError:
        auction = []

    return {"bid": botBid(vul, hand, auction)}
    
if __name__ == "__main__":
	port = int(os.environ.get('PORT', 5000))
	run(app, host="0.0.0.0", port=port)