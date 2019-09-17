import requests
import json
import datetime
import pandas as pd
#from tzwhere import tzwhere
import pytz
import os
import numpy as np
import pickle
import pycountry
my_file = os.path.dirname('__file__')

class Demographics():
    def __init__(self):
        #self.tzwhere = tzwhere.tzwhere()
        self.base = 'https://public.opendatasoft.com/api/records/1.0/search/?dataset=worldcitiespop&'
        self.default_params = '&sort=population'
        self.req = requests.session()

    def get_pop(self, city, country):
        pyco = pycountry.countries.search_fuzzy(country)[0]
        country_code = pyco.alpha_2.lower()
        ret = json.loads(self.req.get(self.base+'q='+city+self.default_params).content)
        pop = np.nan
        iso_country = np.nan
        iso_region = np.nan
        for city_req in ret['records']:
            if city_req['fields']['country'] == country_code:
                if 'population' in city_req['fields']:
                    pop = city_req['fields']['population']
                iso_region = city_req['fields']['region']
                iso_country = city_req['fields']['country']
                break
        return pop, iso_region, iso_country

if __name__=='__main__':
    dg = Demographics()
    print(dg.get_pop('christchurch','new zealand'))