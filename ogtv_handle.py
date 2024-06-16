from collections import OrderedDict

import requests, json
from flask import Response
from support import d, default_headers, logger
from tool import ToolUtil

from .setup import P


class Tvchak:

    headers = {
        'Host': 'azure2986.fastedge.net',
        'accept': '*/*',
        'Referer': 'https://sdr4w5g.allyearcdn.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        'Origin': 'https://sdr4w5g.allyearcdn.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    spotv_headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'referer': 'https://tvchak.com/',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

    _stream_url = 'https://azure2986.fastedge.net'

    _channels = None
    _spotv_channels = None

    @classmethod
    def ch_list(cls):
        if cls._channels == None:
            cls._channels = OrderedDict()
            cate = OrderedDict()
            param = {'content':'', 'category':''}
            for i in range(5):
                param['scrollnum'] = i
                data = requests.post('https://tvchak.com/api/live/mainchannel.php', headers=default_headers, data=param).json()
                if data.get('dataAll') == None:
                    break
                for ch in data['dataAll']:
                    entity = {
                        'name': ch['name'],
                        'logo': ch['logoImgUrl'],
                        'current': ch['liveTitle'],
                        'id': ch['code'],
                        'category': ch['category'],
                        'url': '',
                    }
                    if cate.get(ch['category']) == None:
                        cate[ch['category']] = []
                    cate[ch['category']].append(entity)
            tmp = []
            for order in ['지상파', '뉴스', '종합편성', '드라마/예능', '영화', '정주행', '스포츠']:
                tmp += cate[order]
            for ch in tmp:
                cls._channels[ch['id']] = ch
        
        cls._spotv_channels = OrderedDict()
        data = requests.post('https://tvchak.com/api/sports/live/mainchannel.php', headers=default_headers, data={'category':0}).json()
        for ch in data['dataAll']:
            if ch['showing'] == 1:
                title = f"[{ch['leagueName']}] {ch['awayName']} vs {ch['homeName']}"
                cls._spotv_channels[ch['liveCode']] = {
                    'name': title,
                    'logo': '',
                    'current': title,
                    'id': ch['liveCode'],
                    'category': 'SPOTV',
                }
        return list(cls._channels.values()) + list(cls._spotv_channels.values())
        
    

    @classmethod
    def get_m3u8(cls, ch_id):
        if cls._channels == None:
            cls.ch_list()

        ch = cls._channels.get(ch_id)
        if ch != None:
            if cls._channels[ch_id]['url'] == '':
                url = f"{cls._stream_url}/live/{ch_id}/chunklist.m3u8"
                res = requests.get(url, headers=cls.headers)
                if res.status_code != 200:
                    url = f"{cls._stream_url}/live2/{ch_id}/chunklist.m3u8"
                    res = requests.get(url, headers=cls.headers)
                    if res.status_code == 200:
                        cls._channels[ch_id]['url'] = 'live2'
                else:
                    cls._channels[ch_id]['url'] = 'live'
            else:
                url = f"{cls._stream_url}/{cls._channels[ch_id]['url']}/{ch_id}/chunklist.m3u8"
                res = requests.get(url, headers=cls.headers)
            new_data = []
            for line in res.text.splitlines():
                line = line.strip()
                if line.endswith('.ts'):
                    new = ToolUtil.make_apikey_url(f"/{P.package_name}/api/segment.ts?ch_id={ch_id}&ts={line}&live={cls._channels[ch_id]['url']}")
                    new_data.append(new)
                else:
                    new_data.append(line)
            data = '\n'.join(new_data)
            return 'text', data

        elif cls._spotv_channels.get(ch_id) != None:
            url = f'https://sdr4w5g.allyearcdn.com/player/live/?g={ch_id}&q=0&sports=false'
            text = requests.get(url, headers=cls.spotv_headers).text
            idx = text.index('var tokenJson = ')
            start = text.index('{', idx)
            end = text.index('}', start+1)
            tmp = text[start:end+1]
            data = json.loads(tmp)
            return 'redirect', data['authid']



    @classmethod
    def segment(cls, req):
        url = f"{cls._stream_url}/{req.args.get('live')}/{req.args.get('ch_id')}/{req.args.get('ts')}"
        res = requests.get(url, headers=cls.headers, stream=True, verify=False)
        ret = Response(res.iter_content(chunk_size=1048576), res.status_code, content_type='video/MP2T', direct_passthrough=True)
        return ret


    @classmethod
    def make_m3u(cls):
        M3U_FORMAT = '#EXTINF:-1 tvg-id=\"{id}\" tvg-name=\"{title}\" tvg-logo=\"{logo}\" group-title=\"{group}\" tvg-chno=\"{ch_no}\" tvh-chnum=\"{ch_no}\",{title}\n{url}\n' 
        m3u = '#EXTM3U\n'
        for idx, item in enumerate(cls.ch_list()):
            m3u += M3U_FORMAT.format(
                id=item['id'],
                title=item['name'],
                group=item['category'],
                ch_no=str(idx+1),
                url=ToolUtil.make_apikey_url(f"/{P.package_name}/api/url.m3u8?ch_id={item['id']}"),
                logo= item['logo'],
            )
        return m3u
