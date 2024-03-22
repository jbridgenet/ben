from gevent import monkey
monkey.patch_all()

import deck52
from util import hand_to_str
from bidding import bidding
from bots import BotBid, BotLead, CardPlayer
from nn.models import Models
import numpy as np
import sample
import shelve
import json
from bottle import Bottle, run, static_file, redirect, request

models = Models.load('../models')

app = Bottle()

DB_NAME = 'gamedb'

gg_hand = None
bb_hand = None
gg_bot = None
bb_bot = None


@app.route('/home')
def home():
    html = '<h1><a href="/app/bridge.html">Play Now</a></h1>\n'

    html += '<ul>\n'

    with shelve.open(DB_NAME) as db:
        deal_items = sorted(
            list(db.items()), key=lambda x: x[1]['timestamp'], reverse=True)

        for deal_id, deal in deal_items:
            html += '<li><span><a href="/app/viz.html?deal={}">{} {}</a></span>'.format(
                deal_id, deal['contract'], len(list(filter(lambda x: x % 2 == 1, deal['trick_winners']))))
            html += '<span><a href="/api/delete/deal/{}">delete</a></span></li>\n'.format(
                deal_id)

    html += '</ul>'
    return html


@app.route('/app/<filename>')
def frontend(filename):
    if '?' in filename:
        filename = filename[:filename.index('?')]
    return static_file(filename, root='./frontend')


@app.route('/api/deals/<deal_id>')
def deal_data(deal_id):
    db = shelve.open(DB_NAME)
    deal = db[deal_id]
    db.close()

    return json.dumps(deal)


@app.route('/api/delete/deal/<deal_id>')
def delete_deal(deal_id):
    db = shelve.open(DB_NAME)
    db.pop(deal_id)
    db.close()
    redirect('/home')


@app.route('/api/bid/2o1')
def bid_2o1():
    global gg_hand
    global bb_hand
    global gg_bot
    global bb_bot

    vuln_ns = False
    vuln_ew = False
    hand = None
    auctions = []

    try:
        nick = request.params["nick"]
        vul_ns = request.params["vul_ns"]
        vul_ew = request.params["vul_ew"]
        vuln_ns = bool(vul_ns)
        vuln_ew = bool(vul_ew)
        hand = request.params["hand"]
        auction = request.params["auction"]
        if auction:
            auctions = auction.split(',')
            txf0=isTransfer0(auctions,hand)
            if (txf0 !=None): return txf0
            else:
                txf1=isTransfer1(auctions)
                if (txf1 !=None): return txf1

    except:
        auctions = []

    if nick == 'gg_2o1':
        if gg_bot == None or gg_hand != hand:
            gg_hand = hand
            bot_bid = BotBid([vuln_ns, vuln_ew], hand, models)
            gg_bot = bot_bid
            # print('gg new hand')
        else:
            bot_bid = gg_bot
            # print('gg rebid')
    elif nick == 'bb_2o1':
        if bb_bot == None or bb_hand != hand:
            bb_hand = hand
            bot_bid = BotBid([vuln_ns, vuln_ew], hand, models)
            bb_bot = bot_bid
            # print('bb new hand')
        else:
            bot_bid = bb_bot
            # print('bb rebid')
    else:
        bot_bid = BotBid([vuln_ns, vuln_ew], hand, models)
        # print('no nick, new bid')

    bot_bid = BotBid([vuln_ns, vuln_ew], hand, models)
    bid = bot_bid.bid(auctions)

    if (bid.bid == 'PASS' and len(auctions) > 6):
        level = 0
        try:
            contract = bidding.get_contract(auctions)
            decl_i = bidding.get_decl_i(contract)
            strain_i = bidding.get_strain_i(contract)
            level = int(contract[0])
            if (strain_i < 1) or (level < 3) or (decl_i % 2 != len(auctions) % 2):
                return str(bid.bid)
        except:
            return str(bid.bid)

        dummy_i = (decl_i + 2) % 4
        if (hand == gg_hand):
            dummy_hand = gg_hand
            decl_hand = bb_hand
        else:
            dummy_hand = bb_hand
            decl_hand = gg_hand

        if decl_hand == None or dummy_hand == None:
            hands = bid.samples[0].split()
            decl_hand = hands[decl_i]
            dummy_hand = hands[dummy_i]

        decl_shdc = list(
            map(lambda x: len(x), decl_hand.split('.')))
        dummy_shdc = list(
            map(lambda x: len(x), dummy_hand.split('.')))
        dd_shdc = list(map(lambda x, y: x+y, decl_shdc, dummy_shdc))

        if (dd_shdc[strain_i-1] < 7):
            dummy_cards = dummy_hand.split('.')[strain_i-1]
            if level < 4 and hasStopper(dummy_cards):
                return f'{level}N'
            else:
                try:
                    suit_i = longSHDC(strain_i, dd_shdc)
                except:
                    return str(bid.bid)

                if suit_i > strain_i:
                    if (level > 6):
                        return f'{level}N'
                    else:
                        level += 1

                suit = ['N', 'S', 'H', 'D', 'C'][suit_i]
                return f'{level}{suit}'

    return str(bid.bid)

