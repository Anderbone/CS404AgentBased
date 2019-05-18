import socket
import random


class AuctionClient(object):
    """A client for bidding with the AucionRoom"""
    def __init__(self, host="localhost", port=8020, mybidderid=None, verbose=False):
        self.always200 = False
        self.onlyfirst = ''
        self.losesecond = False
        self.planb = ''
        self.verbose = verbose
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host,port))
        forbidden_chars = set(""" '".,;:{}[]()""")
        if mybidderid:
            if len(mybidderid) == 0 or any((c in forbidden_chars) for c in mybidderid):
                print("""mybidderid cannot contain spaces or any of the following: '".,;:{}[]()!""")
                raise ValueError
            self.mybidderid = mybidderid
        else:
            self.mybidderid = raw_input("Input team / player name : ").strip()  # this is the only thing that distinguishes the clients
            while len(self.mybidderid) == 0 or any((c in forbidden_chars) for c in self.mybidderid):
              self.mybidderid = raw_input("""You input an empty string or included a space  or one of these '".,;:{}[]() in your name which is not allowed (_ or / are all allowed)\n for example Emil_And_Nischal is okay\nInput team / player name: """).strip()
        self.sock.send(self.mybidderid.encode("utf-8"))

        data = self.sock.recv(5024).decode('utf_8')
        x = data.split(" ")
        if self.verbose:
            print("Have received response of %s" % ' '.join(x))
        if(x[0] != "Not" and len(data) != 0):
          self.numberbidders = int(x[0])
          if self.verbose:
              print("Number of bidders: %d" % self.numberbidders)
          self.numtypes = int(x[1])
          if self.verbose:
              print("Number of types: %d" % self.numtypes)
          self.numitems = int(x[2])
          if self.verbose:
              print("Items in auction: %d" % self.numitems)
          self.maxbudget = int(x[3])
          if self.verbose:
              print("Budget: %d" % self.maxbudget)
          self.neededtowin = int(x[4])
          if self.verbose:
              print("Needed to win: %d" % self.neededtowin)
          self.order_known = "True" == x[5]
          if self.verbose:
              print("Order known: %s" % self.order_known)
          self.auctionlist = []
          self.winnerpays = int(x[6])
          if self.verbose:
              print("Winner pays: %d" % self.winnerpays)
          self.values = {}
          self.artists = {}
          order_start = 7
          if self.neededtowin > 0:
              self.values = None
              for i in range(7, 7+(self.numtypes*2), 2):
                  self.artists[x[i]] = int(x[i+1])
                  order_start += 2
              if self.verbose:
                  print("Item types: %s" % str(self.artists))
          else:
              for i in range(7, 7+(self.numtypes*3), 3):
                  self.artists[x[i]] = int(x[i+1])
                  self.values[x[i]] = int(x[i+2])
                  order_start += 3
              if self.verbose:
                  print("Item types: %s" % str(self.artists))
                  print ("Values: %s" % str(self.values))

          if self.order_known:
              for i in range(order_start, order_start+self.numitems):
                  self.auctionlist.append(x[i])
              # if self.verbose:
              #     print("Auction order: %s" % str(self.auctionlist))
              print("Auction order: %s" % str(self.auctionlist))

        self.sock.send('connected '.encode("utf-8"))

        data = self.sock.recv(5024).decode('utf_8')
        x = data.split(" ")
        if x[0] != 'players':
            print("Did not receive list of players!")
            raise IOError
        if len(x) != self.numberbidders + 2:
            print("Length of list of players received does not match numberbidders!")
            raise IOError
        if self.verbose:
         print("List of players: %s" % str(' '.join(x[1:])))

        self.players = []

        for player in range(1, self.numberbidders + 1):
          self.players.append(x[player])

        self.sock.send('ready '.encode("utf-8"))

        self.standings = {name: {artist : 0 for artist in self.artists} for name in self.players}
        for name in self.players:
          self.standings[name]["money"] = self.maxbudget

    def play_auction(self):
        winnerarray = []
        winneramount = []
        done = False
        while not done:
            data = self.sock.recv(5024).decode('utf_8')
            x = data.split(" ")
            if x[0] != "done":
                if x[0] == "selling":
                    currentitem = x[1]
                    if not self.order_known:
                        self.auctionlist.append(currentitem)
                    if self.verbose:
                        print("Item on sale is %s" % currentitem)
                    bid = self.determinebid(self.numberbidders, self.neededtowin, self.artists, self.values, len(winnerarray), self.auctionlist, winnerarray, winneramount, self.mybidderid, self.players, self.standings, self.winnerpays)
                    if self.verbose:
                        print("Bidding: %d" % bid)
                    self.sock.send(str(bid).encode("utf-8"))
                    data = self.sock.recv(5024).decode('utf_8')
                    x = data.split(" ")
                    if x[0] == "draw":
                        winnerarray.append(None)
                        winneramount.append(0)
                    if x[0] == "winner":
                        winnerarray.append(x[1])
                        winneramount.append(int(x[3]))
                        self.standings[x[1]][currentitem] += 1
                        self.standings[x[1]]["money"] -= int(x[3])
            else:
                done = True
                if self.verbose:
                    if self.mybidderid in x[1:-1]:
                        print("I won! Hooray!")
                    else:
                        print("Well, better luck next time...")
        self.sock.close()

    def determinebid(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        '''You have all the variables and lists you could need in the arguments of the function,
        these will always be updated and relevant, so all you have to do is use them.
        Write code to make your bot do a lot of smart stuff to beat all the other bots. Good luck,
        and may the games begin!'''

        '''
        numberbidders is an integer displaying the amount of people playing the auction game.

        wincondition is an integer. A postiive integer means that whoever gets that amount of a single type
        of item wins, whilst 0 means each itemtype will have a value and the winner will be whoever accumulates the
        highest total value before all items are auctioned or everyone runs out of funds.

        artists will be a dict of the different item types as keys with the total number of that type on auction as elements.

        values will be a dict of the item types as keys and the type value if wincondition == 0. Else value == None.

        rd is the current round in 0 based indexing.

        itemsinauction is a list where at index "rd" the item in that round is being sold is displayed. Note that it will either be as long as the sum of all the number of the items (as in "artists") in which case the full auction order is pre-announced and known, or len(itemsinauction) == rd+1, in which case it only holds the past and current items, the next item to be auctioned is unknown.

        winnerarray is a list where at index "rd" the winner of the item sold in that round is displayed.

        winneramount is a list where at index "rd" the amount of money paid for the item sold in that round is displayed.

        example: I will now construct a sentence that would be correct if you substituted the outputs of the lists:
        In round 5 winnerarray[4] bought itemsinauction[4] for winneramount[4] pounds/dollars/money unit.

        mybidderid is your name: if you want to reference yourself use that.

        players is a list containing all the names of the current players.

        standings is a set of nested dictionaries (standings is a dictionary that for each person has another dictionary
        associated with them). standings[name][artist] will return how many paintings "artist" the player "name" currently has.
        standings[name]['money'] (remember quotes for string, important!) returns how much money the player "name" has left.

            standings[mybidderid] is the information about you.
            I.e., standings[mybidderid]['money'] is the budget you have left.

        winnerpays is an integer representing which bid the highest bidder pays. If 0, the highest bidder pays their own bid,
        but if 1, the highest bidder instead pays the second highest bid (and if 2 the third highest, ect....). Note though that if you win, you always pay at least 1 (even if the second-highest was 0).

        Don't change any of these values, or you might confuse your bot! Just use them to determine your bid.
        You can also access any of the object variables defined in the constructor (though again don't change these!), or declare your own to save state between determinebid calls if you so wish.

        determinebid should return your bid as an integer. Note that if it exceeds your current budget (standings[mybidderid]['money']), the auction server will simply set it to your current budget.

        Good luck!
        '''

        # Game 1: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order known.
        if (wincondition > 0) and (winnerpays == 0) and self.order_known:
            return self.first_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 2: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order not known.
        if (wincondition > 0) and (winnerpays == 0) and not self.order_known:
            return self.second_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 3: Highest total value wins, highest bidder pays own bid, auction order known.
        if (wincondition == 0) and (winnerpays == 0) and self.order_known:
            return self.third_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 4: Highest total value wins, highest bidder pays second highest bid, auction order known.
        if (wincondition == 0) and (winnerpays == 1) and self.order_known:
            return self.fourth_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Though you will only be assessed on these four cases, feel free to try your hand at others!
        # Otherwise, this just returns a random bid.
        return self.random_bid(standings[mybidderid]['money'])

    def random_bid(self, budget):
        """Returns a random bid between 1 and left over budget."""
        return int(budget*random.random()+1)

    def first_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 1: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order known."""
        mymoney = standings[mybidderid]['money']
        auction_length = len(itemsinauction)

        # Find out the first or second winning type(with 5 consecutive paintings), depend on the serial number
        def serial_artist(wincondition, artists, rd, itemsinauction, serial):
            auction_length = len(itemsinauction)
            artist_count = {}
            artist_flag = {}
            for j in artists:
                artist_flag[j] = 0
                artist_count[j] = 0
            for i in range(rd, auction_length):
                if i == auction_length - 1:
                    return False
                for artist in artists:
                    # if itemsinauction[i] == artist:
                    if artist_flag[artist] == 0 and itemsinauction[i] == artist:
                        artist_count[artist] += 1
                        if artist_count[artist] == wincondition:
                            # first_artist = artist
                            artist_flag[artist] = 1
                            count = 0
                            for f in artist_flag:
                                count += artist_flag[f]
                            if count == serial:
                                # print('second finish artist')
                                return artist

        # strategy 3 in report, only for two players
        if numberbidders == 2:

            # for the last one to win, return all my money left
            if standings[mybidderid][itemsinauction[rd]] == 4:
                return mymoney
            # other's id
            other = 0
            for player in players:
                if player != mybidderid:
                    other = player

            # if opponent is going to win, return his money+1
            for player in players:
                if standings[player][itemsinauction[rd]] == 4 and player != mybidderid:
                    if itemsinauction[rd] == itemsinauction[winnerarray.index(player)]:
                        return standings[player]['money'] + 1

            # use always 200 strategy for artist type planb
            if self.always200 is True and itemsinauction[rd] == self.planb:
                return 200

            # if lose the second one, target is planb, return the avg money left
            if self.losesecond is True:
                if itemsinauction[rd] == self.planb:
                    return int(mymoney/standings[mybidderid][self.planb])
                else:
                    return 0

            # check if I lose the second one (bidding = 10)
            if other in winnerarray and mybidderid in winnerarray and mymoney == 670:
                other_have = 0
                other_type = ''
                for artist in artists:
                    other_have += standings[other][artist]
                if other_have == 1:
                    other_type = winnerarray.index(other)
                if other_type == itemsinauction[winnerarray.index(mybidderid)]:
                    self.losesecond = True
                    first = serial_artist(wincondition, artists, rd, itemsinauction, 1)
                    self.planb = first
                    if itemsinauction[rd] == first:
                        return int(mymoney/wincondition - standings[mybidderid][first])
                    else:
                        return 0

            # He tryied to get the first one with more than 330.
            # If it is the first 5 winning list,
            # Focus on the one your opponent have and alwasy bid 200
            if other in winnerarray and mymoney == 1000 and standings[other]['money'] < 670:
                other_have = 0
                for artist in artists:
                    other_have += standings[other][artist]
                if other_have == 1:
                    type = winnerarray.index(other)
                    if type == self.onlyfirst:
                        self.always200 = True
                        if itemsinauction[rd] == self.onlyfirst:
                            return 200
                        else:
                            return 0

            # decide to use always 200 strategy, keep bid on what other's have if I lose the first one with bidding 200
            if self.always200 is True and mybidderid not in winnerarray and other in winnerarray:
                other_lucky = itemsinauction[winnerarray.index(other)]
                if itemsinauction[rd] == other_lucky:
                    return 200
                else:
                    return 0

            # keep bid on what I have, this is my main idea
            if mybidderid in winnerarray:
                myartist = itemsinauction[winnerarray.index(mybidderid)]
                if self.always200 is True and itemsinauction[rd] == myartist:
                    return 200
                else:
                    if itemsinauction[rd] == myartist and standings[mybidderid][myartist] == 1:
                        return 10
                    elif itemsinauction[rd] == myartist and standings[mybidderid][myartist] == 2:
                        return 220
                    elif itemsinauction[rd] == myartist and standings[mybidderid][myartist] == 3:
                        return 220
                    elif itemsinauction[rd] == myartist and standings[mybidderid][myartist] == 4:
                        return 220
                    else:
                        return 0

            # if the artist type of the first and second winning list is different,
            # suppose you get the first one, if your opponent choose to
            # bid on the next winning list, you are going to win
            first = serial_artist(wincondition, artists, rd, itemsinauction, 1)
            # print('first' + str(first))
            itemsinauction2 = itemsinauction[:]
            for i in range(rd, auction_length):
                if itemsinauction2[i] == first:
                    itemsinauction2[i] = 'no'
                    break
            second = serial_artist(wincondition, artists, rd, itemsinauction2, 1)
            # print('second'+str(second))
            if first != second:
                self.onlyfirst = first
                if itemsinauction[rd] == first:
                    return 330
                else:
                    return 0
            elif first == second:
                self.always200 = True
                self.planb = first
                if itemsinauction[rd] == self.planb:
                    return 200
                else:
                    return 0

        # strategy 2 in report, focus on the first 5
        elif 2 < numberbidders < 5:
        # elif 2 < numberbidders == 3:
            # try to make a draw if sb gonna win
            for player in players:
                if standings[player][itemsinauction[rd]] == 4 and player != mybidderid:
                    if itemsinauction[rd] == itemsinauction[winnerarray.index(player)]:
                        return standings[player]['money'] + 1

            if mybidderid in winnerarray:
                myartist = itemsinauction[winnerarray.index(mybidderid)]
                if itemsinauction[rd] == myartist:
                    return int(mymoney / (wincondition - standings[mybidderid][myartist]))
                else:
                    return 0
            else:
                # the first winning list type
                first = serial_artist(wincondition, artists, rd, itemsinauction, 1)
                if itemsinauction[rd] == first:
                    return 200
                else:
                    return 0

        # strategy 4 in report. Suppose a lot people focus on the first 5 winning list,
        # I focus on the second 5 paintings
        elif 4 < numberbidders < 30:
            # I already have paintings, still focus on that
            if mybidderid in winnerarray:
                myartist = itemsinauction[winnerarray.index(mybidderid)]
                print('my art'+str(myartist))
                print(mymoney)
                if itemsinauction[rd] == myartist:
                    return int(mymoney / (wincondition - standings[mybidderid][myartist]))
                else:
                    return 0
            else:
                # Find which artist to focus now, the second 5 winning list
                first_art = serial_artist(wincondition, artists, rd, itemsinauction, 2)
                print('first art'+(first_art))

                if first_art is False:
                    print('not possible')
                    # no second winning list, find first 5
                    first_art = serial_artist(wincondition, artists, rd, itemsinauction, 1)
                    if first_art is False:
                        for player in players:
                            # print('could not win now, try to make a draw')
                            if standings[player][itemsinauction[rd]] == 4 and player != mybidderid:
                                if itemsinauction[rd] == itemsinauction[winnerarray.index(player)]:
                                    return standings[player]['money'] + 1

                if first_art == itemsinauction[rd]:
                    return 200
                else:
                    return 0

        # Strategy 1 in report. longer consideration
        elif numberbidders >= 30:
            if mybidderid in winnerarray:
                myartist = itemsinauction[winnerarray.index(mybidderid)]
                if itemsinauction[rd] == myartist:
                    return int(mymoney/(wincondition - standings[mybidderid][myartist]))
                else:
                    return 0
            else:
                player_want_art = {}
                my_choose = {}
                artist_num = {}

                for i in artists:
                    player_want_art[i] = 0
                    my_choose[i] = 0
                    artist_num[i] = 0
                others = []

                for player in players:
                    if player != mybidderid:
                        others.append(player)
                # print(players)
                for player in others:
                    player_have = {}
                    for i in artists:
                        player_have[i] = 0
                    if player in winnerarray:
                        for artist in artists:
                            player_have[artist] = standings[player][artist]
                            if player_have[artist] != 0:
                                player_want_art[artist] += 1

                    else:
                        for artist in artists:
                            player_want_art[artist] += 1
                        # player_want_art[first_art] += 1

                for i in range(rd, auction_length):
                    art = itemsinauction[i]
                    # actually first 6 winning list
                    if artist_num[art] < wincondition:
                        artist_num[art] += 1
                    else:
                        ratio = 1 / (player_want_art[art] + 1)
                        my_choose[art] += ratio / pow(i - rd + 1, 5)
                final = sorted(my_choose, key=lambda x: my_choose[x])[-1]
                if final == itemsinauction[rd]:
                    # print('Decide to Bid on' + final)
                    return int(mymoney / wincondition)
                    # return
                else:
                    return 0

    def second_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 2: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order not known."""
        mymoney = standings[mybidderid]['money']

        # if player < 3, try to make a draw if someone is going to win
        if numberbidders <= 3:
            for player in players:
                if standings[player][itemsinauction[rd]] == 4 and player != mybidderid:
                    if itemsinauction[rd] == itemsinauction[winnerarray.index(player)]:
                        return standings[player]['money'] + 1

        if mybidderid in winnerarray:
            myartist = itemsinauction[winnerarray.index(mybidderid)]
            if itemsinauction[rd] == myartist:
                return int(mymoney/(wincondition -standings[mybidderid][myartist]))
            else:
                return 0
        else:
            player_want_art = {}
            my_choose = {}

            for i in artists:
                player_want_art[i] = 0
                my_choose[i] = 0
            others = []

            for player in players:
                if player != mybidderid:
                    others.append(player)

            for player in others:
                player_have = {}
                for i in artists:
                    player_have[i] = 0
                if player in winnerarray:
                    for artist in artists:
                        player_have[artist] = standings[player][artist]
                        if player_have[artist] != 0:
                            player_want_art[artist] += 1

                else:
                    for artist in artists:
                        player_want_art[artist] += 1

            # Find the artist with most count in total and least people want(already have)
            for artist in artists:
                my_choose[artist] = artists[artist] - player_want_art[artist]

            sort = sorted(my_choose, key=lambda x: my_choose[x])
            print(sort)
            # first_art = sort[-1]
            # second_art = sort[-2]
            last_art = sort[0]
            print(last_art)
            # If it is not the worst artist, try to bid on it if we have nothing before
            if last_art != itemsinauction[rd]:
                return 200
            else:
                return 0

    def third_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 3: Highest total value wins, highest bidder pays own bid, auction order known."""

        mymoney = standings[mybidderid]['money']
        auction_length = len(itemsinauction)
        
        # all value in auction
        all_value = 0
        for art in artists:
            all_value += artists[art] * values[art]

        # remaining value in auction
        remain_value = 0
        for i in range(rd,  auction_length):
            remain_value += values[itemsinauction[i]]
        # my value so far
        myvalue = 0
        for art in artists:
            myvalue += standings[mybidderid][art] * values[art]

        art = itemsinauction[rd]
        return int(mymoney*values[art]/(remain_value/numberbidders))

    def fourth_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 4: Highest total value wins, highest bidder pays second highest bid, auction order known."""
        mymoney = standings[mybidderid]['money']
        auction_length = len(itemsinauction)
        all_value = 0
        for art in artists:
            all_value += artists[art] * values[art]

        remain_value = 0
        for i in range(rd, auction_length):
            remain_value += values[itemsinauction[i]]

        myvalue = 0
        for art in artists:
            myvalue += standings[mybidderid][art] * values[art]

        art = itemsinauction[rd]

        if numberbidders == 2:
            target = all_value/numberbidders + 1
            remain_target = remain_value/numberbidders
        else:
            target = all_value/numberbidders*1.1
            remain_target = remain_value/numberbidders*1.1

        # be more restraint at first, focus on the target
        if remain_value > target - myvalue:
            bid = int(mymoney * values[art] / remain_target)
        # try to spend all money averagely
        else:
            bid = int(mymoney * values[art] / (remain_value/numberbidders))
        return bid
