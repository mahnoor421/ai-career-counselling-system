"""
AI Career Counselor - Flask Application
Version: 3.0
"""

import os
import json
import logging
from datetime import datetime
from functools import wraps
from urllib.parse import unquote

from flask import (
    Flask, render_template, request, redirect, 
    url_for, session, send_file, jsonify, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from chatbot import get_bot_response
from career_engine import recommend_careers


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_career_database():
    """Load all career JSON files from data folder."""
    career_database = {}
    data_folder = "data"
    
    career_files = [
        "computer_science.json",
        "medical.json",
        "engineering.json",
        "business.json",
        "sciences.json",
        "social_sciences.json",
        "arts_and_design.json",
        "other_professional_fields.json"
    ]
    
    for file in career_files:
        try:
            path = os.path.join(data_folder, file)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    career_database.update(data)
                    logger.info(f"Loaded {file}: {len(data)} careers")
            else:
                logger.warning(f"File not found: {file}")
        except Exception as e:
            logger.error(f"Error loading {file}: {str(e)}")
    
    logger.info(f"Total careers loaded: {len(career_database)}")
    return career_database


CAREER_DATABASE = load_career_database()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ai-career-counselor-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///ai_career_counselor.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    """User model for authentication."""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    career_histories = db.relationship(
        'CareerHistory',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Hash and set password."""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if password matches hash."""
        return bcrypt.check_password_hash(self.password, password)


class CareerHistory(db.Model):
    """Career prediction history model."""
    __tablename__ = 'career_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    career = db.Column(db.String(150), nullable=False)
    education = db.Column(db.String(100))
    skills = db.Column(db.Text)
    interests = db.Column(db.Text)
    match_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<CareerHistory {self.career}>'


with app.app_context():
    db.create_all()
    logger.info("Database tables created/verified")


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current logged-in user."""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


@app.route('/')
def home():
    """Home page."""
    try:
        user = get_current_user()
        total_careers = len(CAREER_DATABASE)
        return render_template('index.html', user=user, total_careers=total_careers)
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        return render_template('500.html'), 500


@app.route('/about')
def about():
    """About page."""
    try:
        return render_template('about.html')
    except Exception as e:
        logger.error(f"Error in about route: {str(e)}")
        return render_template('500.html'), 500


@app.route('/careers')
def careers():
    """Browse all careers."""
    try:
        search_query = request.args.get('search', '').lower()
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        careers_list = []
        for career_name, details in CAREER_DATABASE.items():
            if not search_query or search_query in career_name.lower():
                careers_list.append({
                    'name': career_name,
                    'description': details.get('description', 'No description'),
                    'skills': details.get('skills', [])[:3]
                })
        
        start = (page - 1) * per_page
        end = start + per_page
        paginated_careers = careers_list[start:end]
        total_pages = (len(careers_list) + per_page - 1) // per_page
        
        return render_template(
            'careers.html',
            careers=paginated_careers,
            search_query=search_query,
            total_careers=len(CAREER_DATABASE),
            current_page=page,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Error in careers route: {str(e)}")
        return render_template('500.html'), 500


@app.route('/career')
def career_detail():
    """Detailed career information - using query parameter."""
    try:
        career_name = request.args.get('name', '').strip()
        
        if not career_name:
            logger.warning("No career name provided in query parameter")
            flash('Please select a career.', 'danger')
            return redirect(url_for('careers'))
        
        logger.info(f"Looking for career: '{career_name}'")
        logger.info(f"Total careers in database: {len(CAREER_DATABASE)}")
        
        career = None
        
        if career_name in CAREER_DATABASE:
            career = CAREER_DATABASE[career_name].copy()
            career['name'] = career_name
            logger.info(f"Found career (exact match): {career_name}")
        
        if not career:
            for db_career_name, db_details in CAREER_DATABASE.items():
                if db_career_name.lower() == career_name.lower():
                    career = db_details.copy()
                    career['name'] = db_career_name
                    logger.info(f"Found career (case-insensitive): {db_career_name}")
                    break
        
        if not career:
            logger.warning(f"Career not found: '{career_name}'")
            flash(f'Career "{career_name}" not found.', 'danger')
            return redirect(url_for('careers'))
        
        logger.info(f"Successfully loaded career: {career.get('name')}")
        return render_template('career_detail.html', career=career)
    
    except Exception as e:
        logger.error(f"Error in career_detail route: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        flash('Error loading career details. Please try again.', 'danger')
        return redirect(url_for('careers'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup."""
    try:
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not name or not email or not password:
                flash('All fields are required.', 'danger')
                return redirect(url_for('signup'))
            
            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return redirect(url_for('signup'))
            
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('signup'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered!', 'warning')
                return redirect(url_for('login'))
            
            new_user = User(name=name, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            logger.info(f"New user registered: {email}")
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('signup.html')
    
    except Exception as e:
        logger.error(f"Error in signup route: {str(e)}")
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('signup'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    try:
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email and password are required.', 'danger')
                return redirect(url_for('login'))
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_email'] = user.email
                
                logger.info(f"User logged in: {email}")
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(url_for('dashboard'))
            
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
        
        return render_template('login.html')
    
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """User logout."""
    try:
        session.clear()
        logger.info("User logged out")
        flash('You have been logged out.', 'info')
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}")
        return redirect(url_for('home'))


@app.route('/chatbot')
def chatbot():
    """Chatbot interface."""
    try:
        user = get_current_user()
        chat_history = session.get('chat_history', [])
        return render_template('chatbot.html', user=user, chat_history=chat_history)
    except Exception as e:
        logger.error(f"Error in chatbot route: {str(e)}")
        return render_template('500.html'), 500


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chatbot messages."""
    try:
        message = request.form.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Please type a message'}), 400
        
        response = get_bot_response(message, session)
        
        chat_history = session.get('chat_history', [])
        chat_history.append({
            'user': message,
            'bot': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        session['chat_history'] = chat_history
        
        logger.info(f"Chat message processed: {message[:50]}")
        return jsonify({'response': response}), 200
    
    except Exception as e:
        logger.error(f"Error in chat route: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/clear_chat')
def clear_chat():
    """Clear chat history."""
    try:
        session.pop('chat_history', None)
        session.pop('career_chat', None)
        flash('Chat cleared.', 'info')
        return redirect(url_for('chatbot'))
    except Exception as e:
        logger.error(f"Error in clear_chat route: {str(e)}")
        return redirect(url_for('chatbot'))


@app.route('/predict', methods=['POST', 'GET'])
def predict():
    """Generate career predictions."""
    try:
        if request.method == 'POST':
            education = request.form.get('education', '').strip()
            skills = request.form.get('skills', '').strip()
            interests = request.form.get('interests', '').strip()
            
            logger.info(f"Prediction request: Education={education}, Skills={skills}")
            
            if not education or not skills or not interests:
                flash('All fields are required.', 'danger')
                return redirect(url_for('home'))
            
            try:
                matches = recommend_careers(education, skills, interests, top_n=15)
            except Exception as e:
                logger.error(f"Error in recommend_careers: {str(e)}")
                flash('Error generating predictions. Please try again.', 'danger')
                return redirect(url_for('home'))
            
            if not matches:
                flash('No suitable careers found. Please try different inputs.', 'warning')
                return redirect(url_for('home'))
            
            top_careers = []
            for idx, item in enumerate(matches[:15], 1):
                if isinstance(item, tuple):
                    career_name = item[0]
                    score = item[1]
                else:
                    career_name = item.get('career') or item.get('name', '')
                    score = item.get('score') or item.get('match_percentage', 0)
                
                career_details = {}
                for db_name, db_details in CAREER_DATABASE.items():
                    if db_name.lower() == career_name.lower():
                        career_details = db_details
                        career_name = db_name
                        break
                
                top_careers.append({
                    'rank': idx,
                    'name': career_name,
                    'score': int(score) if score else 0,
                    'description': career_details.get('description', 'No description'),
                    'education': career_details.get('education', []),
                    'skills': career_details.get('skills', [])[:5],
                    'roadmap': career_details.get('roadmap', []),
                    'salary_range': career_details.get('salary_range', 'Not specified')
                })
            
            if 'user_id' in session:
                for career_item in top_careers[:5]:
                    try:
                        history = CareerHistory(
                            user_id=session['user_id'],
                            career=career_item['name'],
                            education=education,
                            skills=skills,
                            interests=interests,
                            match_score=career_item['score']
                        )
                        db.session.add(history)
                        db.session.commit()
                    except Exception as e:
                        logger.error(f"Error saving prediction: {str(e)}")
                        db.session.rollback()
            
            logger.info(f"Prediction generated: {len(top_careers)} careers matched")
            
            return render_template(
                'result.html',
                education=education,
                skills=skills,
                interests=interests,
                top_careers=top_careers
            )
        
        return render_template('predict.html')
    
    except Exception as e:
        logger.error(f"Error in predict route: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with prediction history."""
    try:
        user = get_current_user()
        
        history = CareerHistory.query.filter_by(
            user_id=user.id
        ).order_by(CareerHistory.created_at.desc()).all()
        
        total_predictions = len(history)
        unique_careers = len(set(h.career for h in history))
        average_score = round(sum(h.match_score for h in history) / len(history), 1) if history else 0
        
        latest_career = history[0].career if history else "No predictions yet"
        
        career_counts = {}
        for item in history:
            career_counts[item.career] = career_counts.get(item.career, 0) + 1
        
        chart_labels = list(career_counts.keys())[:10]
        chart_values = list(career_counts.values())[:10]
        
        logger.info(f"Dashboard loaded for user: {user.email}")
        
        return render_template(
            'dashboard.html',
            user=user,
            history=history,
            total_predictions=total_predictions,
            unique_careers=unique_careers,
            average_score=average_score,
            latest_career=latest_career,
            chart_labels=chart_labels,
            chart_values=chart_values
        )
    
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        return render_template('500.html'), 500


@app.route('/statistics')
def statistics():
    """Global statistics page."""
    try:

        total_users = User.query.count()

        total_predictions = CareerHistory.query.count()


        popular_careers = db.session.query(
            CareerHistory.career,
            db.func.count(CareerHistory.id).label('count')
        ).group_by(
            CareerHistory.career
        ).order_by(
            db.func.count(CareerHistory.id).desc()
        ).limit(10).all()


        logger.info("Statistics page loaded")


        return render_template(
            'statistics.html',
            total_users=total_users,
            total_predictions=total_predictions,
            total_careers=len(CAREER_DATABASE),
            careers=popular_careers
        )


    except Exception as e:

        logger.error(f"Error in statistics route: {str(e)}")

        return render_template('500.html'), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(error)}")
    return render_template('500.html'), 500


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    return render_template('403.html'), 403


@app.context_processor
def inject_user():
    """Inject user into all templates."""
    return {'current_user': get_current_user()}


if __name__ == '__main__':
    logger.info("="*70)
    logger.info("Starting AI Career Counselor Application")
    logger.info("="*70)
    logger.info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.info(f"Total Careers Loaded: {len(CAREER_DATABASE)}")
    logger.info("="*70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)