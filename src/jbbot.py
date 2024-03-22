from nn.models import Models                                                    
from bots import BotBid                                                         
                                                                                
models = Models.load('../models')                                               
                                                                                
def full_auction(e, w):                                                         
    auction = ['PAD_START']                                                                
                                                                                
    current_hand = e                                                            
    while len(auction) < 4 or set(auction[-3:]) != {'PASS'}:                    
        bot_bid = BotBid([False, False], current_hand, models)                  
        bid = bot_bid.bid(auction).bid                                          
        auction.append(bid)                                                     
        auction.append('PASS')                                                  
                                                                                
        current_hand = e if current_hand == w else e                            
                                                                                
    return auction
                                                                                
e = 'Q3.AK8743.AKQL2.'                                                          
w = 'AJ7.6.T63.Q98653'                                                          
                                                                                
print(full_auction(e, w))