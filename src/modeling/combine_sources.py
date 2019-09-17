import pandas as pd
import os
my_file = os.path.dirname('__file__')
import src.data_sources.songkick as songkick
import src.data_sources.google_trends as google_trends
import src.data_sources.demographics as demographics
import src.data_sources.ticketmaster as ticketmaster
import numpy as np
debug = True


def add_songkick(df):
    sk = songkick.SongKick()
    sk_cont = []
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('SK is', 100 * idx / df.shape[0], 'percent complete')
        try:
            venue_series = sk.get_venue_capacity(row['venue'], row['lat'], row['long'])
            venue_series['sk_popularity'] = sk.get_songkick_popularity(row['performers'], row['event_date'], row['lat'], row['long'])
            last_local_events = sk.get_last_local_events(row['performers'], row['event_date'], row['lat'], row['long'])
            if last_local_events.shape[0] > 0:
                venue_series['last_time_played'] = last_local_events.iloc[0]['event_start']
                venue_series['days_since_last_played'] = (row['event_date'].date() - last_local_events.iloc[0]['event_start'].date()).days
            else:
                venue_series['last_time_played'] = np.nan
                venue_series['time_since_last_played'] = np.nan
            venue_series['total_times_played_locally'] = last_local_events.shape[0]
        except BaseException as e:
            if debug:
                print(e)
                continue
            else:
                raise
        venue_series['idx'] = idx
        sk_cont.append(venue_series)
    sk_df = pd.concat(sk_cont, axis=1, sort=True).T
    sk_df = sk_df.set_index('idx')
    df = pd.merge(df, sk_df, right_index=True, left_index=True)
    return df


days_of_week = ['Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun']


def add_ticket_levels(df):
    tm = ticketmaster.TicketMaster()
    tm_cont = []
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('TM is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = tm.add_availability_info(row)
            row_out['idx'] = idx
            tm_cont.append(pd.Series(row_out))
        except BaseException as e:
            if debug:
                print(e)
                continue
            else:
                raise
    tm_df = pd.concat(tm_cont, axis=1).T
    tm_df = tm_df.set_index('idx')
    df = pd.merge(df, tm_df, right_index=True, left_index=True)
    return df


def add_time_features(df):
    df['day_of_week'] = df['event_date'].apply(lambda x: days_of_week[x.weekday()])
    df['time_of_day'] = df['event_date'].apply(lambda x: x.hour)
    df['on_sale_period'] = df.apply(lambda x: (x['event_date'] - x['on_sale_date']).total_seconds() / 60 / 60 / 24,
                                    axis=1)
    df['days_to_event'] = df.apply(lambda x: (x['event_date'] - x['sample_date'].to_pydatetime()).total_seconds()/60/60/24, axis=1)
    df['days_on_sale'] = df.apply(lambda x: (x['sample_date'].to_pydatetime() - x['on_sale_date']).total_seconds()/60/60/24, axis=1)
    df['event_complete'] = df['days_to_event'] < 0
    df.loc[df['event_complete'], 'days_on_sale'] = df.loc[df['event_complete'], 'on_sale_period']
    df.loc[df['event_complete'], 'days_to_event'] = np.nan
    return df

def add_local_popularity(df):
    gt = google_trends.Trends()
    gt_cont = []
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Trends is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = {}
            row_out['pop_country'], row_out['pop_region'] = gt.get_geo_trends(row['performers'], 'today 5-y', gt.get_iso_region(row['lat'],row['long']))
            row_out['idx'] = idx
            gt_cont.append(pd.Series(row_out))
        except BaseException as e:
            if debug:
                print(e)
                continue
            else:
                raise
    gt_df = pd.concat(gt_cont, axis=1).T
    gt_df = gt_df.set_index('idx')
    df = pd.merge(df, gt_df, right_index=True, left_index=True)
    return df

def add_demographics(df):
    dg = demographics.Demographics()
    dg_cont = []
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Demo is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = {}
            row_out['city_population'], row_out['iso_region'], row_out['iso_country'] = dg.get_pop(row['city'], row['country'])
            row_out['idx'] = idx
            dg_cont.append(pd.Series(row_out))
        except BaseException as e:
            if debug:
                print(e)
                continue
            else:
                raise
    gt_df = pd.concat(dg_cont, axis=1).T
    gt_df = gt_df.set_index('idx')
    df = pd.merge(df, gt_df, right_index=True, left_index=True)
    return df

if __name__ == '__main__':
    df = pd.read_pickle(os.path.join(my_file,'../../data/ticketmaster.pkl')).reset_index(drop=True)
    #df = df.tail(n=100).reset_index(drop=True)
    #df = df.drop([col for col in df.columns if 'avail' in col], axis=1)
    df = add_songkick(df)
    #df = add_ticket_levels(df)
    df = add_time_features(df)
    df = add_local_popularity(df)
    df = add_demographics(df)
    print(df)

