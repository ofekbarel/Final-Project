from flask import Flask, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/users'
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login if unauthorized

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    recipes = db.relationship('PrivetRecipe')

    def __init__(self, email, password, name):

        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class PrivetRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, description, user_id):
        self.title = title
        self.description = description
        self.user_id = user_id


class PublicRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), unique=True)


    def __init__(self, title, description):
        self.title = title
        self.description = description


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))  # Use url_for for better routing

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))  # Use url_for
        else:
            return render_template('login.html', error='Invalid user')

    return render_template('login.html')


@app.route('/dashboard')
@login_required  # Protect this route with login requirement
def dashboard():
    if current_user.is_authenticated:
        return render_template('dashboard.html', user=current_user)
    else:
        return redirect(url_for('login'))  # Redirect to login if not logged in


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))




@app.route('/all_recipes')
def all_recipes():
    user_recipes = PublicRecipe.query.all()
    return render_template('all_recipes2.html', user_recipes=user_recipes)



@app.route('/add_public_recipe', methods=['GET', 'POST'])
@login_required  # Only logged in users can access this route
def add_public_recipe():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        new_recipe = PublicRecipe(title=title, description=description)
        db.session.add(new_recipe)
        db.session.commit()

        return redirect(url_for('dashboard'))
    return render_template('add_public_recipe.html')


@app.route('/add_privet_recipe', methods=['GET', 'POST'])
@login_required  # Only logged in users can access this route
def add_privet_recipe():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        new_recipe = PrivetRecipe(title=title, description=description, user_id=current_user.id)
        db.session.add(new_recipe)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('add_privet_recipe.html')


@app.route('/my_recipes')
@login_required  # Only logged in users can access this route
def my_recipes():
    if current_user.is_authenticated:
        user_recipes = PrivetRecipe.query.filter_by(user_id=current_user.id).all()
        return render_template('my_recipes.html', user_recipes=user_recipes)
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
