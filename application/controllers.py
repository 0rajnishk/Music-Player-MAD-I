import base64
from flask import g, jsonify, render_template, request, redirect, url_for, session, flash
from application import app
from application.models import  User, Album, Song, SongRating, Comment, Playlist, RecentlyPlayedSongs
from application.database import db
from sqlalchemy import and_, func, not_, or_, desc
from sqlalchemy.exc import IntegrityError
from datetime import date
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

app.secret_key = 'development key'  

@app.before_request
def load_user():
    g.user = None
    if 'id' in session:
        g.user = User.query.get(session['id'])

def addadmin():
    if User.query.filter_by(role='admin').first():
        return
    user1 = User('a@gmail.com', '1', 'admin1',  'admin')
    user2 = User('c@c.com', '1', 'creator1', 'creator')
    db.session.add(user1, user2)
    db.session.commit()


    
@app.template_filter('img_to_base64')
def convert_img_to_base64_filter(image_data):
    if image_data:
        return base64.b64encode(image_data).decode('utf-8')
    return None

# get song name from song id
@app.template_filter('song_name')
def get_song_name(song_id):
    if song_id:
        song = Song.query.get(song_id)
        return song.name
    return None

def calculate_average_rating(song_id, decimal_places=2):
    # Get the rounded average rating for a specific song
    average_rating = db.session.query(func.round(func.avg(SongRating.rating), decimal_places)).filter_by(song_id=song_id).scalar()

    # If there are no ratings for the song, set average_rating to 0
    average_rating = average_rating if average_rating is not None else 0

    return average_rating



# get song image from song id
@app.template_filter('song_image')
def get_song_image(song_id):
    if song_id:
        song = Song.query.get(song_id)
        return song.image
    return None

# get base64 song  from audio file
@app.template_filter('audio_to_base64')
def convert_audio_to_base64_filter(audio_data):
    if audio_data:
        return base64.b64encode(audio_data).decode('utf-8')   
    return None


@app.route('/getsong/<int:id>')
def getsong(id):
    song = Song.query.get(id)
    if song:
        audio_data = base64.b64encode(song.audio_file).decode('utf-8')
        image = base64.b64encode(song.image).decode('utf-8')
        song_name = song.name
        singer = song.singer
        lyrics = song.lyrics
        # increment play count
        song.increment_play_count()
        # average rating
        rating = calculate_average_rating(id, decimal_places=1)
        print(rating , '*'*100)
        return {
            'id': id,
            'rating': rating,
            'audio_data': audio_data,
            'image': image,
            'song_name': song_name,
            'singer': singer,
            'lyrics': lyrics
        }
    else:
        return "Song details not found", 404

# recently played song to database
@app.route('/recentlyplayed/<int:id>', methods=['GET', 'POST'])
def recentlyplayed(id):
    recentlyplayed = RecentlyPlayedSongs.query.filter_by(user_id=session['id']).order_by(RecentlyPlayedSongs.timestamp.desc()).all()
    
    # if the song is already in recently played, delete it
    for i in recentlyplayed:
        if i.song_id == id and i.user_id == session['id']:
            db.session.delete(i)
            db.session.commit()

    if request.method == 'POST':
        user_id = session['id']
        song_id = id
        new_recentlyplayed = RecentlyPlayedSongs(user_id=user_id, song_id=song_id)
        db.session.add(new_recentlyplayed)
        db.session.commit()
        return "Successfully added to recently played", 200
    
    return "Error occurred while adding the recently played song", 400


