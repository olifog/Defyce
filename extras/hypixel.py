from extras import leveling


HYPIXEL_API_URL = 'https://api.hypixel.net/'
UUIDResolverAPI = "https://sessionserver.mojang.com/session/minecraft/profile/"


class HypixelAPIError(Exception):
    pass

class PlayerNotFoundException(Exception):
    """ Simple exception if a player/UUID is not found. This exception can usually be ignored.
        You can catch this exception with ``except hypixel.PlayerNotFoundException:`` """
    pass

class GuildNotFoundException(Exception):
    pass


class HypixelAPI(object):
    def __init__(self, key, handler):
        self.api_key = key
        self.handler = handler

    async def getJSON(self, typeOfRequest, **kwargs):
        """ This private function is used for getting JSON from Hypixel's Public API. """
        requestEnd = ''

        for name, value in kwargs.items():
            requestEnd += '&{}={}'.format(name, value)

        url = HYPIXEL_API_URL + '{}?key={}{}'.format(typeOfRequest, self.api_key, requestEnd)

        response = await self.handler.getJSON(url)

        if response['success'] is False:
            raise HypixelAPIError(response)

        if typeOfRequest == 'player':
            if response['player'] is None:
                raise PlayerNotFoundException()

        if typeOfRequest == 'guild':
            if response['guild'] is None:
                raise GuildNotFoundException()

        try:
            return response[typeOfRequest]
        except KeyError:
            return response

    async def getPlayer(self, **kwargs):
        resp = await self.getJSON('player', **kwargs)
        return Player(resp)

    async def getGuild(self, **kwargs):
        resp = await self.getJSON('guild', **kwargs)
        return Guild(resp)


class Player(object):
    def __init__(self, JSON):
        self.JSON = JSON
        self.UUID = JSON["uuid"]

    def getName(self):
        return self.JSON['displayname']

    def getLevel(self):
        try:
            networkExp = self.JSON['networkExp']
        except KeyError:
            networkExp = 0

        try:
            networkLevel = self.JSON['networkLevel']
        except KeyError:
            networkLevel = 0

        exp = leveling.getExperience(networkExp, networkLevel)
        myoutput = leveling.getExactLevel(exp)
        return myoutput

    def getRank(self):
        playerRank = None
        possibleRankLocations = ['packageRank', 'newPackageRank', 'monthlyPackageRank', 'rank']

        rankdata = []

        transform = {
            'NORMAL': None,
            'VIP': 'VIP',
            'VIP_PLUS': 'VIP+',
            'MVP': 'MVP',
            'MVP_PLUS': 'MVP+',
            'SUPERSTAR': 'MVP++',
            'HELPER': 'Hypixel Helper',
            'YOUTUBER': 'Youtuber',
            'MODERATOR': 'Hypixel Moderator',
            'ADMIN': 'Hypixel Admin'
        }

        for location in possibleRankLocations:
            rank = str(self.JSON.get(location)).upper()

            if rank is None or rank is 'NONE':
                continue

            rankdata.append(rank)

        for apirank, formatrank in transform.items():
            if apirank in rankdata:
                playerRank = formatrank

        return playerRank


class Guild:
    def __init__(self, JSON):
        self.JSON = JSON

    def getLevel(self):
        exp = self.JSON['exp']
        levels = [100000, 150000, 250000, 500000, 750000, 1000000, 1250000, 1500000, 2000000, 2500000, 2500000, 2500000,
                  2500000, 2500000]

        l = 0
        for level in levels:
            if exp < level:
                l += exp / level
                break

            l += 1
            exp -= level

        if exp > 0:
            l += exp / 3000000

        return l
