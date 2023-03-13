from flask import Flask, render_template, request, redirect, url_for,session
import firebase_admin
from firebase_admin import credentials, firestore, auth
import geopy.distance
from geopy.distance import distance
from firebase_admin import auth as firebase_auth
import secrets
from flask_mail import Mail, Message

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


@app.route('/post_food', methods=['GET', 'POST'])
def post_food():
    # session_cookie = request.cookies.get('session')
    # decoded_claims = firebase_auth.verify_session_cookie(session_cookie, check_revoked=True)
    # uid = decoded_claims['uid']
    # email = decoded_claims['email']
    
    email = session['email']
    if request.method == 'POST':
        # get the user's current location from the browser's geolocation API
        lat = float(request.form.get('lat'))
        lng = float(request.form.get('lng'))
        
        # get the other form data
        food_name = request.form.get('food_name')
        food_description = request.form.get('food_description')
        quantity = int(request.form['quantity'])
        
        # get the email of the logged-in user
        # email = firebase_auth.current_user().email
        
        # create the food post dictionary
        food_post = {
            'food': food_name,
            'description': food_description,
            'quantity': quantity,
            'location': firestore.GeoPoint(lat, lng),
            'claimed_by': '',
            'email': email
        }
        
        # store the food post in the Firebase Firestore database
        food_posts.add(food_post)
        
        return 'Food posted successfully!'
    else:
        return render_template('post_food.html')


@app.route('/food_post')
def food_post():
    # Retrieve all food posts from Firebase
    db = firestore.client()
    food_posts = db.collection('food_posts').get()

    # Render template with food posts
    return render_template('food_post.html', food_posts=food_posts)


@app.route('/claim_food/<post_id>', methods=['POST'])
def claim_food(post_id):
    # Retrieve the food post from Firebase
    db = firestore.client()
    post_ref = db.collection('food_posts').document(post_id)
    post = post_ref.get().to_dict()
    print(post['email'])
    ybhav = str(session['email'])
    recieveq = [post['email']]
    claim_user = session['username']
    # food_posts = db.collection('food_posts').get()
    # Send email to food donor
    email_text = f"Hello,\n\nAn NGO has claimed your food post for {post['food']}. " \
             f"Please contact them at {ybhav} to arrange for pickup/delivery.\n\n" \
             f"Thank you for your generosity!\n\nFood Donation Platform"
    print(email_text)
    message = Message(subject="Your food post has been claimed!", sender='wetrio222@gmail.com', body=email_text, recipients=recieveq)
    mail.send(message)
    
    # Update food post with NGO information
    post_ref.update({
        'claimed': True,
        'claimed_by': claim_user,
        'claimed_email': session['email']
    })

    # Redirect to the food post page
    return redirect(url_for('food_post'))

@app.route('/logout')
def logout():
    session.pop('email', None)
    return render_template('home.html')



if __name__ == '__main__':
    app.run(debug=True)