@app.route('/')
def index():
    try:
        allsongs = Song.query.all()
        len_song = len(allsongs)
        songs = Song.query.order_by(Song.id.desc()).limit(5).all()
        recentlyplayed = RecentlyPlayedSongs.query.filter_by(user_id=session['id']).order_by(RecentlyPlayedSongs.timestamp.desc()).all()       
        playlists = Playlist.query.filter_by(user_id=session['id']).all()
        bollywood = Song.query.filter_by(genre='bollywood').order_by(Song.id.desc()).limit(5).all()
        len_bollywood_song = len(bollywood)
        devotional = Song.query.filter_by(genre='devotional').order_by(Song.id.desc()).limit(5).all()
        len_devotional_song = len(devotional)
        trendingsongs = Song.query.order_by(Song.play_count.desc()).limit(5).all()
        len_trending_song = len(trendingsongs)
        albums = Album.query.limit(5).all()
        len_album = len(albums)
        if g.user:
            if g.user.role == 'admin':
                return redirect(url_for('adminDashboard'))
            else:
                return render_template('index.html', creator=True, albums=albums , songs=songs, len_song = len_song, recentlyplayed = recentlyplayed, playlists = playlists, bollywood = bollywood, devotional = devotional, trendingsongs= trendingsongs , len_bollywood_song= len_bollywood_song, len_devotional_song = len_devotional_song, len_trending_song = len_trending_song, len_album=len_album), 200
    except:
        session.pop('id', None)
        return render_template('login.html', alert='You are not logged in'), 401


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        role = "user"
        user = User(email, password, name, role)
        try:
            db.session.add(user)
            db.session.commit()
            session['id'] = user.id
            session['email'] = user.email
            session['name'] = user.name
            session['role'] = user.role
            return render_template('login.html',  alert = 'You were successfully registered. Login to continue'), 200
        except IntegrityError as e:
            return render_template('login.html', alert='Email already exists. Please try again with a different email address.'), 401
    else:
        return render_template('login.html'), 401


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = user = User.query.filter(and_(User.email == email, User.role.in_(['user', 'creator']))).first()
        if user and user.password == password:
            session['id'] = user.id
            session['email'] = user.email
            session['name'] = user.name
            session['role'] = user.role
            flash('You were successfully logged in', 'success')
            return redirect(url_for('index'))
        else:
            return render_template('login.html', alert='Invalid username or password')
    else:
        return render_template('login.html'), 200


