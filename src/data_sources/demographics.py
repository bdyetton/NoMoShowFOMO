import requests
import json
import pandas as pd
import os
import numpy as np
import pycountry
import pickle
from src.data_sources import ticketmaster
my_file = os.path.dirname('__file__')

class Demographics:
    def __init__(self, city_to_city, country_to_country):
        #self.tzwhere = tzwhere.tzwhere()
        self.base_city = 'https://public.opendatasoft.com/api/records/1.0/search/?dataset=worldcitiespop&sort=population&'
        self.base_country = 'https://data.opendatasoft.com/api/records/1.0/search/?dataset=world-population%40kapsarc&sort=-year&'
        self.base_gdp = 'https://data.opendatasoft.com/api/records/1.0/search/?dataset=gdp-per-capita%40kapsarc&sort=time_period&'
        self.apikey = ''#&apikey=bde6f189132e01524b2a5afe139e9158a35637d9ac2b348f0376b056'
        self.req = requests.session()
        self.city_to_city_map = city_to_city
        self.country_to_country_map = country_to_country
        try:
            self.country_pop = pickle.load(open('country_pop.pkl','rb'))
        except FileNotFoundError:
            self.country_pop = {}
        try:
            self.country_gdp = pickle.load(open('country_gdp.pkl','rb'))
        except FileNotFoundError:
            self.country_gdp = {}

    def get_pop(self, city, country):
        if city is None or country is None:
            return pd.Series()
        if country in self.country_to_country_map:
            country = self.country_to_country_map[country]
        if city in self.city_to_city_map:
            city = self.city_to_city_map[city]

        pyco = pycountry.countries.search_fuzzy(country)[0]
        country_code = pyco.alpha_2.lower()
        ret = json.loads(self.req.get(self.base_city+'q='+city+self.apikey).content)
        pop_city = np.nan
        iso_country = np.nan
        iso_region = np.nan
        if 'records' not in ret:
            print('city', ret)
        for city_req in ret['records']:
            if city_req['fields']['country'] == country_code:
                if 'population' in city_req['fields']:
                    pop_city = city_req['fields']['population']
                iso_region = city_req['fields']['region']
                iso_country = city_req['fields']['country']
                break

        if country in self.country_pop:
            pop_count = self.country_pop[country]
        else:
            ret = json.loads(self.req.get(self.base_country + 'q=' + country+self.apikey).content)
            if 'records' not in ret:
                print('country', ret)
            pop_count = ret['records'][0]['fields']['value']
            self.country_pop[country] = pop_count
            pickle.dump(self.country_pop, open('country_pop.pkl','wb'))

        if country in self.country_gdp:
            gdp = self.country_gdp[country]
        else:
            ret = json.loads(self.req.get(self.base_gdp + 'q=' + country+self.apikey).content)
            if 'records' not in ret:
                print('gdp', ret)
            gdp = ret['records'][0]['fields']['gdp_per_capita']
            self.country_gdp[country] = gdp
            pickle.dump(self.country_gdp, open('country_gdp.pkl','wb'))

        return pd.Series({'population_city':pop_city, 'population_country':pop_count, 'gdp_country': gdp,'iso_region':iso_region, 'iso_country':iso_country})

if __name__=='__main__':
    tm = ticketmaster.TicketMaster()
    dg = Demographics(city_to_city=tm.city_to_city_map, country_to_country=tm.country_to_country_map)
    print(dg.get_pop('christchurch','new zealand'))