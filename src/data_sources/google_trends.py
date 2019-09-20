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

class Trends():
    def __init__(self):
        self.api = None
        self.proxylist = [
            'http://191.96.42.86:3129',
            'http://72.35.40.34:8080'
        ]
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
            }
        }
        self.login()

    def login(self):
        self.api = TrendReq(hl='en-US', tz=360,
                            proxies=[
                                self.proxylist.pop()
                            ],
                            retries=5,
                            backoff_factor=0.5)


    def get_iso_region(self, lat, long):
        ret = json.loads(self.req.get('http://api.geonames.org/countrySubdivisionJSON?lat='
                            +str(lat)+'&lng='+str(long)+'&maxRows=10&username=bdyetton').content)
        codes = [code for code in ret['codes'] if code['type']=='ISO3166-2']
        region_code = sorted(codes, key=lambda x: x['level'])[0]['code']
        if ret['countryCode'] in self.region_map:
            region_code = self.region_map[ret['countryCode']][region_code]
        region = ret['countryCode'] + '-' + region_code
        return region

    def get_geo_trends(self, kw, timeframe='all', region_iso=None, normalize_in_world=True, youtube=False):
        if isinstance(timeframe, tuple):
            timeframe = timeframe[0].strftime('%Y-%m-%dT%H') + timeframe[1].strftime('%Y-%m-%dT%H')
        for i in range(5):
            try:
                if normalize_in_world:
                    country_iso = region_iso.split('-')[0]
                    self.api.build_payload([kw],
                                           timeframe=timeframe,
                                           gprop='youtube' if youtube else None)
                    interest_by_country_df = self.api.interest_by_region(inc_geo_code=True).set_index('geoCode')
                    interest_by_country = interest_by_country_df.loc[country_iso,kw]

                self.api.build_payload([kw],
                                       timeframe=timeframe,
                                       geo=country_iso,
                                       gprop='youtube' if youtube else None)
                interest_by_region_df = self.api.interest_by_region(resolution='REGION', inc_geo_code=True).set_index('geoCode')
                break
            except ResponseError as e:
                print(e)
                print('Response Error - trying to log in again')
                self.login()

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