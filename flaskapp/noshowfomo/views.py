from flask import render_template, request
from noshowfomo import app
from noshowfomo.models import SelloutClassifier

# Python code to connect to Postgres
# You may need to modify this based on your OS,
# as detailed in the postgres dev setup materials.
#user = 'bdyet' #add your Postgres username here
#host = 'localhost'
#dbname = 'birth_db'
#dbpw = 'Nap4life'
#db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
#con = None
#con = psycopg2.connect(database = dbname, user = user, host = host, password = dbpw) #add your Postgres password here

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/output')
def output():
  ticketmaster_url = request.args.get('input_url')
  print('Got-------', ticketmaster_url)
  sc = SelloutClassifier()
  will_sell_out = sc.predict_from_url(ticketmaster_url='sdasd')
  artist, venue, location = sc.get_event_details()
  return render_template("output.html", artist=artist, venue=venue, location=location, will_sell_out=will_sell_out)