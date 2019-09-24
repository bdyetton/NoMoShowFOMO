import json
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import time
import seaborn as sns
sns.set(font_scale=1.5)
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError
import requests
import queue
import pickle
from collections import deque
import numpy as np


#region_iso was not found: NO-50
# available regions are was not found: Index(['NO-02', 'NO-09', 'NO-06', 'NO-20', 'NO-04', 'NO-12', 'NO-15', 'NO-17',
#        'NO-18', 'NO-05', 'NO-03', 'NO-01', 'NO-11', 'NO-14', 'NO-16', 'NO-08',
#        'NO-19', 'NO-10', 'NO-07'],


class ProxyGrenerator():
    def __init__(self, q_out: queue.Queue):
        self.q_out = q_out
        self.req = requests.session()
        self.didsoft_list = deque()
        try:
            self.proxylist = pickle.load(open('proxylist.pkl','rb'))
        except FileNotFoundError:
            self.proxylist = set()

    def get_didsoft_proxy(self):
        if len(self.didsoft_list) == 0:
            url = 'http://list.didsoft.com/get?email=yettonbd@gmail.com&pass=334hwf&pid=httppremium&https=yes&showcountry=no&country=US|GB|CA|FR|DE'
            try:
                resp = self.req.get(url)
            except requests.exceptions.ConnectionError:
                return
            ret = resp.content.decode('utf8').split('\n')
            ret = ['https://'+prox for prox in ret]
            self.didsoft_list.extend(ret)
            print('NEW DIDSOFT')

        while not self.q_out.full():
            self.q_out.put(self.didsoft_list.popleft())

    def get_pubprox(self):
        try:
            resp = self.req.get('http://pubproxy.com/api/proxy?' +
                                'https=true' +
                                '&api=T24xN09EVDB3NVJKSzZiSStGMDFCQT09&limit=5')
        except requests.exceptions.ConnectionError:
            return
        try:
            ret = json.loads(resp.content)
        except json.decoder.JSONDecodeError:
            print(resp.content)
            return None
        # print('Got new proxy, support is',ret['data'][0]['support'])
        https = ['','s']
        newproxylist = [prox['type']+https[prox['support']['https']]+'://' + prox['ipPort'] for prox in ret['data']]
        newproxylist = [prox for prox in newproxylist if prox not in self.proxylist]
        self.proxylist.update(newproxylist)
        print('Got', len(newproxylist),'new proxies')
        if self.q_out is None:
            return newproxylist
        else:
            for prox in newproxylist:
                self.q_out.put(prox)

    def check_for_new_proxies(self, service='didsoft'):
        if self.q_out is not None and self.q_out.full():
            return
        if service == 'didsoft':
            self.get_didsoft_proxy()
        else:
            self.get_pubprox()

    def save_proxylist(self):
        pickle.dump(self.proxylist, open('proxylist.pkl','wb'))

