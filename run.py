from flask import Flask, Response, render_template
from flask_caching import Cache
import uuid
import random
import collections
import json
import os

app = Flask(__name__)

# Cacheインスタンスの作成
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
    'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 24,
})

class Game:
    status = 'waiting' # waiting, started, end
    gameid = ''
    members = {}
    routelist = []
    routeidx = 0
    cards = []
    hightolow = []
    lowtohigh = []
    stocks = list(range(2, 99))


class Member:
    nickname = ''
    holdcards = []


@app.route('/')
def homepage():
    return render_template('index.html')


# create the game group
@app.route('/create')
def create_game():
    game = Game()
    member = Member()

    gameid = str(uuid.uuid4())
    game.gameid = gameid
    member.nickname = gameid
    game.members[gameid] = member

    cache.set(gameid, game)
    return gameid


# re:wait the game
@app.route('/<gameid>/waiting')
def waiting_game(gameid):
    game = cache.get(gameid)
    game.status = 'waiting'
    cache.set(gameid, game)
    return 'reset game status'


# join the game
@app.route('/<gameid>/join')
@app.route('/<gameid>/join/<nickname>')
def join_game(gameid, nickname='default'):
    if cache.get(gameid).status == 'waiting':
        game = cache.get(gameid)
        member = Member()

        clientid = str(uuid.uuid4())
        if nickname == 'default':
            member.nickname = clientid
        else:
            member.nickname = nickname
        game.holdcards = []
        game.members[clientid] = member

        cache.set(gameid, game)
        return clientid + ' ,' + member.nickname + ' ,' + game.status
    else:
        return 'Already started'


# processing the game
@app.route('/<gameid>/start')
def start_game(gameid):
    game = cache.get(gameid)
    game.status = 'started'

    members = [mid for mid in game.members.keys()]
    random.shuffle(members)
    game.routelist = members

    for mid in members:
        member = game.members[mid]
        member.holdcards = []
        while len(member.holdcards) < 6:
            member.holdcards.append(game.stocks.pop(random.randint(0, len(game.stocks) - 1)))

    game.hightolow = []
    game.lowtohigh = []
    game.hightolow.append([100])
    game.hightolow.append([100])
    game.lowtohigh.append([1])
    game.lowtohigh.append([1])

    cache.set(gameid, game)
    return json.dumps(game.routelist)


# status the game
@app.route('/<gameid>/status')
def game_status(gameid):
    game = cache.get(gameid)
    return game.status


# next to player the game
@app.route('/<gameid>/next')
def processing_game(gameid):
    game = cache.get(gameid)
    members = [mid for mid in game.members.keys()]

    game.routeidx = (game.routeidx + 1) % len(game.members)

    # refresh holdcards for all members
    for mid in members:
        member = game.members[mid]
        while len(member.holdcards) < 6:
            if len(game.stocks) > 0:
                member.holdcards.append(game.stocks.pop(random.randint(0, len(game.stocks) - 1)))

    cache.set(gameid, game)
    return 'go on to the next user'


# set the card on the line
@app.route('/<gameid>/<clientid>/set/<int:lineid>/<int:cardnum>')
def setcard_game(gameid, clientid, lineid, cardnum):
    game = cache.get(gameid)

    if lineid in [0, 1]:
        # 100 -> 2
        if game.hightolow[lineid][-1] > cardnum:
            game.hightolow[lineid].append(cardnum)
        else:
            if (game.hightolow[lineid][-1] + 10) == cardnum:
                game.hightolow[lineid].append(cardnum)
            else:
                return 'Error2'
    elif lineid in [2, 3]:
        # 1 -> 99
        if game.lowtohigh[lineid%2][-1] < cardnum:
            game.lowtohigh[lineid%2].append(cardnum)
        else:
            if (game.lowtohigh[lineid%2][-1] - 10) == cardnum:
                game.lowtohigh[lineid%2].append(cardnum)
            else:
                return 'Error3'
    else:
        return 'Error'

    game.members[clientid].holdcards.remove(cardnum)

    cache.set(gameid, game)
    return 'ok'


# user status the game
@app.route('/<gameid>/<clientid>/status')
def member_status(gameid, clientid):
    game = cache.get(gameid)
    yourturn = False

    if game.routelist[game.routeidx] == clientid:
        yourturn = True

    holdcards = game.members[clientid].holdcards

    response = {'turn': yourturn, 'holdcards': holdcards}

    return json.dumps(response)


# card positiions the game
@app.route('/<gameid>/cardlists')
def cardlists_game(gameid):
    game = cache.get(gameid)

    response = []
    for i in range(4):
        if i in [0,1]:
            response.append(game.hightolow[i])
        else:
            response.append(game.lowtohigh[i%2])

    return json.dumps(response)


# set user information the game
@app.route('/<gameid>/<clientid>/profile/set/<nickname>')
def edit_profile(gameid, clientid, nickname):
    game = cache.get(gameid)

    if clientid in game.members:
        member = game.members[clientid]
        member.nickname = nickname

        cache.set(gameid, game)
        return 'changed user name'
    else:
        return 'NG'


if __name__ == "__main__":
    app.run(debug=True)
#    app.run(debug=True, port=5000, threaded=True)
