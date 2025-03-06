from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration (Using PostgreSQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://wowdata_user:tUujX4Mw14GOgF6dMwC9MBuzo6e4GDVf@dpg-cv4okubtq21c73fd86f0-a.singapore-postgres.render.com/wowdata'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class Download(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(255), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_downloads = db.Column(db.Integer, default=0)

# Initialize database
with app.app_context():
    db.create_all()
    if Stats.query.first() is None:
        db.session.add(Stats(total_downloads=0))
        db.session.commit()

@app.route('/api/track-download', methods=['POST'])
def track_download():
    """Track a new download using device ID to prevent duplicates"""
    try:
        data = request.get_json()
        device_id = data.get('device_id', str(uuid.uuid4()))

        existing_download = Download.query.filter_by(device_id=device_id).first()

        if not existing_download:
            # Add new download record
            new_download = Download(device_id=device_id)
            db.session.add(new_download)

            # Update total count
            stats = Stats.query.first()
            stats.total_downloads += 1
            db.session.commit()

            is_new = True
        else:
            is_new = False

        return jsonify({
            'success': True,
            'downloads': Stats.query.first().total_downloads,
            'is_new': is_new
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download-count', methods=['GET'])
def get_download_count():
    """Get the current download count"""
    try:
        total_downloads = Stats.query.first().total_downloads
        return jsonify({'success': True, 'downloads': total_downloads})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def home():
    """Render the HTML page with download details"""
    downloads = Download.query.order_by(Download.timestamp.desc()).all()
    total_downloads = Stats.query.first().total_downloads
    return render_template('index.html', downloads=downloads, total_downloads=total_downloads)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
