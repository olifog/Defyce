import asyncio
import copy
import json
import time
import traceback
from datetime import datetime, timedelta
from operator import itemgetter

import aiohttp
import motor.motor_asyncio
from pytz import timezone

from extras.hypixel import HypixelAPI
from extras.requesthandler import RequestHandler


class Updater:
    def __init__(self):
        with open('./data/settings.json') as settings:
            self.settings = json.load(settings)
            settings.close()

        uri = f"mongodb://updater:{self.settings['updater_motor_password']}@51.81.32.153:27017/admin"
        self.motor_client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.motor_client.defyce
        self.iterations = 0
        self.handler = RequestHandler(asyncio.get_event_loop())
        self.hypixelapi = HypixelAPI(self.settings['updater_api_key'], self.handler)
        self.last_task_time = time.time()
        self.est = timezone("US/Eastern")

    async def update_guild(self, name):
        guild = await self.hypixelapi.getGuild(name=name)
        guilddata = await self.db[name].find_one({})

        update = {'exp': guild.JSON['exp']}

        top = {'week': [], 'average': []}
        total = {'week': 0, 'average': 0, 'all': guild.JSON['exp']}
        days = []
        for x in range(7):
            d = (datetime.now(tz=self.est) - timedelta(days=x)).strftime("%Y-%m-%d")
            days.append(d)
            top[d] = []
            total[d] = 0

        memberlist = []

        update['members'] = []
        for member in guild.JSON['members']:
            memberlist.append(member['uuid'])
            verified = await self.db.verified.find_one({'uuid': member['uuid']})

            newExpHistory = member['expHistory']
            newExpHistory['week'] = sum(newExpHistory.values())
            newExpHistory['average'] = newExpHistory['week'] / 7
            p = {'xp': 0}

            if verified is not None:
                p['player'] = verified['displayname']
                p['discord'] = verified['discordid']
                await self.db.verified.update_one({'_id': verified['_id']}, {'$set': {'guildExp': newExpHistory, 'guild': name, 'guildrank': member['rank']}})
            else:
                get_from_api = True
                try:
                    for old_mem in guilddata['members']:
                        if old_mem['uuid'] == member['uuid']:
                            try:
                                p['player'] = old_mem['name']
                                get_from_api = False
                            except KeyError:
                                pass
                            break
                except (KeyError, TypeError):
                    pass

                if get_from_api:
                    url = 'https://playerdb.co/api/player/minecraft/' + member['uuid']
                    resp = await self.handler.getJSON(url)
                    p['player'] = resp['data']['player']['username']

            for timeframe, xp in newExpHistory.items():
                p['xp'] = xp
                try:
                    top[timeframe].append(copy.copy(p))
                    total[timeframe] += xp
                except KeyError:
                    pass

            mem = {'name': p['player'],
                   'uuid': member['uuid'],
                   'rank': member['rank'],
                   'exphistory': newExpHistory,
                   'joined': datetime.fromtimestamp(member['joined'] / 1000, tz=self.est)}

            update['members'].append(mem)

        for timeframe in top:
            top[timeframe] = sorted(top[timeframe], key=itemgetter('xp'), reverse=True)[:10]

        update['top'] = top
        update['total'] = total

        async for player in self.db.verified.find({'guild': name}):
            if player['uuid'] not in memberlist:
                await self.db.verified.update_one({'_id': player['_id']}, {"$set": {'remove': True}})

        await self.db[name].update_one({'_id': guilddata['_id']}, {'$set': update})

    async def updater(self):
        await asyncio.sleep(90)
        asyncio.create_task(self.updater())

        self.iterations += 1

        if self.iterations % 2 == 0:
            await self.update_guild('pace')
        else:
            await self.update_guild('defy')

    async def close(self):
        print('\nClosing request handler...')
        await self.handler.close()

        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]
        print('Cancelling tasks')

        [task.cancel() for task in tasks]
        try:
            await asyncio.shield(asyncio.gather(*tasks))
        except asyncio.futures.CancelledError:
            pass

        print('Tasks all cancelled')



updater = Updater()

loop = asyncio.get_event_loop()

loop.create_task(updater.updater())
try:
    print('Starting updater...')
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(updater.close())

print('Closing loop...')
loop.close()
print('Shut down')