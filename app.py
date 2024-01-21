from flask import (
    Flask, render_template, redirect, url_for , request, flash, jsonify, session, abort, send_from_directory
)
from google.oauth2 import id_token
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import Category, Review, User, db, Recipe, Rating
from fuzzywuzzy import process
from config import app_config
from secrets import token_hex
import random
from datetime import datetime
import os
import pathlib
import google.auth.transport.requests
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_migrate import Migrate
from oauthlib.oauth2 import WebApplicationClient
from requests.exceptions import RequestException
import json
import requests
from secrets import token_hex
from werkzeug.exceptions import HTTPException
from werkzeug.utils import redirect
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol

# Ensure that 'models' module is imported correctly
from models import db
os.environ['FLASK_APP'] = 'app.py'
app = Flask(__name__)
app.config.from_object(app_config)
app.secret_key = os.urandom(16).hex()
migrate = Migrate(app, db)
db.init_app(app)

# Configure the Google OAuth 2.0 API
GOOGLE_CLIENT_ID = '330670515807-hlkl2mnit8pcg0g3o8ujlfpqv8kks2k2.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client.json")

# new config
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # to allow Http traffic for local dev
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["email", "profile" , ''],
    redirect_uri="http://localhost:5000/callback"
)

# Define the global variable for Google provider configuration
google_provider_cfg = None

# Load Google provider configuration during app initialization
try:
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
except (RequestException, json.JSONDecodeError, Exception) as e:
    print(f"Error loading Google provider configuration: {str(e)}")

# Create the login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/callback")
def callback():
    try:
        # Fetch token from the authorization response
        flow.fetch_token(authorization_response=request.url)

        # Check if the state parameter matches
        if session.get("state") != request.args.get("state"):
            abort(500)  # State does not match!

        # Get user information from the ID token
        credentials = flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID
        )

        # Store user information in the session or database as needed
        session["google_id"] = id_info.get("sub")
        session["name"] = id_info.get("name")

        # Redirect to the main page or wherever you want
        return redirect(url_for("index"))

    except Exception as e:
        print(f"Callback error: {str(e)}")
        abort(500)  # Handle other errors gracefully

# ... (rest of your code)
# Create the dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    return 'Welcome to the dashboard!'




@app.route('/')
#@login_required
def index():
    recipes = Recipe.query.all()
    return render_template('index.html', recipes=recipes)

@app.route('/recipe/add', methods=['GET', 'POST'])
def add_recipe():
    # Fetch all categories for the form
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form['name']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        nutrition_facts = request.form.get('nutrition_facts', '')
        category_id = request.form.get('category', None)

        # Create a new recipe instance
        new_recipe = Recipe(
            name=name,
            ingredients=ingredients,
            instructions=instructions,
            nutrition_facts=nutrition_facts,
            category_id=category_id
        )

        # Add the new recipe to the database
        db.session.add(new_recipe)
        db.session.commit()

        # Redirect to the home page
        flash('Recipe added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_recipe.html', categories=categories)

