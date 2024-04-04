from flask import Flask, render_template, request, jsonify, url_for
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips, ImageClip
import os
import requests
from io import BytesIO
from PIL import Image
import numpy as np

app = Flask(__name__)
app.secret_key = '42junky123'

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit for file size

# Database configuration
database_url = os.getenv('DATABASE_URL')
ssl_cert_path = 'root.crt'  # since root.crt is in the same directory as app.py

if database_url:
    if 'sslmode' not in database_url:
        database_url += f"?sslmode=verify-full&sslrootcert={ssl_cert_path}"
    database_url = database_url.replace('postgresql://', 'cockroachdb://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['JWT_SECRET_KEY'] = '69junkyplease'
jwt = JWTManager(app)

# Models
class UsersData(db.Model):
    __tablename__ = 'users_data'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    images = db.relationship('UserImage', backref='user', lazy=True)

class UserImage(db.Model):
    __tablename__ = 'user_images'
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(2048), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users_data.id'), nullable=False)

class AudioFile(db.Model):
    __tablename__ = 'audio_files'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    audio_url = db.Column(db.String(2048), nullable=False)


# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')

    user = UsersData.query.filter_by(username=username).first()
    if user:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400

    new_user = UsersData(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Signup successful'}), 201

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')

    user = UsersData.query.filter_by(username=username, password=password).first()
    if user:
        access_token = create_access_token(identity=username)
        return jsonify({'success': True, 'access_token': access_token}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_image():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        
        filename = secure_filename(file.filename)
        # Create the full path for the file to be saved
        save_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        image_url = url_for('static', filename=os.path.join('uploads', filename), _external=True)

        
        current_user = get_jwt_identity()
        user = UsersData.query.filter_by(username=current_user).first()
        new_image = UserImage(image_url=image_url, user=user)
        db.session.add(new_image)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'File uploaded', 'image_url': image_url}), 200

    return jsonify({'success': False, 'message': 'File type not allowed'}), 400

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/get_images', methods=['GET'])
@jwt_required()
def get_images():
    current_user = get_jwt_identity()
    user = UsersData.query.filter_by(username=current_user).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    images = UserImage.query.filter_by(user_id=user.id).all()
    image_urls = [image.image_url for image in images]  
    return jsonify({'success': True, 'images': image_urls})


def insert_audio_files():
    audio_filenames = ['Epic.mp3', 'Happy.mp3', 'Sad.mp3']
    base_url = 'http://127.0.0.1:5000/static/Audio/'  # Modify as per your server's URL

    for filename in audio_filenames:
        audio_url = base_url + filename
        existing_audio = AudioFile.query.filter_by(name=filename).first()
        
        if not existing_audio:
            new_audio = AudioFile(name=filename, audio_url=audio_url)
            db.session.add(new_audio)

    db.session.commit()


@app.route('/create_video', methods=['POST'])
@jwt_required()
def create_video_endpoint():
    data = request.get_json()
    image_urls = data['imageUrls']
    resolution = data['resolution']
    audio_mood = data['audioMood']

    # Fetch audio URL from the database based on audio_mood
    audio_file = AudioFile.query.filter_by(name=f'{audio_mood}.mp3').first()
    
    if not audio_file:
        return jsonify({'success': False, 'message': 'Audio file not found'}), 404

    width, height=parse_resolution(resolution)
    video_url = create_video(image_urls, width, height, audio_file.audio_url)
    return jsonify({'success': True, 'videoUrl': video_url})

def create_video(image_urls, width, height, audio_url, fps=24):
    # Duration each image is displayed
    image_display_duration = 3

    # Create a clip for each image
    clips = [ImageClip(download_image(url), duration=image_display_duration).set_fps(fps).resize(width=width, height=height) for url in image_urls]

    # Concatenate all the image clips
    video_clip = concatenate_videoclips(clips, method="compose")

    # Load the audio file and loop it if necessary
    audio_clip = AudioFileClip(audio_url)
    video_duration = image_display_duration * len(image_urls)

    # If the audio clip is shorter than the video duration, loop it
    if audio_clip.duration < video_duration:
        audio_clip = audio_clip.loop(duration=video_duration)

    # Set the audio of the concatenated clip
    video_clip = video_clip.set_audio(audio_clip.set_duration(video_duration))

    # Output file path
    output_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output_video.mp4')
    video_clip.write_videofile(output_file, codec='libx264', fps=fps)

    # Return the URL of the created video
    return url_for('static', filename='uploads/output_video.mp4', _external=True)



def parse_resolution(res_string):
    resolutions = {
        '360p': (640, 360),
        '480p': (854, 480),
        '720p': (1280, 720),
    }
    return resolutions.get(res_string, (854, 480))

def download_image(image_url):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    return np.array(image)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        insert_audio_files()
    app.run(debug=True)