@app.route('/admin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, role='admin').first()
        if user is not None and user.password == password:
            session['id'] = user.id
            session['email'] = user.email
            session['name'] = user.name
            session['role'] = user.role
            return redirect(url_for('adminDashboard'))
        else:
            return render_template('adminlogin.html', error='Invalid username or password')

    return render_template('adminlogin.html')


@app.route('/adminDashboard', methods=['GET', 'POST'])
def adminDashboard():
    creators = User.query.filter_by(role='creator').all()
    songs = Song.query.all()
    albums = Album.query.all()
    users = User.query.filter_by(role='user').all()
    top_five_songs = Song.query.order_by(Song.play_count.desc()).limit(5).all()


    labels = [song.name for song in top_five_songs]
    play_counts = [song.play_count for song in top_five_songs]

    # Create a new figure and axes for the horizontal bar chart
    fig_bar, ax_bar = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
    ax_bar.barh(labels, play_counts, color='skyblue')
    ax_bar.set_title('Top Five Songs by Play Count')
    ax_bar.set_xlabel('Play Count')
    ax_bar.set_ylabel('Song Name')  # Add ylabel for song names

    # Rotate the labels for better visibility
    ax_bar.tick_params(axis='y', rotation=45)

    # Save the horizontal bar chart to a BytesIO object
    img_bar = BytesIO()
    fig_bar.savefig(img_bar, format='png', bbox_inches='tight')  # Use bbox_inches='tight' to prevent labels cutoff
    img_bar.seek(0)
    bar_chart_url = base64.b64encode(img_bar.getvalue()).decode()

    # creating a combined bar chart for the total number of songs, albums, users, and creators
    categories = ['Songs', 'Albums', 'Users', 'Creators']
    counts = [len(songs), len(albums), len(users), len(creators)]

    # Create a new figure and axes for the combined bar chart
    fig_combined, ax_combined = plt.subplots()
    ax_combined.bar(categories, counts, color='lightcoral')
    ax_combined.set_title('Total Number of Songs, Albums, Users, and Creators')
    ax_combined.set_xlabel('Categories')
    ax_combined.set_ylabel('Count')

    # Save the combined bar chart to a BytesIO object
    img_combined = BytesIO()
    fig_combined.savefig(img_combined, format='png')
    img_combined.seek(0)
    combined_chart_url = base64.b64encode(img_combined.getvalue()).decode()

    return render_template('adminDashboard.html', combined_chart_url = combined_chart_url, bar_chart_url=bar_chart_url, albums=albums, songs=songs, creators=creators, top_five_songs=top_five_songs, users=users)

@app.route('/creator', methods=['GET', 'POST'])
def creatorDashboard():
    # top 5 songs by creator
    top_five_songs = Song.query.filter_by(user_id=session['id']).order_by(Song.play_count.desc()).limit(5).all()
    labels = [song.name for song in top_five_songs]
    play_counts = [song.play_count for song in top_five_songs]

    # Create a new figure and axes for the horizontal bar chart
    fig_bar, ax_bar = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
    ax_bar.barh(labels, play_counts, color='skyblue')
    ax_bar.set_title('Top Five Songs by Play Count')
    ax_bar.set_xlabel('Play Count')
    ax_bar.set_ylabel('Song Name')  # Add ylabel for song names

    # Rotate the labels for better visibility
    ax_bar.tick_params(axis='y', rotation=45)

    # Save the horizontal bar chart to a BytesIO object
    img_bar = BytesIO()
    fig_bar.savefig(img_bar, format='png', bbox_inches='tight')  # Use bbox_inches='tight' to prevent labels cutoff
    img_bar.seek(0)
    bar_chart_url = base64.b64encode(img_bar.getvalue()).decode()
    if request.args.get('H') and g.user.role != 'admin':
        user = User.query.get(session['id'])
        user.role = 'creator'
        db.session.commit()
        session['role'] = 'creator'
        return redirect(url_for('creatorDashboard'))
    elif g.user:
        albums = Album.query.filter_by(user_id=session['id']).all()
        songs = Song.query.filter_by(user_id=session['id']).all()
        if g.user.role == 'creator':
            return render_template('creatorDashboard.html',bar_chart_url= bar_chart_url, albums=albums, songs = songs, creator=True)
        elif g.user.role == 'user':
            return render_template('creatorDashboard.html', creator = False)
        elif g.user.role == 'admin':
            return redirect(url_for('adminDashboard'))
    return redirect(url_for('index'))

@app.route('/addalbum', methods=['GET', 'POST'])
def addalbum():
    user = User.query.get(session['id'])
    if g.user and user.role == 'creator' and not g.user.blacklist:
        if request.method == 'POST':
            name = request.form['name']
            singer = request.form['singer']
            genre = request.form['genre']
            new_album = Album(name=name, singer=singer, user_id=session['id'], genre=genre)
            db.session.add(new_album)
            db.session.commit()
            return redirect(url_for('creatorDashboard'))
        return render_template('addalbum.html')
    return redirect(url_for('creatorDashboard', alert='Not allowed: error "You have been blacklisted"')), 401


@app.route('/editalbum/<int:id>', methods=['GET', 'POST'])
def editalbum(id):
    if g.user and session['role'] == 'admin':
        album = Album.query.get(id)
        if request.method == 'POST':
            album.name = request.form['name']
            album.singer = request.form['singer']
            album.genre = request.form['genre']
            db.session.commit()
            return redirect(url_for('creatorDashboard'))
        return render_template('editalbum.html', album=album)
    return redirect(url_for('adminlogin'))


@app.route('/deletealbum/<int:id>', methods=['GET', 'POST'])
def deletealbum(id):
    if g.user:
        if session['role'] == 'admin':
            album = Album.query.get(id)
            db.session.delete(album)
            db.session.commit()
            return redirect(url_for('adminDashboard'))
        
        elif session['role'] == 'creator':
            album = Album.query.get(id)
            db.session.delete(album)
            songs = Song.query.filter_by(album_id=id).all()
            for song in songs:
                db.session.delete(song)
            db.session.commit()
            return redirect(url_for('creatorDashboard'))
    return redirect(url_for('creatorDashboard'))


@app.route('/viewalbums')
def viewalbums():
    return Album.query.all()

@app.route('/viewsongs')
def viewsongs():
    return Song.query.all()

# view all songs
@app.route('/viewallsongs', methods=['GET', 'POST'])
def viewallsongs():
    recentlyplayed = RecentlyPlayedSongs.query.filter_by(user_id=session['id']).order_by(RecentlyPlayedSongs.timestamp.desc()).all()

    try:
        title = request.form['title']
        if title == 'devotional':
            songs = Song.query.filter_by(genre=title).all()
            return render_template('viewsong.html', songs=songs, recentlyplayed=recentlyplayed)
        elif title == 'newreleases':
            songs = Song.query.order_by(Song.id.desc()).all()
            return render_template('viewsong.html', songs=songs, recentlyplayed=recentlyplayed)
        elif title == 'trendingsongs':
            songs = Song.query.order_by(Song.play_count.desc()).all()
            return render_template('viewsong.html', songs=songs, recentlyplayed=recentlyplayed)
        elif title == 'bollywood':
            songs = Song.query.filter_by(genre=title).all()
            return render_template('viewsong.html', songs=songs, recentlyplayed=recentlyplayed)
        elif title == 'album':
            albums = Album.query.all()
            return render_template('allalbums.html', albums=albums, recentlyplayed=recentlyplayed)
    except:
        songs = Song.query.all()
        return render_template('viewsong.html', songs=songs, recentlyplayed=recentlyplayed)


@app.route('/addsong', methods=['GET', 'POST'])
def addsong():
    if g.user and session['role'] == 'creator' and not g.user.blacklist:
        if request.method == 'POST':
            name = request.form['name']
            audio_file = request.files['song'].read()
            image = request.files['image'].read()
            genre = request.form['genre']
            print(genre, '*'*100)
            lyrics = request.form['lyrics']
            date = request.form['date_created']
            singer = request.form['singer']
            try:
                album_id = request.form['album_id']
            except:
                album_id = None
            artist_id = session['id']
            
            song = Song(name,  artist_id, audio_file, image,  date, lyrics, singer, album_id, genre )
            song.audio_file = audio_file
            song.genre = genre
            song.image = image
            try:
                db.session.add(song)
                db.session.commit()
                return redirect(url_for('creatorDashboard'))
            except IntegrityError as e:
                return render_template('addsong.html', alert='Song already exists. Please try again with a different song name.'), 401
        return render_template('addsong.html')
    return redirect(url_for('index'))


@app.route('/editsong/<int:id>', methods=['GET', 'POST'])
def editsong(id):
    # fetch albums of the user
    albums = Album.query.filter_by(user_id=session['id']).all()
    if g.user and session['role'] == 'creator':
        if session['id'] == Song.query.get(id).user_id:
            song = Song.query.get(id)   
            print(song.genre, '*'*100)
            if request.method == 'POST':
                song.name = request.form['name'] if request.form['name'] else song.name
                song.singer = request.form['singer'] if request.form['singer'] else song.singer
                audio_file = request.files.get('song')  # Use get() to avoid KeyError
                song.genre = request.form['genre'] if request.form['genre'] else song.genre
                # song.lyrics = request.form['lyrics'] if request.form['lyrics'] else song.lyrics
                song.date_created = request.form['date_created'] if request.form['date_created'] else song.date_created
                # song.lyrics = request.form['lyrics'] if request.form['lyrics'] else song.lyrics
                if len(song.lyrics)>0:
                    song.lyrics = request.form['lyrics']
                else:
                    song.lyrics = song.lyrics

                if audio_file:
                    song.audio_file = audio_file.read()
                else:
                    song.audio_file = song.audio_file
                try:
                    song.album_id = request.form['album'] if request.form['album'] else song.album_id
                except:
                    song.album_id = song.album_id

                # Handle image
                image_file = request.files.get('image')
                if image_file:
                    song.image = image_file.read()
                else:
                    song.image = song.image
                db.session.commit()
                return redirect('/creator')

            return render_template('editsong.html', song=song, albums = albums)
    return redirect(url_for('adminlogin'))



@app.route('/deletesong/<int:id>', methods=['GET', 'POST'])
def deletesong(id):
    if g.user and session['role'] == 'admin':
        song = Song.query.get(id)
        try:
            db.session.delete(song)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()  # Rollback changes if there's an integrity error
            flash('Error: Unable to delete the song. It may be associated with other records.', 'error')
        else:
            flash('Song deleted successfully!', 'success')
        return render_template('adminDashboard.html', alert='Song deleted successfully.')
    elif g.user and session['role'] == 'creator':
        song = Song.query.get(id)
        if song.user_id == session['id']:
            try:
                db.session.delete(song)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()  
                flash('Error: Unable to delete the song. It may be associated with other records.', 'error')
            else:
                flash('Song deleted successfully!', 'success')
            return render_template('creatorDashboard.html', alert='Song deleted successfully.', creator=True)
    return redirect(url_for('adminlogin'))



@app.route('/viewalbum/<int:id>')
def viewalbum(id):
    album = Album.query.get(id)
    songs = Song.query.filter_by(album_id=id).all()
    recentlyplayed = RecentlyPlayedSongs.query.filter_by(user_id=session['id']).order_by(RecentlyPlayedSongs.timestamp.desc()).all()
    return render_template('viewalbum.html', album=album, songs=songs, recentlyplayed=recentlyplayed)

# view a albums for creator and admin
@app.route('/viewaalbums/<int:id>')
def viewaalbums(id):
    if g.user and session['role'] == 'creator':
        albums = Album.query.get(id)
        songs = Song.query.filter_by(album_id=id).all()
        return render_template('viewaalbums.html', album=albums, songs=songs)
    elif g.user and session['role'] == 'admin':
        albums = Album.query.get(id)
        songs = Song.query.filter_by(album_id=id).all()
        return render_template('viewadminalbums.html', album=albums, songs=songs)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    if g.user:
        name = session['name']
        role = session['role']
        if session['role'] == 'admin':
            session.pop('id', None)
            session.pop('email', None)
            session.pop('name', None)
            session.pop('role', None)
            return render_template('adminlogin.html', alert= f"{role} {name}: Logged out successfully "), 200
        session.pop('id', None)
        session.pop('email', None)
        session.pop('name', None)
        session.pop('role', None)
        return render_template('login.html', alert= f"{role} {name}: Logged out successfully "), 200
    return render_template('login.html', alert='You are not logged in'), 401
        


@app.route('/viewusers')
def viewusers():
    if g.user and session['role'] == 'admin':
        users = User.query.all()
        return render_template('viewusers.html', users=users)
    return redirect(url_for('adminlogin'))



@app.route('/addcommnent/<int:id>', methods=['GET', 'POST'])
def addcomment(id):
    if g.user:
        if request.method == 'POST':
            comment = request.form['comment']
            user_id = session['id']
            song_id = id
            new_comment = Comment(comment=comment, user_id=user_id, song_id=song_id)
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('index', id=id))
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    user = User.query.get(session['id'])
    if request.method == 'POST':
        name = request.form['search']

        # Search songs based on name, rating, and genre
        songs = (
            Song.query
            .filter(
                or_(
                    Song.name.like(f'%{name}%'),
                    Song.genre.like(f'%{name}%'),
                    Song.singer.like(f'%{name}%'),
                )
            )
            .all()
        )

        # Search albums based on name, artist, and genre
        albums = (
            Album.query
            .join(User, Album.user_id == User.id)
            .filter(
                or_(
                    Album.name.like(f'%{name}%'),
                    Album.singer.like(f'%{name}%'), 
                    Album.genre.like(f'%{name}%'),
                )
            )
            .all()
        )
        if g.user.role == 'admin':
            
            return render_template('adminsearch.html', songs=songs, albums=albums)

        # Search recently played songs
        recentlyplayed = RecentlyPlayedSongs.query.filter_by(user_id=session['id']).order_by(RecentlyPlayedSongs.timestamp.desc()).all()
        return render_template('search.html', songs=songs, albums=albums, user=user, name=name, recentlyplayed=recentlyplayed)

    return redirect(url_for('index'))