class Trends():
    def __init__(self, q_in=None, use_proxy=True):
        self.api = None
        self.use_proxies = use_proxy
        self.q_in = q_in
        self.req = requests.session()
        self.region_map = {
            'CZ':{
                '10':'PR',
                '31':'JC',
                '64':'JM',
                '41':'KA',
                '52':'KR',
                '51':'LI',
                '71':'OL',
                '53':'PA',
                '32':'PL',
                '20':'ST',
                '42':'US',
                '63':'VY',
                '72':'ZL'
            },
            'LU':{
                'ES':'L',
                'CA':'L',
                'CL':'D',
                'DI':'D',
                'EC':'G',
                'GR':'G',
                'LU':'L',
                'ME':'L',
                'RD':'D',
                'RM':'G',
                'VD':'D',
                'WI':'D',
            },
            'PL':{
                '02':'DS',
                '04':'KP',
                '08':'LB',
                '10':'LD',
                '06':'LU',
                '12':'MA',
                '14':'MZ',
                '16':'OP',
                '20':'PD',
                '18':'PK',
                '22':'PM',
                '26':'SK',
                '24':'SL',
                '28':'WN',
                '30':'WP',
                '32':'ZP',
            },
            # 'NO':{'23':'16',
            #       '50':'16'}
        },
        self.login()

    def login(self):
        for t in range(30):
            try:
                if hasattr(self, 'api'):
                    del self.api
                proxies = [self.q_in.get()] if self.use_proxies else []
                self.api = TrendReq(hl='en-US', tz=360,
                                    proxies=proxies,
                                    timeout=(3,6),
                                    retries=5, backoff_factor=1)
                time.sleep(1)
                print('Successful login @ login')
                return
            except (ValueError, requests.exceptions.ConnectionError):
                pass
        print('Failed login @ login!')


    def get_iso_region(self, lat, long):
        for i in range(5):
            try:
                ret = json.loads(self.req.get('http://api.geonames.org/countrySubdivisionJSON?lat='
                                    +str(lat)+'&lng='+str(long)+'&maxRows=10&username=bdyetton').content)
                break
            except requests.exceptions.ConnectionError as e:
                print(e)
                continue
        else:
            raise ValueError('Remote disconnect x5 for geonames')
        if 'codes' not in ret:
            print(ret)
            raise ValueError('Lat='+str(lat)+', Long='+str(long)+'is not in a country')
        codes = [code for code in ret['codes'] if code['type']=='ISO3166-2']
        region_code = sorted(codes, key=lambda x: x['level'])[0]['code']
        if ret['countryCode'] in self.region_map:
            if region_code not in self.region_map[ret['countryCode']].values():
                region_code = self.region_map[ret['countryCode']][region_code]
        region = ret['countryCode'] + '-' + region_code
        return region

    def get_geo_trends(self, kw, timeframe='all', region_iso=None, normalize_in_world=True, youtube=False):
        if isinstance(timeframe, tuple):
            timeframe = timeframe[0].strftime('%Y-%m-%dT%H') + timeframe[1].strftime('%Y-%m-%dT%H')
        problem = False
        for i in range(20):
            try:
                if normalize_in_world:
                    country_iso = region_iso.split('-')[0]
                    self.api.build_payload([kw],
                                           timeframe=timeframe,
                                           gprop='youtube' if youtube else None)
                    interest_by_country_df = self.api.interest_by_region(inc_geo_code=True).set_index('geoCode')
                    interest_by_country = interest_by_country_df.loc[country_iso,kw]
                time.sleep(0.55)
                self.api.build_payload([kw],
                                       timeframe=timeframe,
                                       geo=country_iso,
                                       gprop='youtube' if youtube else None)
                interest_by_region_df = self.api.interest_by_region(resolution='REGION', inc_geo_code=True).set_index('geoCode')
                time.sleep(0.55)
                if problem:
                    problem = False
                print('--------------------------------------------Query successful :)')
                break
            except (ResponseError,
                    requests.exceptions.ConnectTimeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout,
                    AttributeError) as e:
                problem = True
                print(e)
                print('Response Error - trying to log in again')
                self.login()
            except IndexError as e:
                print('Proxy list Index- trying to log in again')
                print(e)
                problem = True
                self.login()

        if problem:
            print('Login unsuccessful!!!! No data was pulled.')
            return pd.Series()

        if normalize_in_world:
            interest_by_region_df[kw] = interest_by_region_df[kw]*interest_by_country/100
        if region_iso in interest_by_region_df.index:
            interest_by_region = interest_by_region_df.loc[region_iso, kw]
        else:
            print('region_iso was not found:',region_iso)
            print('available regions are was not found:',interest_by_region_df.index)
            return pd.Series()

        return pd.Series({'popularity_in_country':interest_by_country, 'popularity_in_region':interest_by_region})


if __name__=='__main__':
    tr = Trends()
    a = tr.get_geo_trends("dixon",'today 5-y',tr.get_iso_region(51.5074,0.1278))
    a = tr.get_geo_trends("dixon",'today 5-y',tr.get_iso_region(51.5074,0.1278))
    a = tr.get_geo_trends("dixon",'today 5-y',tr.get_iso_region(51.5074,0.1278))
    print(a)