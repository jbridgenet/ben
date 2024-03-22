    contract = bidding.get_contract(auctions)
    level = 0
    try:
        level = int(contract[0])
    except:
        return str(bid.bid)

    if level < 2 or level > 3:  # check cuebid at level 2-3
        return str(bid.bid)

    strain_i = bidding.get_strain_i(contract)
    decl_i = bidding.get_decl_i(contract)
    last_contract = bidding.last_contract(auctions)
    if bid.bid == 'PASS':
        lastBid = isLastPass(auctions)
        if lastBid and decl_i % 2 == len(auctions) % 2:
            call = nextCall(bid)
            if call == None:
                dummy_i = (decl_i+2) % 4
                hands = bid.samples[0].split()
                decl_shdc = list(
                    map(lambda x: len(x), hands[decl_i].split('.')))
                dummy_shdc = list(
                    map(lambda x: len(x), hands[dummy_i].split('.')))
                dd_shdc = list(map(lambda x, y: x+y, decl_shdc, dummy_shdc))

                dummy_cards = hands[dummy_i].split('.')[strain_i-1]
                # print(bid.samples[0],dummy_cards)
                if hasStopper(dummy_cards):
                    bid.bid = f'{level}N'
                # elif (strain_i == 1):  # S
                else:
                    suit_i = longSHDC(strain_i, dd_shdc)
                    if suit_i > strain_i:
                        level += 1

                    suit = ['N', 'S', 'H', 'D', 'C'][suit_i]
                    bid.bid = f'{level}{suit}'

    return str(bid.bid)

def isCueBid(auction, bid):
    l = len(auction)
    if l < 3:
        return False

    auction_1 = auction[:l-1]
    auction_2 = auction[:l-2]
    contract_1 = bidding.get_contract(auction_1)
    contract_2 = bidding.get_contract(auction_2)
    level_1 = 0
    strain_1 = 0
    level_2 = 0
    strain_2 = 0

    try:    # pd's bid
        decl_1 = bidding.get_decl_i(contract_1)
        level_1 = int(contract_1[0])
        strain_1 = bidding.get_strain_i(contract_1)
        # print('1',contract_1, decl_1, level_1, strain_1)
    except:
        return False

    if strain_1 < 1:
        return False

    try:
        decl_2 = bidding.get_decl_i(contract_2)
        level_2 = int(contract_2[0])
        strain_2 = bidding.get_strain_i(contract_2)
        # print('2',contract_2, decl_2, level_2, strain_2)
        if decl_1 != decl_2:
            if strain_1 != strain_2 or (level_1-level_2) != 1:
                return False

        if l < 6:
            return False
        try:
            auction_6 = auction[:l-6]
            contract_6 = bidding.get_contract(auction_6)
            decl_6 = bidding.get_decl_i(contract_6)
            level_6 = int(contract_6[0])
            strain_6 = bidding.get_strain_i(contract_6)
            # print('6',contract_6, decl_6, level_6, strain_6)
        except:
            return False

        if strain_1 != strain_6 or (level_1-level_6) != 1:
            return False
        if decl_1 % 2 == decl_6 % 2:
            return False
    except:
        return False

    # print('cue')
    contract = bidding.get_contract(auction)
    if bid == 'PASS' and 'X' in contract:
        return False

    try:    # my bid
        level_0 = int(bid[0])
        strain_0 = bidding.get_strain_i(bid)
    except:
        level_0 = 0
        strain_0 = 0

    return strain_0 > 0 and strain_0 == strain_1 and level_0 > level_1


def isLastPass(auction):
    passes = 0
    for bid in reversed(auction):
        if bidding.is_contract(bid):
            return passes > 2
        passes += 1

    return passes > 2


def nextCall(bid):
    # print(bid.to_dict()['candidates'])
    for c in bid.to_dict()['candidates']:
        call = c['call']
        if call != 'PASS':
            return call
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
