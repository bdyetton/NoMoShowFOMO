import json
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import pycountry
import seaborn as sns
sns.set(font_scale=1.5)
from pytrends.request import TrendReq
import geocoder
import requests

class Trends():
    def __init__(self):
        self.api = TrendReq(hl='en-US', tz=360)
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
            }
        }

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

        if normalize_in_world:
            country_iso = region_iso.split('-')[0]
            self.api.build_payload([kw],
                                   timeframe=timeframe,
                                   geo='',
                                   gprop='youtube' if youtube else None)
            interest_by_country_df = self.api.interest_by_region(inc_geo_code=True).set_index('geoCode')
            interest_by_country = interest_by_country_df.loc[country_iso,kw]

        self.api.build_payload([kw],
                               timeframe=timeframe,
                               geo=country_iso,
                               gprop='youtube' if youtube else None)
        interest_by_region_df = self.api.interest_by_region(resolution='REGION', inc_geo_code=True).set_index('geoCode')

        if normalize_in_world:
            interest_by_region_df[kw] = interest_by_region_df[kw]*interest_by_country/100
        interest_by_region = interest_by_region_df.loc[region_iso, kw]

        return interest_by_country, interest_by_region


if __name__=='__main__':
    tr = Trends()
    a = tr.get_geo_trends("dixon",'today 5-y',tr.get_iso_region(51.5074,0.1278))
    print(a)