def isTransfer0(auctions, cards):
    length = len(auctions)
    if length < 2 or length > 7:
        return None
    else:
        bid2 = auctions[-2]
        bid1 = auctions[-1]
        if (bid2 == '1N' or bid2 == '2N'):
            if (bid1 == 'PASS'):
                if (length > 2):
                    for x in auctions[:length-2]:
                        if (x !='PASS'): return None
                    
                level2 = int(bid2[0])+1
                my_shdc = list(map(lambda x: len(x), cards.split('.')))                
                if (my_shdc[0] > 4): return f'{level2}H=txf to S'
                elif (my_shdc[1] > 4): return f'{level2}D=txf to H'
                elif (my_shdc[2] > 4): return f'{level2}NT=txf to D'
                elif (my_shdc[3] > 4): return f'{level2}S=txf to C'
                    
    return None

def isTransfer1(auctions):
    length = len(auctions)
    if length < 4:
        return None
    else:
        bid4 = auctions[-4]
        bid2 = auctions[-2]
        bid1 = auctions[-1]
        if (bid4 == '1N' or bid4 == '2N'):
            if (bid2 != 'PASS' and bid1 == 'PASS'):
                level4 = int(bid4[0])
                level2 = int(bid2[0])
                if ((level2-level4) == 1):
                    strain_i = bidding.get_strain_i(bid2)
                    if (level4==1 and strain_i==0): return f'{level2+1}D=txf!'
                    elif (level4==1 and strain_i==1): return f'{level2+1}C=txf!'
                    elif (strain_i==2): return f'{level2}S=txf!'
                    elif (strain_i==3): return f'{level2}H=txf!'
                    elif (strain_i==4): return f'{level2}D=txf!'
                    
    return None


def hasStopper(cards):
    hcp = 0
    length = len(cards)
    if length < 1:
        return False
    elif length > 4:
        return True
    else:
        for card in cards:
            if card == 'A':
                hcp += 4
            elif card == 'K':
                hcp += 3
            elif card == 'Q':
                hcp += 2
            elif card == 'J':
                hcp += 1
    return length+hcp > 4


def longSHDC(strain, shdc):
    if strain == 1:  # S
        if shdc[1] > 7:
            return 2
        elif shdc[2] > shdc[3]:
            return 3
        return 4
    elif strain == 2:  # H
        if shdc[0] > 7:
            return 1
        elif shdc[2] > shdc[3]:
            return 3
        return 4
    elif strain == 3:  # D
        if shdc[0] > shdc[1]:
            return 1
        elif shdc[1] > shdc[3]:
            return 2
        return 4
    elif strain == 4:  # C
        if shdc[0] > shdc[1]:
            return 1
        elif shdc[1] > shdc[2]:
            return 2
        return 3
    else:
        return strain


@app.route('/api/openlead')
def openingLead():
    vul_ns = request.params["vul_ns"]
    vul_ew = request.params["vul_ew"]
    vuln_ns = bool(vul_ns)
    vuln_ew = bool(vul_ew)
    hand = request.params["hand"]
    auction = request.params["auction"]

    try:
        auctions = auction.split(',')
    except:
        auctions = []

    lead_bot = BotLead([vuln_ns, vuln_ew], hand, models)
    card = lead_bot.lead(auctions).card
    return str(card)


