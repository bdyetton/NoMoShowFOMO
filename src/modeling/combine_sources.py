import pandas as pd
import os
my_file = os.path.dirname('__file__')
import src.data_sources.songkick as songkick
import src.data_sources.google_trends as google_trends
import src.data_sources.demographics as demographics
import src.data_sources.ticketmaster as ticketmaster
import numpy as np
import sys
import pickle
debug = False


def add_songkick(df):
    sk = songkick.SongKick()
    sk_cont = []
    print('running sk for ', df.shape[0],'records')
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('SK is', 100 * idx / df.shape[0], 'percent complete')
        try:
            venue_series = sk.get_songkick_data_for_event(row)
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
        venue_series['idx'] = idx
        sk_cont.append(venue_series)
    sk_df = pd.concat(sk_cont, axis=1, sort=True).T
    sk_df = sk_df.set_index('idx')
    return sk_df


def add_ticket_levels(df):
    tm = ticketmaster.TicketMaster()
    tm_cont = []
    print('running avail for ', df.shape[0], 'records')
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('TM is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = tm.add_availability_info(row)
            row_out['idx'] = idx
            tm_cont.append(row_out)
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
    tm_df = pd.concat(tm_cont, axis=1).T
    tm_df = tm_df.set_index('idx')
    return tm_df

def add_time_features(df):
    tm = ticketmaster.TicketMaster()
    tm_cont = []
    print('running time for ', df.shape[0], 'records')
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Time is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = tm.get_time_features_for_event(row)
            row_out['idx'] = idx
            tm_cont.append(row_out)
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
    tm_df = pd.concat(tm_cont, axis=1).T
    tm_df = tm_df.set_index('idx')
    return tm_df

def add_local_popularity(df):
    gt = google_trends.Trends()
    gt_cont = []
    print('running popularity for ', df.shape[0], 'records')
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Trends is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = gt.get_geo_trends(row['performers'], 'today 5-y', gt.get_iso_region(row['lat'],row['long']))
            row_out['idx'] = idx
            gt_cont.append(row_out)
        except KeyboardInterrupt:
            return
        except BaseException as e:
            raise e
            print(idx)
            if not debug:
                print(e)
                continue
            else:
                raise
    gt_df = pd.concat(gt_cont, axis=1).T
    gt_df = gt_df.set_index('idx')
    return gt_df

def add_availability(df):
    tm = ticketmaster.TicketMaster()

    tm_cont = []
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Avail is', 100 * idx / df.shape[0], 'percent complete')
        try:
            if 'avail_checked' in row.index and row['avail_checked']:
                continue
            row_out = tm.add_availability_info(row)
            row_out['idx'] = idx
            tm_cont.append(pd.Series(row_out))
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
    tm_df = pd.concat(tm_cont, axis=1).T
    tm_df = tm_df.set_index('idx')
    return tm_df

def parse_events(events):
    tm = ticketmaster.TicketMaster()
    events = tm.parse_events_to_df(events)
    print('Got', events.shape[0],'records')
    return events

def add_demographics(df):
    tm = ticketmaster.TicketMaster()
    dg = demographics.Demographics(tm.city_to_city_map, tm.country_to_country_map)
    dg_cont = []
    print('running demo for ', df.shape[0], 'records')
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Demo is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = dg.get_pop(row['city'], row['country'])
            row_out['idx'] = idx
            dg_cont.append(row_out)
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
    dg_df = pd.concat(dg_cont, axis=1).T
    dg_df = dg_df.set_index('idx')
    return dg_df

if __name__ == '__main__':
    basedate = sys.argv[1]
    routine = sys.argv[2]
    if routine == 'get_events':
        print('getting_events')
        tm = ticketmaster.TicketMaster()
        events = tm.get_events(event_limit=None)
        pickle.dump(events, open('../../data/tickemaster_event_scrap_'+basedate+'.pkl','wb'))
    if routine == 'parse_events':
        print('parsing_events')
        events = pd.read_pickle(os.path.join(my_file,'../../data/tickemaster_event_scrap_'+basedate+'.pkl'))
        df = parse_events(events)
        df.to_pickle('../../data/events_'+basedate+'.pkl')
    if routine == 'avail':
        df_events = pd.read_pickle('../../data/events_' + basedate + '.pkl')
        df = add_availability(df_events)
        df = pd.merge(df, df_events, right_index=True, left_index=True)
        df = df.loc[df['avail_first_tier']!='unknown',:]
        df.to_pickle('../../data/events_and_avail_'+basedate+'.pkl')
    if routine == 'songkick':
        df_events = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        df = add_songkick(df_events)
        df.to_pickle('../../data/songkick_'+basedate+'.pkl')
    if routine == 'time':
        df_events = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        df = add_time_features(df_events)
        df.to_pickle('../../data/time_'+basedate+'.pkl')
    if routine == 'popularity':
        df_events = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        df = add_local_popularity(df_events)
        df.to_pickle('../../data/popularity_'+basedate+'.pkl')
    if routine == 'demographics':
        df_events = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        df = add_demographics(df_events)
        df.to_pickle('../../data/demographics_'+basedate+'.pkl')
    if routine == 'combine':
        df_base = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        for table in ['demographics','popularity','songkick','time']:
            df = pd.read_pickle('../../data/'+table+'_'+basedate+'.pkl')
            df_base = pd.merge(df_base, df, right_index=True, left_index=True)
        df.to_pickle('../../data/combined_'+basedate+'.pkl')

