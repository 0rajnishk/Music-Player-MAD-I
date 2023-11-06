import base64
from flask import g, render_template, request, redirect, url_for, session, flash
from application import app
from application.models import  User, Album, Song
from application.database import db

app.secret_key = 'development key'  



def convert_to_base64(image_data):
    return base64.b64encode(image_data).decode('utf-8')

@app.before_request
def load_user():
    g.user = None
    if 'id' in session:
        g.user = User.query.get(session['id'])


def addadmin():
    if User.query.filter_by(role='admin').first():
        return
    user1 = User('a@gmail.com', '1', 'admin1', 'chennai', 'admin')
    user2 = User('creator@c.com', '1', 'creator1', 'chennai', 'creator')
    db.session.add(user1, user2)
    db.session.commit()


@app.route('/')
def index():
    try:
        albums = Album.query.all()
        print(albums, 'albums')
        songs = Song.query.all()
        for song in songs:
            song.image = base64.b64encode(song.image).decode('utf-8')
        if g.user:
            if g.user.role == 'admin':
                return redirect(url_for('adminDashboard'))
            elif g.user.role == 'creator':
                return redirect(url_for('creatorDashboard'))
            else:
                return render_template('index.html', songs=songs, user=session['name'], albums=albums) 
        return render_template('login.html')
    except Exception as e:
        print(e, 'error')
        
    

    


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        print(email, '\n'*10)
        password = request.form['password']
        name = request.form['name']
        city = request.form['city']
        role = "user"
        user = User(email, password, name, city, role)
        db.session.add(user)
        db.session.commit()
        flash('You were successfully registered', 'success')
        return render_template('index.html')
    else:
        return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, role='user').first()
        if user and user.password == password:
            session['id'] = user.id
            session['email'] = user.email
            session['name'] = user.name
            session['city'] = user.city
            session['role'] = user.role
            flash('You were successfully logged in', 'success')
            return redirect(url_for('index'))
        else:
            return render_template('index.html', error='Invalid username or password')
    else:
        return render_template('login.html')


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
            session['city'] = user.city
            session['role'] = user.role
            return redirect(url_for('adminDashboard'))
        else:
            return render_template('adminlogin.html', error='Invalid username or password')

    return render_template('adminlogin.html')


@app.route('/adminDashboard', methods=['GET', 'POST'])
def adminDashboard():
    if g.user:
        if g.user.role == 'admin':
            return render_template('adminDashboard.html', albums=viewalbums())
        else:
            return redirect(url_for('logout'))
    return redirect(url_for('adminlogin'))

@app.route('/creator', methods=['GET', 'POST'])
def creatorDashboard():
    if request.args.get('H'):
        user = User.query.get(session['id'])
        user.role = 'creator'
        db.session.commit()
        session['role'] = 'creator'
        return redirect(url_for('creatorDashboard'))
    elif g.user:
        if g.user.role == 'creator':
            return render_template('creatorDashboard.html', albums=viewalbums(), creator=True)
        elif g.user.role == 'user':
            return render_template('creatorDashboard.html', creator = False)
        elif g.user.role == 'admin':
            return render_template('adminDashboard.html', albums=viewalbums())
    return redirect(url_for('index'))

@app.route('/addalbum', methods=['GET', 'POST'])
def addalbum():
    user = User.query.get(session['id'])
    if g.user and user.role == 'creator':
        if request.method == 'POST':
            name = request.form['name']
            genre = request.form['genre']
            artist_id = session['id']

            # Create an instance of the Album model
            new_album = Album(name=name, genre=genre, artist_id=artist_id)

            # Add the instance to the db.session and commit the changes
            db.session.add(new_album)
            db.session.commit()
            return redirect(url_for('creatorDashboard'))
        return render_template('addalbum.html')
    return redirect(url_for('adminlogin'))


@app.route('/editalbum/<int:id>', methods=['GET', 'POST'])
def editcategory(id):
    if g.user and session['role'] == 'admin':
        album = Album.query.get(id)
        if request.method == 'POST':
            album.name = request.form['name']
            db.session.commit()
            return redirect(url_for('adminDashboard'))
        return render_template('editalbum.html', album=album)
    return redirect(url_for('adminlogin'))


@app.route('/deletealbum/<int:id>', methods=['GET', 'POST'])
def deletecategory(id):
    if g.user and session['role'] == 'admin':
        artist = Album.query.get(id)
        db.session.delete(artist)
        songs = Song.query.filter_by(artist_id=id).all()
        for song in songs:
            db.session.delete(song)
        db.session.commit()
        return redirect(url_for('adminDashboard'))
    return redirect(url_for('adminlogin'))


@app.route('/viewalbums')
def viewalbums():
    return Album.query.all()


@app.route('/addsong', methods=['GET', 'POST'])
def addsong(id):
    if g.user and session['role'] == 'admin':
        artist = Album.query.get(id)
        
        if request.method == 'POST':
            name = request.form['name']
            genre = request.form['genre']
            image = request.files['image'].read()
            lyrics = request.form['lyrics']
            duration = request.form['duration']
            date_created = request.form['date_created']
            
            song = Song(name, image, duration, date_created,lyrics, artist.id, genre )
            song.image = image
            db.session.add(song)
            db.session.commit()
            return redirect(url_for('adminDashboard'))
        return render_template('addsong.html', artist=artist)
    return redirect(url_for('adminlogin'))


@app.route('/editsong/<int:id>', methods=['GET', 'POST'])
def editproduct(id):
    if g.user and session['role'] == 'admin':
        song = Song.query.get(id)
        if request.method == 'POST':
            song.name = request.form['name']
            song.manufacture = request.form['mnf-date']
            song.expirydate = request.form['exp-date']
            song.rateperunit = request.form['price']
            song.quantity = request.form['quantity']
            song.totalprice = int(song.rateperunit)*int(song.quantity)
            song.unit = request.form['unit']
            db.session.commit()
            return redirect('/viewsong/{}'.format(song.category_id))
        return render_template('editproduct.html', song=song)
    return redirect(url_for('adminlogin'))


@app.route('/deletesong/<int:id>', methods=['GET', 'POST'])
def deleteproduct(id):
    if g.user and session['role'] == 'admin':
        song = Song.query.get(id)
        db.session.delete(song)
        artist = Album.query.get(song.category_id)
        artist.quantity = int(artist.quantity)-1
        db.session.commit()
        return redirect('/viewsong/{}'.format(song.category_id))
    return redirect(url_for('adminlogin'))


@app.route('/viewsong/<int:id>')
def viewsong(id):
    songs = Song.query.filter_by(artist_id=id).all()
    print(songs)
    return render_template('viewsong.html', songs=songs)


@app.route('/logout')
def logout():
    session.pop('id', None)
    session.pop('email', None)
    session.pop('name', None)
    session.pop('city', None)
    session.pop('role', None)
    return redirect(url_for('index'))



#Search

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        name = request.form['search']
        songs = Song.query.filter(Song.name.like('%'+name+'%')).all()
        return render_template('search.html', songs=songs)
    return redirect(url_for('index'))
# getproduct by id

@app.route('/getproduct/<int:id>')
def getproduct(id):
    songs = Song.query.get(id)
    return render_template('product.html', songs=songs)