# album songs========================================================================================================

@app.route('/addsongtoalbum/<int:id>', methods=['GET', 'POST'])
def addsongtoalbum(id):
    if g.user and session['role'] == 'creator':
        if request.method == 'POST':
            name = request.form['name']
            audio_file = request.files['song'].read()
            image = request.files['image'].read()
            lyrics = request.form['lyrics']
            date = request.form['date_created']
            singer = request.form['singer']
            album_id = request
            user_id = session['id']
            song = Song(name, user_id, audio_file, image, date, lyrics, singer, album_id )
            song.audio_file = audio_file
            song.image = image
            db.session.add(song)
            db.session.commit()
            return redirect(url_for('creatorDashboard'))
        return render_template('addsong.html', album_id=id)
    return redirect(url_for('index'))

#  route for adding a song to a playlist
@app.route('/addsongtoplaylist/<int:id>', methods=['POST'])
def addsongtoplaylist(id):
    if g.user:
        if request.method == 'POST':
            playlist_id = id
            song_id = request.json['song_id']
            song = Song.query.get(song_id)
            playlist = Playlist.query.get(playlist_id)
            if song not in playlist.songs:
                playlist.songs.append(song)
                db.session.commit()
                return jsonify({'status': "song added successfully"}), 200
            else:
                return jsonify({'status': "song already exist in the playlist"}), 201
            



