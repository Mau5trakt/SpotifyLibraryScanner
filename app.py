import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template
from tkns import client_id, client_secret
from tqdm import tqdm
from cs50 import SQL
import logging

app = Flask(__name__)
db = SQL("sqlite:///music.db")

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = 'YOUR_SECRET_KEY'

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'


# route to handle logging in
@app.route('/')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)


# route to handle the redirect URI after authorization
@app.route('/home')
def show_home():
    return render_template("home.html")



@app.route('/redirect')
def redirect_page():
    # clear the session
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info
    # redirect the user to the albmus route
    return redirect(url_for('albums', _external=True))


@app.route('/addAlbumsSongs')
def add_album_songs():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect("/")
    logging.disable()
    sp = spotipy.Spotify(auth=token_info['access_token'], requests_timeout=15)

    albums = db.execute("SELECT album_id, album_artist_name from albums")
    for a in tqdm(albums):
        # print(a['album_id'])
        print(a)
        songs = sp.album_tracks(a['album_id'])
        for song in songs['items']:
            print(f"song: {song['name']} id: {song['id']} artist: {a['album_artist_name']}")
            qty_song = db.execute("SELECT COUNT(*) as qty  FROM library WHERE song_id = ?", song['id'])[0]['qty']
            if qty_song == 0:
                db.execute("INSERT INTO library(song_id, song_name, artist_name) VALUES (?, ?, ?)", song['id'],
                           song['name'], a['album_artist_name'])
            else:
                print("Song already in the library")

    return render_template("albums.html")


@app.route("/addPlaylistsSongs")
def playlists():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect("/")
    logging.disable()
    sp = spotipy.Spotify(auth=token_info['access_token'], requests_timeout=15)

    # add all the playlists, then look through all the songs on it

    playlists = sp.current_user_playlists(limit=1)

    counter = 0

    while counter < playlists['total']:
        pl = sp.current_user_playlists(limit=1, offset=counter)
        print(pl['items'][0]['name'])
        print(pl['items'][0]['id'])

        qty = db.execute("SELECT COUNT(*) AS qty FROM playlists WHERE playlist_id = ? ", pl['items'][0]['id'])[0]['qty']


        if qty == 0:
            db.execute("INSERT INTO playlists (playlist_id, playlist_name) VALUES (?, ?)", pl['items'][0]['id'], pl['items'][0]['name'])
        else:
            print("Playlist already added")

        counter += 1

    total_playlist = db.execute("SELECT * FROM playlists")


    for p in total_playlist:
        actual_playlist = sp.playlist(p['playlist_id'])
        actual_playlist_total = actual_playlist['tracks']['total'] #number of songs on it
        song_counter = 0


        print(actual_playlist['name'])
        print(actual_playlist['tracks']['items'][song_counter]['track']['name'], actual_playlist['tracks']['items'][song_counter]['track']['id'], actual_playlist['tracks']['items'][song_counter]['track']['artists'][0]['name'])
        while song_counter < actual_playlist_total:

            qty = db.execute("SELECT COUNT(song_id) as qty FROM library WHERE song_id = ?", actual_playlist['tracks']['items'][song_counter]['track']['id'])[0]['qty']

            if qty == 0:
                db.execute("INSERT INTO library(song_id, song_name, artist_name) VALUES(?, ?, ?)", actual_playlist['tracks']['items'][song_counter]['track']['id'], actual_playlist['tracks']['items'][song_counter]['track']['name'], actual_playlist['tracks']['items'][song_counter]['track']['artists'][0]['name'])
            else: print("Song Already Added!!")

            song_counter += 1
    
    return render_template("playlists.html")


@app.route('/addLikedSongs')
def liked_songs():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect("/")
    logging.disable()

    sp = spotipy.Spotify(auth=token_info['access_token'], requests_timeout=15)

    liked = sp.current_user_saved_tracks(limit=1, )

    total = liked['total']
    counter = 0
    print(total)
    pbar = tqdm(total=total)
    while counter < total:
        song = sp.current_user_saved_tracks(limit=1, offset=counter)
        print(
            f"song: {song['items'][0]['track']['name']} Artist: {song['items'][0]['track']['artists'][0]['name']} Id: {song['items'][0]['track']['id']}")
        qty = \
        db.execute("SELECT COUNT(song_id) AS qty FROM library WHERE song_id = ?", song['items'][0]['track']['id'])[0][
            'qty']
        if qty == 0:
            db.execute("INSERT INTO library(song_id, song_name, artist_name) VALUES (?, ?, ?)",
                       song['items'][0]['track']['id'], song['items'][0]['track']['name'],
                       song['items'][0]['track']['artists'][0]['name'])
            print("Inserted!")
        else:
            print("Song already in library")

        pbar.update(1)
        counter += 1

    pbar.close()
    return render_template("liked.html")


@app.route('/userAlbums')
def albums():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect("/")

    sp = spotipy.Spotify(auth=token_info['access_token'])
    # get the albums of a user

    albums = sp.current_user_saved_albums()

    counter = 0

    cuantity = albums['total']

    pbar = tqdm(total=cuantity)
    logging.disable()
    while counter < cuantity:
        print(f"Album: {sp.current_user_saved_albums(limit=1, offset=counter)['items'][0]["album"]["name"]}  Artista: {sp.current_user_saved_albums(limit=1, offset=counter)['items'][0]["album"]["artists"][0]['name']} Id: {sp.current_user_saved_albums(limit=1, offset=counter)['items'][0]["album"]["id"]}")

        query = db.execute("SELECT COUNT(album_id) AS qty FROM albums where album_id = ?",
                           sp.current_user_saved_albums(limit=1, offset=counter)['items'][0]["album"]["id"])[0]['qty']

        if query == 0:
            db.execute("INSERT INTO albums(album_id, album_name, album_artist_name) VALUES(?,?,?)",
                       sp.current_user_saved_albums(limit=1, offset=counter)['items'][0]["album"]["id"],
                       sp.current_user_saved_albums(limit=1, offset=counter)['items'][0]["album"]["name"],
                       sp.current_user_saved_albums(limit=1, offset=counter)['items'][0]["album"]["artists"][0][
                           'name'])
            print("Insertion Made")

        counter += 1
        pbar.update(1)

    pbar.close()

    return "Albums"


# function to get the token info from the session
# credits to: Synsation
# https://www.youtube.com/watch?v=mBycigbJQzA&t=1378s
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))

    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-library-read playlist-modify-public playlist-modify-private'
    )


if __name__ == "__name__":
    app.run()