@app.route('/api/play')
def play():
    _player_i = request.params["seat"]
    player_i = int(_player_i)-1
    _vuln_ns = request.params["vul_ns"]
    _vuln_ew = request.params["vul_ew"]
    vuln_ns = bool(_vuln_ns)
    vuln_ew = bool(_vuln_ew)
    _hands = request.params["hands"]
    hands = _hands.split(',')
    _played_cards = request.params["played"]
    played_cards = _played_cards.split(',')
    _auction = request.params["auction"]
    auction = _auction.split(',')
    contract = bidding.get_contract(auction)
    level = int(contract[0])
    strain_i = bidding.get_strain_i(contract)
    decl_i = bidding.get_decl_i(contract)
    is_decl_vuln = [vuln_ns, vuln_ew, vuln_ns, vuln_ew][decl_i]

    cardplayer_i = (player_i + 3 - decl_i) % 4
    lefty_hand = hands[(decl_i + 1) % 4]  # 0
    dummy_hand = hands[(decl_i + 2) % 4]  # 1
    righty_hand = hands[(decl_i + 3) % 4]  # 2
    decl_hand = hands[decl_i]  # 3

    card_players = [
        CardPlayer(models.player_models, 0, lefty_hand,
                   dummy_hand, contract, is_decl_vuln),
        CardPlayer(models.player_models, 1, dummy_hand,
                   decl_hand, contract, is_decl_vuln),
        CardPlayer(models.player_models, 2, righty_hand,
                   dummy_hand, contract, is_decl_vuln),
        CardPlayer(models.player_models, 3, decl_hand,
                   dummy_hand, contract, is_decl_vuln)
    ]

    player_cards_played = [[] for _ in range(4)]
    shown_out_suits = [set() for _ in range(4)]

    tricks = []
    tricks52 = []
    trick_won_by = []
    # card_responses = []
    current_trick = []
    current_trick52 = []

    leader_i = 0
    trick_i = 0
    for played_card in played_cards:
        seat_i = int(played_card[:1]) - 1
        player_i = (seat_i + 3 - decl_i) % 4
        played_card1 = played_card[1:].replace('10', 'T')
        # print(played_card,played_card1)
        card52 = deck52.encode_card(played_card1)
        card = deck52.card52to32(card52)

        if len(current_trick) % 4 == 0:
            leader_i = player_i
            lead = card

        for card_player in card_players:
            card_player.set_card_played(
                trick_i=trick_i, leader_i=leader_i, i=player_i, card=card)

        current_trick.append(card)
        current_trick52.append(card52)
        card_players[player_i].hand52[card52] -= 1
        card_players[player_i].set_own_card_played52(card52)

        if player_i == 1:
            for i in [0, 2, 3]:
                card_players[i].set_public_card_played52(card52)
        if player_i == 3:
            card_players[1].set_public_card_played52(card52)

        # update shown out state
        # card is different suit than lead card
        if card // 8 != current_trick[0] // 8:
            shown_out_suits[player_i].add(current_trick[0] // 8)

        # sanity checks after trick completed
        # assert len(current_trick) == 4
        if len(current_trick) == 4:
            # for i, card_player in enumerate(card_players):
            # assert np.min(card_player.hand52) == 0
            # assert np.min(card_player.public52) == 0
            # assert np.sum(card_player.hand52) == 13 - trick_i - 1
            # assert np.sum(card_player.public52) == 13 - trick_i - 1

            tricks.append(current_trick)
            tricks52.append(current_trick52)

            # initializing for the next trick
            # initialize hands
            if trick_i < 13:
                for i, card in enumerate(current_trick):
                    card_players[(leader_i + i) % 4].x_play[:, trick_i + 1,
                                                            0:32] = card_players[(leader_i + i) % 4].x_play[:, trick_i, 0:32]
                    card_players[(leader_i + i) % 4].x_play[:,
                                                            trick_i + 1, 0 + card] -= 1

                # initialize public hands
                for i in (0, 2, 3):
                    card_players[i].x_play[:, trick_i + 1,
                                           32:64] = card_players[1].x_play[:, trick_i + 1, 0:32]
                card_players[1].x_play[:, trick_i + 1,
                                       32:64] = card_players[3].x_play[:, trick_i + 1, 0:32]

                for card_player in card_players:
                    # initialize last trick
                    for i, card in enumerate(current_trick):
                        card_player.x_play[:, trick_i +
                                           1, 64 + i * 32 + card] = 1

                    # initialize last trick leader
                    card_player.x_play[:, trick_i + 1, 288 + leader_i] = 1

                    # initialize level
                    card_player.x_play[:, trick_i + 1, 292] = level

                    # initialize strain
                    card_player.x_play[:, trick_i + 1, 293 + strain_i] = 1

            # sanity checks for next trick
            # for i, card_player in enumerate(card_players):
            #    assert np.min(card_player.x_play[:, trick_i + 1, 0:32]) == 0
            #    assert np.min(card_player.x_play[:, trick_i + 1, 32:64]) == 0
            #    assert np.sum(
            #        card_player.x_play[:, trick_i + 1, 0:32], axis=1) == 13 - trick_i - 1
            #    assert np.sum(
            #        card_player.x_play[:, trick_i + 1, 32:64], axis=1) == 13 - trick_i - 1

            trick_winner = (
                leader_i + deck52.get_trick_winner_i(current_trick52, (strain_i - 1) % 5)) % 4
            trick_won_by.append(trick_winner)

            if trick_winner % 2 == 0:
                card_players[0].n_tricks_taken += 1
                card_players[2].n_tricks_taken += 1
            else:
                card_players[1].n_tricks_taken += 1
                card_players[3].n_tricks_taken += 1

            # update cards shown
            for i, card in enumerate(current_trick):
                player_cards_played[(leader_i + i) % 4].append(card)

            leader_i = trick_winner
            trick_i += 1
            current_trick = []
            current_trick52 = []

    rollout_states = None
    player_i = cardplayer_i
    if isinstance(card_players[player_i], CardPlayer):
        rollout_states = sample.init_rollout_states(trick_i, player_i, card_players, player_cards_played, shown_out_suits,
                                                    current_trick, 100, auction, card_players[player_i].hand.reshape((-1, 32)), [vuln_ns, vuln_ew], models)

    # card_resp = card_player.play_card(trick_i, leader_i, current_trick52, rollout_states)
    # print(player_i,trick_i, leader_i, current_trick52,played_cards, len(played_cards))
    card_resp = card_players[player_i].play_card(
        trick_i, leader_i, current_trick52, rollout_states)
    return card_resp.card.symbol()


run(app, host='0.0.0.0', port=8080, server='gevent')