# New route for creating a playlist and adding a song to it
@app.route('/createplaylistandsong/<int:id>', methods=['POST'])
def createplaylistandsong(id):
    if g.user:
        if request.method == 'POST':
            name = request.json['name']  # Assuming the data is sent as JSON
            user_id = session['id']
            new_playlist = Playlist(name=name, user_id=user_id)
            db.session.add(new_playlist)
            db.session.commit()
            playlist_id = new_playlist.id
            song_id = id
            song = Song.query.get(song_id)
            playlist = Playlist.query.get(playlist_id)
            playlist.songs.append(song)
            db.session.commit()
            return jsonify({'status': name +" Playlist created Succesfully" }), 200
    return redirect(url_for('index', alert='something went wrong.'))

# view playlist
@app.route('/viewplaylist/<int:id>')
def viewplaylist(id):
    if g.user:
        playlist = Playlist.query.get(id)
        return render_template('playlist.html', playlist=playlist, songs=playlist.songs, playlist_id=id)
    return redirect(url_for('index', alert='something went wrong.')), 401



# view all playlist
@app.route('/myplaylist')
def viewallplaylist():
    recentlyplayed = RecentlyPlayedSongs.query.filter_by(user_id=session['id']).order_by(RecentlyPlayedSongs.timestamp.desc()).all()
    if g.user:
        playlists = Playlist.query.filter_by(user_id=session['id']).all()
        return render_template('myplaylist.html', playlists=playlists, recentlyplayed=recentlyplayed)
    return f'error, there\'s some error related to login.', 401


