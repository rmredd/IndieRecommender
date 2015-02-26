from flask import render_template, request
from app import app
from recommender import recommend_games
import MySQLdb as mdb
import numpy as np
import pandas as pd

from login_script import login_mysql

#Read login info
db = login_mysql('login.txt')
charset = 'utf8'

#Get the full list of indie game words -- this may take a bit to load
words_indie_matrix = pd.read_csv("words_tf_idf.csv").as_matrix()[:,1:]

#Get the full list of Metacritic game titles
with db:
   cur = db.cursor()
   meta_titles = recommend_games.get_list_of_metacritic_titles(cur)
db.close()

@app.route('/')
@app.route('/index')
def index():
   user = { 'nickname': 'Miguel' } # fake user
   return render_template("index.html",
                          title = 'Home',
                          user = user,
                          meta_titles = meta_titles)

@app.route('/db')
def games_page():
    with db:
        cur = db.cursor()
        cur.execute("SELECT title FROM Games LIMIT 15;")
        query_results = cur.fetchall()
    games = ""
    for result in query_results:
        games += result[0]
        games += "<br>"
    return games

@app.route("/db_fancy")
def games_page_fancy():
    with db:
        cur = db.cursor()
        cur.execute("SELECT title, creator, game_type, rating \
             FROM Games ORDER BY votes DESC LIMIT 15;")

        query_results = cur.fetchall()
    games = []
    for result in query_results:
        games.append(dict(title=result[0], creator=result[1], game_type=result[2], rating=result[3]))
    return render_template('games.html', games=games)

@app.route('/output', methods=['GET'])
def games_output():
  #Make sure we're all logged in
  db = login_mysql('login.txt')
  #pull 'ID' from input field and store it
  game = request.args.get('game_select')
  
  platforms = []

  #Get whether or not the checkboxes are checked
  if 'platform_w' in request.values.keys():
     platforms.append(request.values['platform_w'])
  if 'platform_m' in request.values.keys():
     platforms.append(request.values['platform_m'])
  if 'platform_l' in request.values.keys():
     platforms.append(request.values['platform_l'])

  #If there was no input, pull the "no entry" output instead
  if game == "" or game == None:
     return render_template("output_nogame.html", meta_titles = meta_titles, platforms = platforms )

  with db:
    cur = db.cursor()
    #just select the city from the world_innodb that the user inputs
    titles, game_types, themes, ratings, sim_ratings, game_urls, rel_words = recommend_games.run_everything_on_input_title(game,platforms,words_indie_matrix,cur,min_votes=5, nvalues=6)

  games = []
  #Checking to see if the game itself has been returned in the list, and removing it if so
  if game in titles:
     non_duplicate = np.where(titles != game)[0]
     for i in non_duplicate:
        games.append(dict(title=titles[i], game_type=game_types[i], theme=themes[i], rating=ratings[i],
                          sim_rating=int(sim_ratings[i]*100+0.5), url=game_urls[i]))
  else:
     for i in range(np.min([len(titles),5])):
        games.append(dict(title=titles[i], game_type=game_types[i], theme=themes[i], rating=ratings[i],
                          sim_rating=int(sim_ratings[i]*100+0.5), url=game_urls[i]))

  if len(platforms) == 0:
     return render_template("output.html", big_game = game, games = games, meta_titles = meta_titles, rel_words=rel_words)
  else:
     return render_template("output.html", big_game = game, games = games, platforms = platforms, 
                            meta_titles = meta_titles, rel_words = rel_words)

@app.route('/about')
def games_about():
   return render_template("about.html")

@app.route('/contact')
def games_contact():
   return render_template("contact.html")

@app.route('/slides')
def slides():
   return render_template("slides.html")
