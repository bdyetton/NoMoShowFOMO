from src.data_sources.ticketmaster import TicketMaster
import datetime
import pickle
from time import sleep
tm = TicketMaster()
time_started = datetime.datetime.now() - datetime.timedelta(days=1)
while True:
    if datetime.datetime.now() - time_started > datetime.timedelta(days=1):
        time_started = datetime.datetime.now()
        print('Grabbing Events', time_started)
        events = tm.get_events(event_limit=10000)
        pickle.dump(events,
                    open('../../data/tickemaster_event_scrap_' + time_started.strftime(
                        '%d-%m-%Y') + '.pkl', "wb"))
        print('Wrote Events', datetime.datetime.now())
    sleep(60*60)
    print('sleeping')