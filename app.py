from flask import Flask, render_template, request, redirect, url_for,session, flash, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_admin import auth as firebase_auth
import secrets
from flask_mail import Mail, Message
import requests


app = Flask(__name__)
cred = credentials.Certificate("foodpro-e0c85-firebase-adminsdk-i61j7-68edee59ff.json")
firebase_admin.initialize_app(cred)
app.secret_key = secrets.token_hex(16)

db = firestore.client()
food_posts = db.collection('food_posts')
food_providers = db.collection('food_providers')
ngos = db.collection('ngos')


app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'wetrio222@gmail.com'
app.config['MAIL_PASSWORD'] = 'jjbglfkopsfwpnlu'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
def get_address(lat, lng):
    api_key = '40a06180d30b4c219c3f0eddde964903'
    url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lng}&key={api_key}"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        if len(data['results']) > 0:
            return data['results'][0]['formatted']
    return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        try:
            user = auth.create_user(email=email, password=password)
            uid = user.uid
            user_data = {'email': email,'name' : username}
            
            if user_type == 'food_provider':
                food_providers.document(uid).set(user_data)
            elif user_type == 'ngo':
                ngos.document(uid).set(user_data)
                
            return redirect('/login')
        
        except:
            return 'There was an error creating your account'
        
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        session['email'] = email
        session['username'] = username
        try:
            user = firebase_auth.get_user_by_email(email)
            uid = user.uid
            user_type = request.form['user_type']
            
            if user_type == 'food_provider' and food_providers.document(uid).get().exists:
                return redirect('/post_food')
            elif user_type == 'ngo' and ngos.document(uid).get().exists:
                return redirect('/food_post')
            else:
                return 'Invalid user type'
            
        except firebase_auth.AuthError as e:
            return 'Invalid login credentials: ' + str(e)
        
    return render_template('login.html')



@app.route('/community')
def community():
    # Retrieve all food posts from Firestore
    db = firestore.client()
    posts_ref = db.collection('food_posts')
    posts = posts_ref.get()

    # Calculate total meals served
    total_meals_served = 0
    for post in posts:
        total_meals_served += post.to_dict()['quantity']

    # Add markers to map
    markers = []
    for post in posts:
        post_dict = post.to_dict()
        location = post_dict['location']
        lat, lon = location.latitude, location.longitude
        marker = {
            'lat': lat,
            'lon': lon,
            'title': post_dict['food'],
            'description': post_dict['description'],
        }
        markers.append(marker)

    # Render page with map and total meals served
    return render_template('community.html', markers=markers, total_meals_served=total_meals_served)


@app.route('/post_food', methods=['GET', 'POST'])
def post_food():
    email = session['email']
    food_posts = db.collection('food_posts')

    if request.method == 'POST':
        lat = float(request.form.get('lat'))
        lng = float(request.form.get('lng'))
        food_name = request.form.get('food_name')
        food_description = request.form.get('food_description')
        quantity = int(request.form['quantity'])

        food_post = {
            'food': food_name,
            'description': food_description,
            'quantity': quantity,
            'location': firestore.GeoPoint(lat, lng),
            'claimed_by': '',
            'claimed_email': '',
            'email': email,
            'claimed': False
        }

        food_posts.add(food_post)

        flash('Food posted successfully!')

    my_posts = food_posts.where('email', '==', email).get()
    return render_template('post_food.html', email=email, my_posts=my_posts, get_address=get_address)




@app.route('/food_post')
def food_post():
    # Retrieve all food posts from Firebase
    db = firestore.client()
    food_posts = db.collection('food_posts').get()

    # Filter food posts claimed by the logged in NGO
    claimed_posts = []
    email = session['email']
    for post in food_posts:
        if post.to_dict()['claimed_email'] == email:
            claimed_posts.append(post)

    # Filter unclaimed food posts
    unclaimed_posts = []
    for post in food_posts:
        if not post.to_dict()['claimed']:
            unclaimed_posts.append(post)

    # Render template with food posts
    return render_template('food_post.html', unclaimed_posts=unclaimed_posts, claimed_posts=claimed_posts,get_address=get_address)

@app.route('/claim_food/<post_id>', methods=['POST'])
def claim_food(post_id):
    # Retrieve the food post from Firebase
    db = firestore.client()
    post_ref = db.collection('food_posts').document(post_id)
    post = post_ref.get().to_dict()

    # Send email to food donor
    email_text = f"Hello,\n\nAn NGO has claimed your food post for {post['food']}. " \
                 f"Please contact them at {session['email']} to arrange for pickup/delivery.\n\n" \
                 f"Thank you for your generosity!\n\nFood Donation Platform"
    message = Message(subject="Your food post has been claimed!", sender='wetrio222@gmail.com', body=email_text, recipients=[post['email']])
    mail.send(message)
    
    # Update food post with NGO information
    post_ref.update({
        'claimed': True,
        'claimed_by': session['username'],
        'claimed_email': session['email']
    })
    flash('Food claimed successfully!')
    
    # Redirect to the food post page
    return redirect('/food_post')




@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('username', None)
    return render_template('home.html')

@app.route ('/about')
def about():
    return render_template('about.html')



if __name__ == '__main__':
    app.run(debug=True)