@app.route('/recipe/edit/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    categories = Category.query.all()  # Fetch all categories

    if request.method == 'POST':
        recipe.name = request.form['name']
        recipe.ingredients = request.form['ingredients']
        recipe.instructions = request.form['instructions']
        recipe.nutrition_facts = request.form.get('nutrition_facts', '')
        recipe.category_id = request.form.get('category', None)  # Update category

        db.session.commit()

        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_recipe.html', recipe=recipe, categories=categories)  # Pass categories to the template

from flask import redirect, url_for

@app.route('/recipe/delete/<int:recipe_id>')
def delete_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    
    # Delete associated reviews
    reviews = Review.query.filter_by(recipe_id=recipe_id).all()
    for review in reviews:
        db.session.delete(review)

    # Delete associated ratings
    Rating.query.filter_by(recipe_id=recipe_id).delete()

    # Now delete the recipe
    db.session.delete(recipe)

    # Commit the changes
    db.session.commit()

    return redirect(url_for('index'))




@app.route('/suggest_recipe_page')
def suggest_recipe_page():
    return render_template('suggest_recipe.html')


@app.route('/suggest_recipe', methods=['POST'])
def suggest_recipe():
    if request.method == 'POST':
        user_ingredients = request.form.get('ingredients', '').split(',')
        all_recipes = Recipe.query.all()
        recipe_ingredients = [recipe.ingredients.split(',') for recipe in all_recipes]
        all_recipe_ingredients = [ingredient.strip().lower() for sublist in recipe_ingredients for ingredient in sublist]
        matches = [process.extractOne(user_ingredient.strip().lower(), all_recipe_ingredients) for user_ingredient in user_ingredients]
        matched_ingredients = [match[0] for match in matches if match[1] > 80]
        matched_recipes = Recipe.query.filter(Recipe.ingredients.ilike('%{}%'.format('%'.join(matched_ingredients)))).all()

        # Pass the detailed information of suggested recipes to the template
        return render_template('view_recipe.html', suggested_recipes=matched_recipes)

    return redirect(url_for('suggest_recipe_page'))

@app.route('/recipe/<int:recipe_id>')
def recipe_details(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return render_template('404.html'), 404

    return render_template('recipe_details.html', recipe=recipe)





@app.route('/categories')
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/category/<int:category_id>')
def category_recipes(category_id):
    category = Category.query.get(category_id)
    if not category:
        return render_template('404.html'), 404

    recipes = category.recipes
    return render_template('category_recipes.html', category=category, recipes=recipes)



@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        recipes = Recipe.query.filter(
            (Recipe.name.ilike(f"%{query}%")) | (Recipe.ingredients.ilike(f"%{query}%"))
        ).all()

        if not recipes:
            # No results found, redirect to 'no_results.html'
            return render_template('no_results.html', query=query)

        return render_template('search_results.html', query=query, recipes=recipes)

    return render_template('search.html')

# Utility function to calculate the average rating
def calculate_average_rating(ratings):
    total_ratings = sum(rating.value for rating in ratings)
    average_rating = total_ratings / len(ratings) if len(ratings) > 0 else 0
    return round(average_rating, 2)

# Route to rate a recipe
@app.route('/rate_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def rate_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)

    if not recipe:
        return render_template('404.html'), 404

    if request.method == 'POST':
        rating_value = int(request.form['rating'])

        if 1 <= rating_value <= 5:
            new_rating = Rating(value=rating_value, recipe_id=recipe_id)
            db.session.add(new_rating)
            db.session.commit()

            # Update the average rating for the recipe
            ratings = Rating.query.filter_by(recipe_id=recipe_id).all()
            recipe.rating = calculate_average_rating(ratings)
            db.session.commit()

            # Flash a success message
            flash('Rating has been saved successfully!', 'success')
            return jsonify({'success': True, 'message': 'Rating has been saved successfully!'})

    # Fetch all ratings for the recipe
    ratings = Rating.query.filter_by(recipe_id=recipe_id).all()

    # Calculate the average rating
    average_rating = calculate_average_rating(ratings)

    return render_template('rate_recipe.html', recipe=recipe, ratings=ratings, average_rating=average_rating)

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))



@app.route('/recipe_of_the_day')
def recipe_of_the_day():
    current_date = datetime.now().strftime('%Y-%m-%d')
    random.seed(current_date)
    all_recipes = Recipe.query.all()
    recipes = [recipe for recipe in all_recipes]
    random_recipe = random.choice(recipes)

    return render_template('recipe_of_the_day.html', recipe=random_recipe) 

@app.route('/search_nutrition', methods=['GET', 'POST'])
def search_nutrition():
    if request.method == 'POST':
        nutrition_query = request.form.get('nutrition_query', '')
        matched_recipes = Recipe.query.filter(Recipe.nutrition_facts.ilike('%{}%'.format(nutrition_query))).all()
        if not matched_recipes:
        
            return render_template('no_results.html', query=nutrition_query)
        
        return render_template('search_results.html', query=nutrition_query, recipes=matched_recipes)

    return render_template('search_nutrition.html')





@app.route('/recipe_list', methods=['GET'])
def recipe_list():
    recipes = Recipe.query.all()
    return render_template('recipe_list.html', recipes=recipes)

# Updated route for viewing reviews based on recipe ID
@app.route('/view_reviews/<int:recipe_id>', methods=['GET'])
def view_reviews(recipe_id):
    recipe = Recipe.query.get(recipe_id)

    if not recipe:
        return render_template('404.html'), 404

    reviews = Review.query.filter_by(recipe_id=recipe_id).all()

    return render_template('view_reviews.html', recipe=recipe, reviews=reviews)



@app.route('/choose_recipe', methods=['GET', 'POST'])
def choose_recipe():
    if request.method == 'POST':
        recipe_name = request.form.get('recipe_name')

        # Check if the recipe name exists
        if Recipe.query.filter_by(name=recipe_name).first():
            return redirect(url_for('add_review', recipe_name=recipe_name))
        else:
            flash(f"Recipe with the name '{recipe_name}' does not exist. Please enter a valid recipe name.")
            
    return render_template('input_recipe.html')

@app.route('/add_review/<string:recipe_name>', methods=['GET', 'POST'])
def add_review(recipe_name):
    # Query the recipe by name
    recipe = Recipe.query.filter_by(name=recipe_name).first()

    if not recipe:
        return render_template('404.html'), 404

    if request.method == 'POST':
        review_content = request.form.get('review_content')

        if review_content:
            new_review = Review(content=review_content, recipe_id=recipe.id)
            db.session.add(new_review)
            db.session.commit()

            # Redirect to the correct recipe page or any other appropriate page
            return redirect(url_for('view_reviews', recipe_id=recipe.id))

    return render_template('add_review.html', recipe_name=recipe_name)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
   app.run(host="localhost", port=5000, debug=True)