# delete song from playlist
@app.route('/deletesongfromplaylist/<int:playlist_id>/<int:song_id>')
def deletesongfromplaylist(playlist_id, song_id):
    if g.user:
        playlist = Playlist.query.get(playlist_id)
        song = Song.query.get(song_id)
        playlist.songs.remove(song)
        db.session.commit()
        return redirect(url_for('viewplaylist', id=playlist_id, alert='Song deleted successfully.'))
    return f'error, there\'s some error related to login.', 401


# delete playlist
@app.route('/deleteplaylist/<int:id>')
def deleteplaylist(id):
    if g.user:
        playlist = Playlist.query.get(id)
        db.session.delete(playlist)
        db.session.commit()
        return redirect(url_for('viewallplaylist', alert='Playlist deleted successfully.'))
    return render_template('myplaylist.html', alert='error deleting playlist'), 401



# create playlist
@app.route('/createplaylist', methods=['GET', 'POST'])
def createplaylist():
    if g.user:
        if request.method == 'POST':
            name = request.form['name']
            user_id = session['id']
            new_playlist = Playlist(name=name, user_id=user_id)
            db.session.add(new_playlist)
            db.session.commit()
            return redirect(url_for('viewplaylist', id=new_playlist.id))
        return render_template('createplaylist.html')
    return redirect(url_for('login'))





@app.route('/addrating/<int:id>', methods=['GET', 'POST'])
def addrating(id):
    if g.user:
        if request.method == 'POST':
            new_rating_value = request.form['rating']
            user_id = session['id']
            song_id = id
            existing_rating = SongRating.query.filter_by(user_id=user_id, song_id=song_id).first()
            if existing_rating:
                existing_rating.rating = new_rating_value
                db.session.commit()
                return 'Rating updated successfully', 200
            else:
                new_rating = SongRating(rating=new_rating_value, user_id=user_id, song_id=song_id)
                db.session.add(new_rating)
                db.session.commit()
                return 'Rating added successfully', 201
        return 'Error', 401

# user profile
@app.route('/profile')
def profile():
    if g.user:
        user = User.query.get(session['id'])
        if request.method == 'POST':
            user.name = request.form['name']
            user.email = request.form['email']
            user.password = request.form['password']
            db.session.commit()
            return redirect(url_for('profile'))
        return render_template('profile.html', user=user)
    return redirect(url_for('login'))



# blacklist a creator
@app.route('/blacklist/<int:id>')
def blacklist(id):
    if g.user and session['role'] == 'admin':
        user = User.query.get(id)
        user.blacklist_user()
        return render_template('adminDashboard.html', alert='Creator blacklisted successfully.')
    return redirect(url_for('adminlogin'))

# whitelist a creator
@app.route('/whitelist/<int:id>')
def whitelist(id):
    if g.user and session['role'] == 'admin':
        user = User.query.get(id)
        user.unblacklist_user()
        return render_template('adminDashboard.html', alert='Creator whitelisted successfully.')
    return redirect(url_for('adminlogin'))