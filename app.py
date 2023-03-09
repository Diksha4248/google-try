from flask import Flask, render_template, request, redirect
import firebase_admin
from firebase_admin import credentials, firestore, auth
import geopy.distance
from geopy.distance import distance
from firebase_admin import auth as firebase_auth


app = Flask(__name__)
cred = credentials.Certificate("foodpro-e0c85-firebase-adminsdk-i61j7-68edee59ff.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
food_posts = db.collection('food_posts')
food_providers = db.collection('food_providers')
ngos = db.collection('ngos')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        try:
            user = auth.create_user(email=email, password=password)
            uid = user.uid
            user_data = {'email': email}
            
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
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = firebase_auth.get_user_by_email(email)
            uid = user.uid
            user_type = request.form['user_type']
            
            if user_type == 'food_provider' and food_providers.document(uid).get().exists:
                return redirect('/post_food')
            elif user_type == 'ngo' and ngos.document(uid).get().exists:
                return redirect('/find_food')
            else:
                return 'Invalid user type'
            
        except firebase_auth.AuthError as e:
            return 'Invalid login credentials: ' + str(e)
        
    return render_template('login.html')

# @app.route('/post_food', methods=['GET', 'POST'])
# def post_food():
#     if request.method == 'POST':
#         food = request.form['food']
#         quantity = request.form['quantity']
#         latitude = request.form['latitude']
#         longitude = request.form['longitude']
        
#         food_post = {'food': food, 'quantity': quantity, 'location': firestore.GeoPoint(latitude, longitude), 'claimed_by': ''}
#         food_posts.add(food_post)
        
#         return redirect('/')
    
#     return render_template('post_food.html')

@app.route('/post_food', methods=['GET', 'POST'])
def post_food():
    if request.method == 'POST':
        # get the user's current location from the browser's geolocation API
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        
        # get the other form data
        food_name = request.form.get('food_name')
        food_description = request.form.get('food_description')
        pickup_address = request.form.get('pickup_address')
        pickup_time = request.form.get('pickup_time')
        
        
        
        return 'Food posted successfully!'
    else:
        return render_template('post_food.html')



@app.route('/find_food', methods=['GET', 'POST'])
def find_food():
    if request.method == 'POST':
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        radius = request.form['radius']
        quantity = request.form['quantity']
        
        center = firestore.GeoPoint(latitude, longitude)
        filtered_posts = []
        for post in food_posts.stream():
            post_dict = post.to_dict()
            if post_dict['claimed_by'] == '':
                post_location = post_dict['location']
                post_quantity = post_dict['quantity']
                distance = geopy.distance.distance((latitude, longitude), (post_location.latitude, post_location.longitude)).km
                if distance <= float(radius) and post_quantity >= int(quantity):
                    post_dict['id'] = post.id
                    filtered_posts.append(post_dict)
        
        return render_template('find_food.html', posts=filtered_posts)
    
    return render_template('find_food.html')

@app.route('/claim_food/<post_id>')
def claim_food(post_id):
    try:
        post_ref = food_posts.document(post_id)
        post = post_ref.get().to_dict()
        claimed_by = post.get('claimed_by', None)
        
        if claimed_by is None:
            user = auth.current_user
            uid = user.uid
            post_ref.update({'claimed_by': uid})
            return redirect('/')
        else:
            return 'This post has already been claimed'
    
    except:
        return 'There was an error claiming this post'


if __name__ == '__main__':
    app.run(debug=True)

