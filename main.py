from flask import Flask, Response, render_template
from flask_caching import Cache
import uuid
import random
import collections
import json
import os
import copy

app = Flask(__name__)

# Cacheインスタンスの作成
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
    'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 2,
})


@app.route('/')
def homepage():
    return render_template('index.html')


# create the game group
@app.route('/create/<nickname>')
def create_game(nickname):
    game = {
        'status': 'waiting',
        'routeidx': 0,
        'stocks': list(range(2, 99)),
        'players': []}
    player = {}

    gameid = str(uuid.uuid4())
    game['gameid'] = gameid
    player['playerid'] = gameid
    player['nickname'] = nickname
    player['holdcards'] = []
    game['players'].append(player)

    app.logger.debug(gameid)
    app.logger.debug(game)
    cache.set(gameid, game)
    return gameid


# re:wait the game
@app.route('/<gameid>/waiting')
def waiting_game(gameid):
    game = cache.get(gameid)
    game['status'] = 'waiting'
    cache.set(gameid, game)
    return 'reset game status'


# join the game
@app.route('/<gameid>/join')
@app.route('/<gameid>/join/<nickname>')
def join_game(gameid, nickname='default'):
    game = cache.get(gameid)
    if game['status'] == 'waiting':
        player = {}

        playerid = str(uuid.uuid4())
        player['playerid'] = playerid
        if nickname == 'default':
            player['nickname'] = playerid
        else:
            player['nickname'] = nickname
        player['holdcards'] = []
        game['players'].append(player)

        cache.set(gameid, game)
        return playerid + ' ,' + player['nickname'] + ' ,' + game['status']
    else:
        return 'Already started'


# processing the game
@app.route('/<gameid>/start')
def start_game(gameid):
    game = cache.get(gameid)
    app.logger.debug(gameid)
    app.logger.debug(game)
    game['status'] = 'started'

    # playerids = [player['playerid'] for player in game['players']]
    routelist = copy.copy(game['players'])
    random.shuffle(routelist)
    game['routelist'] = routelist

    players = game['players']

    for player in players:
        player['holdcards'] = []
        while len(player['holdcards']) < 6:
            player['holdcards'].append(game['stocks'].pop(random.randint(0, len(game['stocks']) - 1)))

    game['hightolow'] = []
    game['lowtohigh'] = []
    game['hightolow'].append([100])
    game['hightolow'].append([100])
    game['lowtohigh'].append([1])
    game['lowtohigh'].append([1])

    cache.set(gameid, game)
    return json.dumps(game['routelist'])


# next to player the game
@app.route('/<gameid>/next')
def processing_game(gameid):
    game = cache.get(gameid)

    game['routeidx'] = (game['routeidx'] + 1) % len(game['players'])

    players = game['players']

    # refresh holdcards for all members
    for player in players:
        while len(player['holdcards']) < 6:
            if len(game['stocks']) > 0:
                player['holdcards'].append(game['stocks'].pop(random.randint(0, len(game['stocks']) - 1)))
            else:
                break

    cache.set(gameid, game)
    return 'go on to the next user'


# set the card on the line
@app.route('/<gameid>/<clientid>/set/<int:lineid>/<int:cardnum>')
def setcard_game(gameid, clientid, lineid, cardnum):
    game = cache.get(gameid)
    player = [player for player in game['players'] if player['playerid'] == clientid][0]

    if lineid in [0, 1]:
        highToLow = game['hightolow'][lineid]
        # 100 -> 2
        if highToLow[-1] > cardnum:
            highToLow.append(cardnum)
        else:
            if (highToLow[-1] + 10) == cardnum:
                highToLow.append(cardnum)
            else:
                return 'Error2'
    elif lineid in [2, 3]:
        lowToHigh = game['lowtohigh'][lineid%2]
        # 1 -> 99
        if lowToHigh[-1] < cardnum:
            lowToHigh.append(cardnum)
        else:
            if (lowToHigh[-1] - 10) == cardnum:
                lowToHigh.append(cardnum)
            else:
                return 'Error3'
    else:
        return 'Error'

    player['holdcards'].remove(cardnum)

    cache.set(gameid, game)
    return 'ok'


# all status the game
@app.route('/<gameid>/status')
def game_status(gameid):
    game = cache.get(gameid)

    return json.dumps(game)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
