from flask import render_template, request, redirect
from noshowfomo import app
from noshowfomo.models import predict_from_url

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

@app.route('/nomoshowfomo')
@app.route('/nomoshowfomo/')
def nomoshowfomo():
    return render_template("nomoshowfomo.html")

@app.route('/nomoshowfomo/slides')
@app.route('/nomoshowfomo/slides/')
def slide_link():
    print('Redirecting to google slides')
    return redirect('https://docs.google.com/presentation/d/1mMAviK2M_NZML94paKmBVSNm8phbRax7RivjC0Js2Dk/edit?usp=sharing')

@app.route('/nomoshowfomo/code')
@app.route('/nomoshowfomo/code/')
def code_link():
    print('Redirecting to github')
    return redirect('https://github.com/bdyetton/NoMoShowFOMO')


@app.route('/nomoshowfomo/go')
def nomoshowfomo_go():
    ticketmaster_url = request.args.get('input_url')
    print('Got-------', ticketmaster_url)
    try:
        will_sell_out, artist, venue, city, country, event_url = predict_from_url(ticketmaster_url)
    except Exception as e:
        return render_template("nomoshowfomo_ohno.html", error=str(e), event_url=ticketmaster_url)
    else:
        return render_template("nomoshowfomo_show.html", artist=artist,
                               venue=venue, city=city,
                               country=country, will_sell_out=will_sell_out, event_url=event_url)