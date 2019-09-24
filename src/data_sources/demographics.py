import requests
import json
import pandas as pd
import os
import numpy as np
import pycountry
from src.data_sources import ticketmaster
my_file = os.path.dirname('__file__')

class Demographics:
    def __init__(self, city_to_city, country_to_country):
        #self.tzwhere = tzwhere.tzwhere()
        self.base_city = 'https://public.opendatasoft.com/api/records/1.0/search/?dataset=worldcitiespop&sort=population&'
        self.base_country = 'https://data.opendatasoft.com/api/records/1.0/search/?dataset=world-population%40kapsarc&sort=-year&'
        self.req = requests.session()
        self.city_to_city_map = city_to_city
        self.country_to_country_map = country_to_country

    def get_pop(self, city, country):
        if city is None or country is None:
            return pd.Series()
        if country in self.country_to_country_map:
            country = self.country_to_country_map[country]
        if city in self.city_to_city_map:
            city = self.city_to_city_map[city]

        pyco = pycountry.countries.search_fuzzy(country)[0]
        country_code = pyco.alpha_2.lower()
        ret = json.loads(self.req.get(self.base_city+'q='+city).content)
        pop_city = np.nan
        iso_country = np.nan
        iso_region = np.nan
        for city_req in ret['records']:
            if city_req['fields']['country'] == country_code:
                if 'population' in city_req['fields']:
                    pop_city = city_req['fields']['population']
                iso_region = city_req['fields']['region']
                iso_country = city_req['fields']['country']
                break

        ret = json.loads(self.req.get(self.base_country + 'q=' + country).content)
        pop_count = ret['records'][0]['fields']['value']
        return pd.Series({'population_city':pop_city, 'population_country':pop_count, 'iso_region':iso_region, 'iso_country':iso_country})

if __name__=='__main__':
    tm = ticketmaster.TicketMaster()
    dg = Demographics(city_to_city=tm.city_to_city_map, country_to_country=tm.country_to_country_map)
    print(dg.get_pop('christchurch','new zealand'))