from application.database import db
from datetime import datetime

# Define the association table first
playlist_song = db.Table('playlist_song',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(128), default='user', nullable=False)
    blacklist = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, email, password, name, role):
        self.email = email
        self.password = password
        self.name = name
        self.role = role

    def blacklist_user(self):
        self.blacklist = True
        db.session.commit()
    def unblacklist_user(self):
        self.blacklist = False
        db.session.commit()

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    singer = db.Column(db.String(128))
    genre = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    songs = db.relationship('Song', backref='album', lazy=True)

    def __init__(self, name, singer, user_id, genre):
        self.name = name
        self.singer = singer
        self.user_id = user_id
        self.genre = genre

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    audio_file = db.Column(db.LargeBinary)  
    image = db.Column(db.LargeBinary)
    genre = db.Column(db.String(128))
    date = db.Column(db.String)
    lyrics = db.Column(db.String(10000), nullable=False)
    singer = db.Column(db.String(128), nullable=False)
    play_count = db.Column(db.Integer, default=0, nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), default=None)
    ratings = db.relationship('SongRating', backref='song', lazy=True)
    comments = db.relationship('Comment', backref='song', lazy=True)

    def __init__(self, name, user_id, audio_file, image, date, lyrics, singer, album_id, genre):
        self.name = name    
        self.user_id = user_id
        self.audio_file = audio_file  
        self.image = image
        self.date = date
        self.lyrics = lyrics
        self.singer = singer  
        self.album_id = album_id
        self.genere = genre
        
    def increment_play_count(self):
        self.play_count += 1
        db.session.commit()

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    songs = db.relationship('Song', secondary=playlist_song, backref='playlists', lazy='dynamic')

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id

class SongRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, song_id, rating):
        self.user_id = user_id
        self.song_id = song_id
        self.rating = rating

# comments
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'),nullable=False)
    comment = db.Column(db.String(10000), nullable=False)

    def __init__(self, user_id, song_id, comment):
        self.user_id = user_id
        self.song_id = song_id
        self.comment = comment

# recently played songs
class RecentlyPlayedSongs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, song_id, user_id):
        self.song_id = song_id
        self.user_id = user_id