import sqlite3  # Reloaded with new API keys
import os
import json
from flask import Flask, request, jsonify, g, abort, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash # Used for password hashing
from functools import wraps
import datetime
import logging
import random # For stochastic severity and randomization in suggestions
from agents.crop_suggestion import Crop_Suggestion, CropSuggestionInputError
from agents.knowledge_base import DEFAULT_CROP, get_crop_details

from agents.provider import Agent
from agents.fertilizer_recommender import FertilizerRecommender
from agents.disease_diagonsis import DiseaseDiagnosis
from dotenv import load_dotenv


# Load environment variables (force override to respect .env changes)
load_dotenv(override=True)
GEN_API_KEY = os.getenv('GEMINI_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
# Sanity check: ensure we aren't using a dummy value if a real one exists in .env
if WEATHER_API_KEY == "dummy_weather_key":
    WEATHER_API_KEY = "38f655d86ea3100d7717c708fb382c7a"

# --- Configuration ---
DATABASE = "farm_app.db"
SECRET_KEY = os.environ.get('SECRET_KEY', 'a-very-secret-key-for-dev') # Use env var in production

# --- Flask App Setup ---
app = Flask(__name__)
app.config['DATABASE'] = DATABASE
app.config['SECRET_KEY'] = SECRET_KEY
# Optional: Enable CORS if your frontend is on a different domain
# Optional: Enable CORS if your frontend is on a different domain
from flask_cors import CORS
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def absolute_upload_url(path):
    if not path:
        return path
    normalized = str(path).replace('\\', '/')
    if normalized.startswith(('http://', 'https://')):
        return normalized
    if normalized.startswith('/uploads/'):
        normalized = normalized[1:]
    elif not normalized.startswith('uploads/'):
        return path
    return f"{request.host_url.rstrip('/')}/{normalized}"

def normalize_image_urls(row, fields=('image_url', 'image_storage_url')):
    if not row:
        return row
    normalized = dict(row)
    for field in fields:
        if field in normalized:
            normalized[field] = absolute_upload_url(normalized[field])
    return normalized


# --- Database Helper Functions ---

def dict_factory(cursor, row):
    """Convert database row objects to dictionaries keyed by column names."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(
                app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = dict_factory
            # Enable foreign key constraint enforcement for this connection
            g.db.execute("PRAGMA foreign_keys = ON;")
            print("DB connection opened.")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            abort(500, description="Database connection error.")
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
        print("DB connection closed.")

def query_db(query, args=(), one=False):
    """Helper function to execute queries."""
    try:
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except sqlite3.Error as e:
        print(f"Database query error: {e}\nQuery: {query}\nArgs: {args}")
        abort(500, description=f"Database error: {e}")

def execute_db(sql, args=()):
    """Helper function for INSERT, UPDATE, DELETE."""
    try:
        conn = get_db()
        cur = conn.execute(sql, args)
        conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id # Return the ID of the inserted row
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error: {e}\nSQL: {sql}\nArgs: {args}")
        abort(409, description=f"Data integrity violation: {e}") # Use 409 Conflict for integrity errors like UNIQUE constraints
    except sqlite3.Error as e:
        print(f"Database execution error: {e}\nSQL: {sql}\nArgs: {args}")
        abort(500, description=f"Database execution error: {e}")


# --- Authentication ---
# Simple token-based auth for demo. In production, use JWT with proper expiry and refresh mechanisms.
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.user = None
        g.device_auth = False

        auth_header = request.headers.get('Authorization')
        device_key = request.headers.get('X-Device-Key')

        if auth_header and auth_header.startswith("Bearer demo-token-user-"):
            try:
                # Extract user ID from the simple demo token
                user_id = int(auth_header.split('-')[-1])
                # Optional: Verify user_id actually exists in DB
                # user_check = query_db("SELECT id FROM users WHERE id = ?", (user_id,), one=True)
                # if not user_check:
                #    abort(401, description="Invalid user in token.")
                g.user = {'id': user_id} # Attach user info to Flask's 'g' object
                print(f"User authenticated: {g.user['id']}")
            except (ValueError, IndexError):
                 abort(401, description="Invalid demo token format.")

        # Allow device key authentication specifically for the ingest endpoint
        elif request.path == '/api/v1/ingest/soil-readings' and device_key:
             # TODO: Validate device_key against a secure store or hardware_devices table
             if device_key.startswith("device-key-"): # Dummy validation
                 g.device_auth = True # Indicate device authentication
                 print("Device authenticated via X-Device-Key.")
             else:
                 abort(401, description="Invalid device key.")

        # If neither user nor valid device auth for ingest endpoint, deny access
        if not g.user and not g.device_auth:
            abort(401, description="Authentication required.")

        return f(*args, **kwargs)
    return decorated_function

# --- API Endpoints ---

@app.route('/')
def home():
    return jsonify({"message": "Welcome to KisanSarthi Backend API", "status": "running"}), 200

# 1. Authentication (/auth)
@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('password') or not data.get('name'):
        abort(400, description="Missing required fields: name, email, password.")

    # email = data['email']
    name = data['name']
    phone = data.get('phone_number') # Optional

    # --- SECURITY: Hash the password ---
    password_hash = generate_password_hash(data['password'])
    # --- End Security ---

    sql = "INSERT INTO users (name, phone_number, password_hash) VALUES (?, ?, ?)"
    try:
        user_id = execute_db(sql, (name, phone, password_hash))
        user = query_db("SELECT id, name FROM users WHERE id = ?", (user_id,), one=True)
        # Generate simple demo token (replace with JWT in production)
        token = f"demo-token-user-{user_id}"
        return jsonify({"user": user, "token": token}), 201
    except sqlite3.IntegrityError: # Caught by execute_db, but can be caught here for specific message
        abort(409, description=f"phone number '{phone}' already registered.")

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email_or_phone') or not data.get('password'):
        abort(400, description="Missing email_or_phone or password.")

    login_identifier = data['email_or_phone']
    password_attempt = data['password']

    user = query_db("SELECT * FROM users WHERE phone_number = ?",
                    (login_identifier,), one=True)

    # --- SECURITY: Check hashed password ---
    if user and check_password_hash(user['password_hash'], password_attempt):
        # --- End Security ---
        # Generate simple demo token (replace with JWT in production)
        token = f"demo-token-user-{user['id']}"
        user_info = { "id": user['id'], "name": user['name'] }
        return jsonify({"user": user_info, "token": token}), 200
    else:
        abort(401, description="Invalid credentials.")

# 2. Users (/users)
@app.route('/api/v1/users/me', methods=['GET'])
@auth_required
def get_current_user():
    user = query_db("SELECT id, name, email, phone_number, created_at FROM users WHERE id = ?", (g.user['id'],), one=True)
    if not user:
        # This case should ideally not happen if auth_required works correctly
        abort(404, description="User not found.")
    # Do not return password hash
    user.pop('password_hash', None)
    return jsonify(user), 200

@app.route('/api/v1/users/me', methods=['PUT'])
@auth_required
def update_current_user():
    data = request.get_json()
    if not data:
        abort(400, description="No update data provided.")

    # Only allow updating specific fields
    allowed_fields = ['name', 'phone_number', 'email']
    update_fields = []
    update_values = []

    for field in allowed_fields:
        if field in data:
            # Basic validation example (can be expanded)
            if field == 'phone_number' and data[field] is not None and not isinstance(data[field], str):
                 abort(400, description="Invalid format for phone_number.")
            if field == 'name' and (not isinstance(data[field], str) or not data[field].strip()):
                 abort(400, description="Name cannot be empty.")

            update_fields.append(f"{field} = ?")
            update_values.append(data[field])

    if not update_fields:
        abort(400, description="No valid fields provided for update.")

    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    update_values.append(g.user['id']) # For the WHERE clause

    sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
    execute_db(sql, tuple(update_values))

    # Fetch and return the updated user (excluding password hash)
    user = query_db("SELECT id, name, email, phone_number, created_at, updated_at FROM users WHERE id = ?", (g.user['id'],), one=True)
    return jsonify(user), 200

# 3. Farms (/farms) - (Ownership checks seem okay)
@app.route('/api/v1/farms', methods=['POST'])
@auth_required
def create_farm():
    data = request.get_json()
    if not data or not data.get('farm_name'):
        abort(400, description="Missing required field: farm_name.")
    # Basic input validation
    if len(data['farm_name']) > 100:
         abort(400, description="Farm name too long.")

    sql = """
        INSERT INTO farms (user_id, farm_name, location_latitude, location_longitude, address)
        VALUES (?, ?, ?, ?, ?)
    """
    farm_id = execute_db(sql, (
        g.user['id'],
        data['farm_name'],
        data.get('location_latitude'), # Consider adding type/range validation
        data.get('location_longitude'),# Consider adding type/range validation
        data.get('address')
    ))
    farm = query_db("SELECT * FROM farms WHERE id = ?", (farm_id,), one=True)
    return jsonify(normalize_image_urls(farm)), 201

@app.route('/api/v1/farms', methods=['GET'])
@auth_required
def list_farms():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    if limit > 100: limit = 100 # Add a max limit

    # Subqueries are acceptable for SQLite on moderate data, indexes help
    sql = """
       SELECT
           f.*,
           (SELECT COUNT(*) FROM lands l WHERE l.farm_id = f.id) as land_count,
           (SELECT COUNT(*) FROM hardware_devices hd WHERE hd.farm_id = f.id) as device_count
       FROM farms f
       WHERE f.user_id = ?
       ORDER BY f.created_at DESC
       LIMIT ? OFFSET ?
    """
    farms = [normalize_image_urls(farm) for farm in query_db(sql, (g.user['id'], limit, offset))]
    total = query_db("SELECT COUNT(*) as count FROM farms WHERE user_id = ?", (g.user['id'],), one=True)['count']

    return jsonify({"farms": farms, "total": total}), 200

@app.route('/api/v1/courses', methods=['GET'])
@auth_required
def list_courses():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    if limit > 100: limit = 100 # Add a max limit

    # Subqueries are acceptable for SQLite on moderate data, indexes help
    sql = """
       SELECT
           * FROM Courses
       LIMIT ? OFFSET ?
    """
    courses = query_db(sql, (limit, offset))
    
    return jsonify({"courses": courses,}), 200


@app.route('/api/v1/farms/<int:farm_id>', methods=['GET'])
@auth_required
def get_farm(farm_id):
    # Query includes ownership check and counts
    sql = """
       SELECT
           f.*,
           (SELECT COUNT(*) FROM lands l WHERE l.farm_id = f.id) as land_count,
           (SELECT COUNT(*) FROM hardware_devices hd WHERE hd.farm_id = f.id) as device_count
       FROM farms f
       WHERE f.id = ? AND f.user_id = ?
    """
    farm = query_db(sql, (farm_id, g.user['id']), one=True)
    if not farm:
        abort(404, description="Farm not found or access denied.")
    return jsonify(normalize_image_urls(farm)), 200

@app.route('/api/v1/farms/<int:farm_id>', methods=['PUT'])
@auth_required
def update_farm(farm_id):
    # Verify ownership first
    owner_check = query_db("SELECT id FROM farms WHERE id = ? AND user_id = ?", (farm_id, g.user['id']), one=True)
    if not owner_check:
        abort(404, description="Farm not found or access denied.")

    data = request.get_json()
    if not data:
        abort(400, description="No update data provided.")

    allowed_fields = ['farm_name', 'location_latitude', 'location_longitude', 'address']
    update_fields = []
    update_values = []

    for field in allowed_fields:
        if field in data:
             # Add validation as needed here (e.g., length, type, range)
             if field == 'farm_name' and (not isinstance(data[field], str) or not data[field].strip()):
                 abort(400, description="Farm name cannot be empty.")
             update_fields.append(f"{field} = ?")
             update_values.append(data[field])

    if not update_fields:
        abort(400, description="No valid fields provided for update.")

    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    update_values.append(farm_id) # For the WHERE clause

    sql = f"UPDATE farms SET {', '.join(update_fields)} WHERE id = ?"
    execute_db(sql, tuple(update_values))

    updated_farm = query_db("SELECT * FROM farms WHERE id = ?", (farm_id,), one=True)
    return jsonify(normalize_image_urls(updated_farm)), 200

@app.route('/api/v1/farms/<int:farm_id>', methods=['DELETE'])
@auth_required
def delete_farm(farm_id):
    # Verify ownership before deleting
    owner_check = query_db("SELECT id FROM farms WHERE id = ? AND user_id = ?", (farm_id, g.user['id']), one=True)
    if not owner_check:
        abort(404, description="Farm not found or access denied.")

    # Assuming DB has CASCADE delete set up for related tables (lands, devices etc.)
    # If not, delete related records manually here first.
    execute_db("DELETE FROM farms WHERE id = ?", (farm_id,))
    return '', 204 # No Content

@app.route('/api/v1/farms/<int:farm_id>/image', methods=['POST'])
@auth_required
def upload_farm_image(farm_id):
    owner_check = query_db("SELECT id FROM farms WHERE id = ? AND user_id = ?", (farm_id, g.user['id']), one=True)
    if not owner_check:
        abort(404, description="Farm not found or access denied.")

    if 'image' not in request.files:
        abort(400, description="No image file provided.")
    
    file = request.files['image']
    if file.filename == '':
        abort(400, description="No selected file.")
        
    if file:
        import uuid
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"farm_{farm_id}_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        image_url = f"/uploads/{filename}"
        execute_db("UPDATE farms SET image_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (image_url, farm_id))
        
        updated_farm = query_db("SELECT * FROM farms WHERE id = ?", (farm_id,), one=True)
        return jsonify(normalize_image_urls(updated_farm)), 200


# 4. Lands (/farms/{farm_id}/lands and /lands) - (Ownership checks seem okay)
@app.route('/api/v1/farms/<int:farm_id>/lands', methods=['POST'])
@auth_required
def create_land(farm_id):
    # Verify farm ownership
    farm = query_db("SELECT id FROM farms WHERE id = ? AND user_id = ?", (farm_id, g.user['id']), one=True)
    if not farm:
        abort(403, description="Access denied to this farm.")

    data = request.get_json()
    if not data or not data.get('land_name') or 'area' not in data or not data.get('area_unit'):
         abort(400, description="Missing required fields: land_name, area, area_unit.")
    # Basic validation
    try:
        area = float(data['area'])
        if area <= 0: raise ValueError("Area must be positive")
    except (ValueError, TypeError):
         abort(400, description="Invalid area value.")
    if data['area_unit'] not in ['hectares', 'acres', 'sq_meters']: # Example valid units
         abort(400, description="Invalid area_unit.")

    sql = """
        INSERT INTO lands (farm_id, land_name, area, area_unit, soil_type_manual)
        VALUES (?, ?, ?, ?, ?)
    """
    land_id = execute_db(sql, (
        farm_id,
        data['land_name'],
        area,
        data['area_unit'],
        data.get('soil_type_manual') # Optional field
    ))
    land = query_db("SELECT * FROM lands WHERE id = ?", (land_id,), one=True)
    return jsonify(land), 201

@app.route('/api/v1/farms/<int:farm_id>/lands', methods=['GET'])
@auth_required
def list_lands(farm_id):
    # Verify farm ownership
    farm = query_db("SELECT id FROM farms WHERE id = ? AND user_id = ?", (farm_id, g.user['id']), one=True)
    if not farm:
        abort(403, description="Access denied to this farm.")

    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    if limit > 200: limit = 200 # Set max limit

    # LEFT JOINs are efficient for getting related optional data
    sql = """
       SELECT
           l.*,
           c.crop_name as current_crop_name,
           p.status as current_planting_status,
           hd.device_name as assigned_device_name,
           hd.id as assigned_device_id
       FROM lands l
       LEFT JOIN plantings p ON l.current_planting_id = p.id
       LEFT JOIN crops c ON p.crop_id = c.id
       LEFT JOIN hardware_devices hd ON hd.assigned_land_id = l.id
       WHERE l.farm_id = ?
       ORDER BY l.land_name
       LIMIT ? OFFSET ?
    """
    lands = query_db(sql, (farm_id, limit, offset))
    total = query_db("SELECT COUNT(*) as count FROM lands WHERE farm_id = ?", (farm_id,), one=True)['count']

    # Reformat slightly to nest related info
    formatted_lands = []
    for land in lands:
        land_data = {k: v for k, v in land.items() if k not in ['current_crop_name', 'current_planting_status', 'assigned_device_name', 'assigned_device_id']}
        if land['current_planting_id']:
            land_data['current_planting'] = {'id': land['current_planting_id'], 'crop_name': land['current_crop_name'], 'status': land['current_planting_status']}
        else:
            land_data['current_planting'] = None
        if land['assigned_device_id']:
             land_data['assigned_device'] = {'id': land['assigned_device_id'], 'device_name': land['assigned_device_name']}
        else:
             land_data['assigned_device'] = None
        formatted_lands.append(land_data)

    return jsonify({"lands": formatted_lands, "total": total}), 200

@app.route('/api/v1/lands/<int:land_id>', methods=['GET'])
@auth_required
def get_land(land_id):
    # Verify ownership via farm_id JOIN
    land = query_db("SELECT l.*, f.user_id, f.address as farm_address, f.farm_name FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
    if not land or land['user_id'] != g.user['id']:
        abort(404, description="Land not found or access denied.")

    # Fetch related data: planting, device, latest reading
    planting = None
    if land.get('current_planting_id'):
        planting_sql = """
            SELECT p.id, p.planting_date, p.status, c.id as crop_id, c.crop_name
            FROM plantings p JOIN crops c ON p.crop_id = c.id
            WHERE p.id = ?
        """
        planting_data = query_db(planting_sql, (land['current_planting_id'],), one=True)
        if planting_data:
            planting = {
                "id": planting_data['id'],
                "crop": { "id": planting_data['crop_id'], "crop_name": planting_data['crop_name'] },
                "planting_date": planting_data['planting_date'],
                "status": planting_data['status']
            }

    device_sql = """
        SELECT id, hardware_unique_id, device_name, status, last_seen_at
        FROM hardware_devices WHERE assigned_land_id = ?
    """
    device = query_db(device_sql, (land_id,), one=True)

    latest_reading_sql = """
        SELECT * FROM soil_readings WHERE land_id = ? ORDER BY timestamp DESC LIMIT 1
    """
    latest_reading = query_db(latest_reading_sql, (land_id,), one=True)

    # Construct response, excluding user_id
    response_data = {k: v for k, v in land.items() if k != 'user_id'}
    response_data['current_planting'] = planting
    response_data['assigned_device'] = device  # type: ignore
    response_data['latest_soil_reading'] = latest_reading  # type: ignore

    return jsonify(response_data), 200

@app.route('/api/v1/lands/<int:land_id>', methods=['PUT'])
@auth_required
def update_land(land_id):
    # Verify ownership
    owner_check = query_db("SELECT l.id, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
    if not owner_check or owner_check['user_id'] != g.user['id']:
        abort(404, description="Land not found or access denied.")

    data = request.get_json()
    if not data:
        abort(400, description="No update data provided.")

    # current_planting_id is managed via planting API, do not allow direct update here
    allowed_fields = ['land_name', 'area', 'area_unit', 'soil_type_manual', 'soil_type_detected']
    update_fields = []
    update_values = []

    for field in allowed_fields:
        if field in data:
             # Add validation similar to create_land
            if field == 'area':
                try:
                    area = float(data['area'])
                    if area <= 0: raise ValueError("Area must be positive")
                    update_values.append(area)
                except (ValueError, TypeError):
                    abort(400, description="Invalid area value.")
            elif field == 'area_unit' and data[field] not in ['hectares', 'acres', 'sq_meters']:
                 abort(400, description="Invalid area_unit.")
            elif field == 'land_name' and (not isinstance(data[field], str) or not data[field].strip()):
                 abort(400, description="Land name cannot be empty.")
            else:
                update_values.append(data[field])
            update_fields.append(f"{field} = ?")

    if not update_fields:
        abort(400, description="No valid fields provided for update.")

    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    update_values.append(land_id) # For the WHERE clause

    sql = f"UPDATE lands SET {', '.join(update_fields)} WHERE id = ?"
    execute_db(sql, tuple(update_values))

    # Fetch the full updated land details for the response
    updated_land = get_land(land_id).get_json() # Reuse the GET logic
    return jsonify(updated_land), 200

@app.route('/api/v1/lands/<int:land_id>', methods=['DELETE'])
@auth_required
def delete_land(land_id):
    # Verify ownership
    owner_check = query_db("SELECT l.id, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
    if not owner_check or owner_check['user_id'] != g.user['id']:
        abort(404, description="Land not found or access denied.")

    # Assuming CASCADE delete for plantings, readings, diagnosis_logs related to this land.
    # If not, manual deletion is needed. Also, unassign any hardware device.
    execute_db("UPDATE hardware_devices SET assigned_land_id = NULL, status = 'inactive', updated_at = CURRENT_TIMESTAMP WHERE assigned_land_id = ?", (land_id,))
    execute_db("DELETE FROM lands WHERE id = ?", (land_id,))
    return '', 204

# 5. Hardware Devices (/hardware_devices) - (Ownership checks seem okay)
@app.route('/api/v1/hardware_devices', methods=['POST'])
@auth_required
def register_hardware_device():
    data = request.get_json()
    if not data or not data.get('hardware_unique_id') or not data.get('farm_id'):
        abort(400, description="Missing required fields: hardware_unique_id, farm_id.")

    farm_id = data['farm_id']
    # Verify farm ownership
    farm = query_db("SELECT id FROM farms WHERE id = ? AND user_id = ?", (farm_id, g.user['id']), one=True)
    if not farm:
        abort(403, description="Access denied: Farm not found or does not belong to user.")

    assigned_land_id = data.get('assigned_land_id')
    new_status = 'inactive' # Default status
    if assigned_land_id:
        # Verify land belongs to the specified farm
        land = query_db("SELECT id FROM lands WHERE id = ? AND farm_id = ?", (assigned_land_id, farm_id), one=True)
        if not land:
            abort(400, description="Assigned land plot does not belong to the specified farm.")
         # Check if land is already assigned a device (enforces one device per land)
        existing_device = query_db("SELECT id FROM hardware_devices WHERE assigned_land_id = ?", (assigned_land_id,), one=True)
        if existing_device:
            abort(409, description=f"Land plot {assigned_land_id} already has a device assigned.")
        new_status = 'active'

    sql = """
        INSERT INTO hardware_devices
        (hardware_unique_id, farm_id, assigned_land_id, device_name, model, registration_date, status)
        VALUES (?, ?, ?, ?, ?, DATE('now'), ?)
    """
    try:
        device_id = execute_db(sql, (
            data['hardware_unique_id'],
            farm_id,
            assigned_land_id,
            data.get('device_name'),
            data.get('model'),
            new_status
        ))
    except sqlite3.IntegrityError as e:
         # Specifically catch unique hardware_unique_id violation
         if 'UNIQUE constraint failed: hardware_devices.hardware_unique_id' in str(e):
              abort(409, description=f"Device with Hardware Unique ID '{data['hardware_unique_id']}' already registered.")
         else:
              abort(409, description=f"Data integrity violation: {e}") # General integrity error


    device = query_db("SELECT * FROM hardware_devices WHERE id = ?", (device_id,), one=True)
    return jsonify(device), 201

@app.route('/api/v1/farms/<int:farm_id>/hardware_devices', methods=['GET'])
@auth_required
def list_farm_hardware_devices(farm_id):
    # Verify farm ownership
    farm = query_db("SELECT id FROM farms WHERE id = ? AND user_id = ?", (farm_id, g.user['id']), one=True)
    if not farm:
        abort(403, description="Access denied to this farm.")

    status_filter = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    if limit > 100: limit = 100

    sql_base = "SELECT hd.id, hd.hardware_unique_id, hd.device_name, hd.status, hd.assigned_land_id, l.land_name as assigned_land_name, hd.last_seen_at FROM hardware_devices hd LEFT JOIN lands l ON hd.assigned_land_id = l.id WHERE hd.farm_id = ?"
    params = [farm_id]

    if status_filter:
        sql_base += " AND hd.status = ?"
        params.append(status_filter)

    sql = sql_base + " ORDER BY hd.device_name LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    count_sql = "SELECT COUNT(*) as count FROM hardware_devices WHERE farm_id = ?"
    count_params = [farm_id]
    if status_filter:
        count_sql += " AND status = ?"
        count_params.append(status_filter)


    devices = query_db(sql, tuple(params))
    total = query_db(count_sql, tuple(count_params), one=True)['count']

    return jsonify({"devices": devices, "total": total}), 200

@app.route('/api/v1/hardware_devices/<int:device_id>', methods=['GET'])
@auth_required
def get_hardware_device(device_id):
     # Verify ownership via farm JOIN
    device = query_db("""
        SELECT hd.*, f.user_id, l.land_name as assigned_land_name
        FROM hardware_devices hd
        JOIN farms f ON hd.farm_id = f.id
        LEFT JOIN lands l ON hd.assigned_land_id = l.id
        WHERE hd.id = ?
        """, (device_id,), one=True)

    if not device or device['user_id'] != g.user['id']:
        abort(404, description="Device not found or access denied.")

    # Don't send user_id back
    response_data = {k: v for k, v in device.items() if k != 'user_id'}
    return jsonify(response_data), 200

@app.route('/api/v1/hardware_devices/<int:device_id>', methods=['PUT'])
@auth_required
def update_hardware_device(device_id):
    # Verify ownership via JOIN
    owner_check = query_db("SELECT hd.id FROM hardware_devices hd JOIN farms f ON hd.farm_id = f.id WHERE hd.id = ? AND f.user_id = ?",
                           (device_id, g.user['id']), one=True)
    if not owner_check:
        abort(404, description="Device not found or access denied.")

    data = request.get_json()
    if not data:
        abort(400, description="No update data provided.")

    # Assignment and hardware_unique_id are generally not updated here
    allowed_fields = ['device_name', 'model', 'status']
    update_fields = []
    update_values = []

    for field in allowed_fields:
        if field in data:
             # Add validation (e.g., status must be valid enum)
            if field == 'status' and data[field] not in ['active', 'inactive', 'maintenance', 'error']:
                 abort(400, description="Invalid status value.")
            update_fields.append(f"{field} = ?")
            update_values.append(data[field])

    if not update_fields:
        abort(400, description="No valid fields provided for update.")

    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    update_values.append(device_id)

    sql = f"UPDATE hardware_devices SET {', '.join(update_fields)} WHERE id = ?"
    execute_db(sql, tuple(update_values))

    updated_device = get_hardware_device(device_id).get_json() # Reuse GET logic
    return jsonify(updated_device), 200

@app.route('/api/v1/hardware_devices/<int:device_id>/assignment', methods=['PUT'])
@auth_required
def update_device_assignment(device_id):
    # Verify ownership and get farm_id
    device = query_db("SELECT hd.id, hd.farm_id, f.user_id FROM hardware_devices hd JOIN farms f ON hd.farm_id = f.id WHERE hd.id = ?",
                       (device_id,), one=True)
    if not device or device['user_id'] != g.user['id']:
        abort(404, description="Device not found or access denied.")

    data = request.get_json()
    # Allow 'assigned_land_id' to be explicitly null for unassignment
    if 'assigned_land_id' not in data:
        abort(400, description="Missing required field: assigned_land_id (can be null).")

    assigned_land_id = data['assigned_land_id']
    new_status = 'inactive' # Default if unassigning

    if assigned_land_id is not None:
        try:
            assigned_land_id = int(assigned_land_id) # Ensure it's an int if not null
        except (ValueError, TypeError):
             abort(400, description="Invalid format for assigned_land_id.")

        # Verify land exists and belongs to the same farm
        land = query_db("SELECT id FROM lands WHERE id = ? AND farm_id = ?", (assigned_land_id, device['farm_id']), one=True)
        if not land:
            abort(400, description="Assigned land plot not found or does not belong to the device's farm.")
        # Check if land is already assigned to *another* device
        existing_device = query_db("SELECT id FROM hardware_devices WHERE assigned_land_id = ? AND id != ?", (assigned_land_id, device_id), one=True)
        if existing_device:
            abort(409, description=f"Land plot {assigned_land_id} already has device {existing_device['id']} assigned.")
        new_status = 'active' # Set status to active upon successful assignment


    sql = "UPDATE hardware_devices SET assigned_land_id = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    execute_db(sql, (assigned_land_id, new_status, device_id))

    updated_device = get_hardware_device(device_id).get_json() # Reuse GET logic
    return jsonify(updated_device), 200

@app.route('/api/v1/hardware_devices/<int:device_id>', methods=['DELETE'])
@auth_required
def delete_hardware_device(device_id):
    # Verify ownership
    owner_check = query_db("SELECT hd.id FROM hardware_devices hd JOIN farms f ON hd.farm_id = f.id WHERE hd.id = ? AND f.user_id = ?",
                           (device_id, g.user['id']), one=True)
    if not owner_check:
        abort(404, description="Device not found or access denied.")

    # Assuming CASCADE delete handles readings. If not, delete readings first.
    execute_db("DELETE FROM hardware_devices WHERE id = ?", (device_id,))
    return '', 204

# 6. Soil Readings (/lands/{land_id}/soil-readings and /ingest)
@app.route('/api/v1/lands/<int:land_id>/soil-readings', methods=['GET'])
@auth_required
def get_soil_readings(land_id):
     # Verify ownership via farm_id JOIN
    owner_check = query_db("SELECT l.id, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
    if not owner_check or owner_check['user_id'] != g.user['id']:
        abort(404, description="Land not found or access denied.")

    # Filtering parameters
    start_date = request.args.get('start_date') # Expect ISO format e.g., 2023-10-26 or 2023-10-26T10:00:00Z
    end_date = request.args.get('end_date')
    parameters = request.args.get('parameters') # e.g., "ph_value,rainfall"
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    if limit > 1000: limit = 1000 # Max limit for readings

    # Define allowed columns for selection to prevent selecting arbitrary data
    allowed_params = ['id', 'timestamp', 'received_at', 'land_id', 'device_id', 'farm_id',
                      'ph_value', 'nitrogen_value', 'phosphorus_value', 'potassium_value',
                      'rainfall', 'temperature_value', 'humidity_value']
    select_cols = "id, timestamp, received_at, land_id, device_id" # Default minimal columns

    if parameters:
        req_params = [p.strip() for p in parameters.split(',') if p.strip() in allowed_params]
        # Ensure core columns are always included if specific params are requested
        select_cols_set = set(req_params).union({'id', 'timestamp', 'land_id', 'device_id'})
        select_cols = ", ".join(sorted(list(select_cols_set))) # Sort for consistent query caching if used
    else:
        select_cols = "*" # Select all allowed columns if no specific params requested

    sql = f"SELECT {select_cols} FROM soil_readings WHERE land_id = ?"
    count_sql = "SELECT COUNT(*) as count FROM soil_readings WHERE land_id = ?"
    params = [land_id]
    count_params = [land_id]

    # Add date filtering (ensure valid date formats)
    try:
        if start_date:
            # Validate format (basic check)
            datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            sql += " AND timestamp >= ?"
            count_sql += " AND timestamp >= ?"
            params.append(start_date)
            count_params.append(start_date)
        if end_date:
            datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # Make end_date exclusive for ranges (e.g., up to midnight)
            # If end_date is just a date 'YYYY-MM-DD', treat it as up to 'YYYY-MM-DD 23:59:59.999...'
            # SQLite handles date comparisons reasonably well. Adding a check for '<' vs '<='.
            # For simplicity, we'll use '<=' assuming user provides the exact end point they want.
            # More robust range handling might involve adding a day if only date is provided.
            sql += " AND timestamp <= ?"
            count_sql += " AND timestamp <= ?"
            params.append(end_date)
            count_params.append(end_date)
    except ValueError:
        abort(400, description="Invalid date format. Use ISO 8601 format (e.g., YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ).")


    sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    readings = query_db(sql, tuple(params))
    total = query_db(count_sql, tuple(count_params), one=True)['count']

    return jsonify({"readings": readings, "total": total}), 200

@app.route('/api/v1/ingest/soil-readings', methods=['POST'])
@auth_required # Uses device auth check inside decorator
def ingest_soil_reading():
    # Ensure this endpoint was called with device authentication
    if not hasattr(g, 'device_auth') or not g.device_auth:
         abort(401, description="Device authentication required for ingestion.")

    data = request.get_json()
    if not data or not data.get('hardware_unique_id') or not data.get('timestamp'):
        abort(400, description="Missing hardware_unique_id or timestamp in reading.")

    hw_unique_id = data['hardware_unique_id']

    # Validate timestamp format
    try:
        # Ensure timestamp is valid ISO format (or format expected from device)
        reading_ts = datetime.datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')).isoformat()
    except ValueError:
        abort(400, description="Invalid timestamp format. Use ISO 8601 format.")

    # Find the device and its current assignment based on the hardware ID
    device = query_db("SELECT id, farm_id, assigned_land_id, status FROM hardware_devices WHERE hardware_unique_id = ?", (hw_unique_id,), one=True)

    if not device:
        print(f"Warning: Received reading from unknown device HW ID: {hw_unique_id}")
        # Consider if you want to create a log entry for unknown devices
        abort(404, description="Device not registered.")

    if not device['assigned_land_id']:
        print(f"Info: Received reading from unassigned device: {hw_unique_id} (ID: {device['id']})")
        # Decide action: reject, store in a separate log, or store without land_id.
        # Current decision: Reject as readings are tied to land plots.
        return jsonify({"message": "Device is not assigned to a land plot. Reading ignored."}), 202 # Accepted but not processed as intended

    land_id = device['assigned_land_id']
    farm_id = device['farm_id']
    device_id = device['id']
    rainfall = data.get("rainfall")
    if rainfall is None:
        return {"error": "rainfall is required"}, 400
    try:
        rainfall = float(rainfall)
    except (TypeError, ValueError):
        return {"error": "rainfall must be numeric"}, 400

    # Map incoming data keys to database columns, handling potential missing values gracefully (as NULL)
    sql = """
        INSERT INTO soil_readings (
            device_id, land_id, farm_id, timestamp, ph_value,
            nitrogen_value, phosphorus_value, potassium_value,
            rainfall, temperature_value, humidity_value
            -- received_at is handled by DEFAULT CURRENT_TIMESTAMP in schema
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        device_id,
        land_id,
        farm_id,
        reading_ts, # Use validated timestamp
        data.get('ph_value'), # .get() returns None if key is missing
        data.get('nitrogen_value'),
        data.get('phosphorus_value'),
        data.get('potassium_value'),
        rainfall,
        data.get('temperature_value'),
        data.get('humidity_value')
    )
    execute_db(sql, params)

    # Update last_seen_at and potentially status for the device
    # Set status to 'active' if it wasn't already? Or handle status based on reading quality?
    execute_db("UPDATE hardware_devices SET last_seen_at = CURRENT_TIMESTAMP, status = 'active' WHERE id = ?", (device_id,))

    # Optional: Trigger further processing (e.g., update land's latest reading cache, run checks)

    return jsonify({"message": "Reading accepted"}), 202 # Use 202 Accepted


@app.route('/api/v1/lands/<int:land_id>/manual-soil-reading', methods=['POST'])
@auth_required
def save_manual_soil_reading(land_id):
    # Verify ownership
    land = query_db("SELECT l.id, l.farm_id, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
    if not land or land['user_id'] != g.user['id']:
        abort(404, description="Land not found or access denied.")

    data = request.get_json()
    if not data:
        abort(400, description="No reading data provided.")

    farm_id = land['farm_id']
    
    # Generate/Get a "Manual Entry" device for this farm to satisfy the foreign key constraint
    # We use a deterministic unique ID for the manual device of this farm.
    manual_hw_id = f"manual_farm_{farm_id}"
    
    # Check if exists
    device = query_db("SELECT id FROM hardware_devices WHERE hardware_unique_id = ?", (manual_hw_id,), one=True)
    if not device:
        # Create it
        print(f"Creating virtual manual device for farm {farm_id}")
        execute_db("""
            INSERT INTO hardware_devices (hardware_unique_id, farm_id, device_name, status, last_seen_at) 
            VALUES (?, ?, 'Manual Entry Device', 'active', CURRENT_TIMESTAMP)
        """, (manual_hw_id, farm_id))
        # Fetch back ID
        device = query_db("SELECT id FROM hardware_devices WHERE hardware_unique_id = ?", (manual_hw_id,), one=True)
    
    device_id = device['id']
    
    # Prepare params
    timestamp = data.get('timestamp')
    if not timestamp:
         timestamp = datetime.datetime.utcnow().isoformat()

    try:
        # Validate format if provided
        timestamp = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00')).isoformat()
    except ValueError:
        timestamp = datetime.datetime.utcnow().isoformat() # Fallback to now if invalid
    
    rainfall = data.get("rainfall")
    if rainfall is None:
        return {"error": "rainfall is required"}, 400
    try:
        rainfall = float(rainfall)
    except (TypeError, ValueError):
        return {"error": "rainfall must be numeric"}, 400

    sql = """
        INSERT INTO soil_readings (
            device_id, land_id, farm_id, timestamp, ph_value,
            nitrogen_value, phosphorus_value, potassium_value,
            rainfall, temperature_value, humidity_value
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        device_id,
        land_id,
        farm_id,
        timestamp,
        data.get('ph'),
        data.get('N'),
        data.get('P'),
        data.get('K'),
        rainfall,
        data.get('temperature'),
        data.get('humidity')
    )
    
    execute_db(sql, params)
    
    return jsonify({"message": "Manual reading saved successfully."}), 201

# 7. Plantings (/lands/{land_id}/plantings and /plantings) - (Ownership checks seem okay)
@app.route('/api/v1/lands/<int:land_id>/plantings', methods=['POST'])
@auth_required
def start_planting(land_id):
    # Verify land ownership
    land = query_db("SELECT l.id, l.current_planting_id, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
    if not land or land['user_id'] != g.user['id']:
        abort(404, description="Land not found or access denied.")

    data = request.get_json()
    if not data or not data.get('crop_id') or not data.get('planting_date'):
        abort(400, description="Missing required fields: crop_id, planting_date.")

    # Check if there's already an active planting linked to the land
    if land['current_planting_id']:
        existing_active = query_db("SELECT id, status FROM plantings WHERE id = ?", (land['current_planting_id'],), one=True)
        if existing_active and existing_active['status'] == 'active':
            if data.get('override'):
                execute_db("DELETE FROM plantings WHERE id = ?", (existing_active['id'],))
            else:
                abort(409, description="An active planting already exists for this land plot. Mark the current one as 'harvested' or 'failed' first.")

    # Verify crop exists
    crop = query_db("SELECT id FROM crops WHERE id = ?", (data['crop_id'],), one=True)
    if not crop:
        abort(400, description="Invalid crop_id.")

    # Validate date formats
    try:
        planting_date = datetime.datetime.fromisoformat(data['planting_date'].replace('Z', '+00:00')).date().isoformat()
        expected_harvest_date = None
        if data.get('expected_harvest_date'):
             expected_harvest_date = datetime.datetime.fromisoformat(data['expected_harvest_date'].replace('Z', '+00:00')).date().isoformat()
    except ValueError:
         abort(400, description="Invalid date format for planting_date or expected_harvest_date. Use YYYY-MM-DD.")

    sql = """
        INSERT INTO plantings (land_id, crop_id, planting_date, expected_harvest_date, notes, status)
        VALUES (?, ?, ?, ?, ?, 'active')
    """
    planting_id = execute_db(sql, (
        land_id,
        data['crop_id'],
        planting_date,
        expected_harvest_date,
        data.get('notes')
    ))

    # Update the land record to link to this new active planting
    execute_db("UPDATE lands SET current_planting_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (planting_id, land_id))

    # Fetch the created planting with crop info for the response
    new_planting = query_db("""
        SELECT p.*, c.crop_name
        FROM plantings p JOIN crops c ON p.crop_id = c.id
        WHERE p.id = ?
        """, (planting_id,), one=True)

    return jsonify(new_planting), 201

@app.route('/api/v1/plantings/<int:planting_id>', methods=['GET'])
@auth_required
def get_planting(planting_id):
    # Verify ownership via land -> farm JOIN
    planting = query_db("""
        SELECT p.*, c.crop_name, f.user_id, l.id as land_id, l.land_name
        FROM plantings p
        JOIN lands l ON p.land_id = l.id
        JOIN farms f ON l.farm_id = f.id
        JOIN crops c ON p.crop_id = c.id
        WHERE p.id = ?
        """, (planting_id,), one=True)

    if not planting or planting['user_id'] != g.user['id']:
        abort(404, description="Planting not found or access denied.")

    # Remove user_id before sending response
    response_data = {k: v for k, v in planting.items() if k != 'user_id'}
    return jsonify(response_data), 200

@app.route('/api/v1/plantings/<int:planting_id>', methods=['DELETE'])
@auth_required
def delete_planting(planting_id):
    planting_check = query_db("""
        SELECT p.id, p.land_id, f.user_id, l.current_planting_id
        FROM plantings p
        JOIN lands l ON p.land_id = l.id
        JOIN farms f ON l.farm_id = f.id
        WHERE p.id = ?
        """, (planting_id,), one=True)

    if not planting_check or planting_check['user_id'] != g.user['id']:
        abort(404, description="Planting not found or access denied.")

    if planting_check['current_planting_id'] == planting_id:
        execute_db("UPDATE lands SET current_planting_id = NULL WHERE id = ?", (planting_check['land_id'],))

    execute_db("DELETE FROM plantings WHERE id = ?", (planting_id,))
    return '', 204

@app.route('/api/v1/plantings/<int:planting_id>', methods=['PUT'])
@auth_required
def update_planting(planting_id):
    # Verify ownership and get land_id
    planting_check = query_db("""
        SELECT p.id, p.land_id, p.status as current_status, f.user_id
        FROM plantings p
        JOIN lands l ON p.land_id = l.id
        JOIN farms f ON l.farm_id = f.id
        WHERE p.id = ?
        """, (planting_id,), one=True)

    if not planting_check or planting_check['user_id'] != g.user['id']:
        abort(404, description="Planting not found or access denied.")

    data = request.get_json()
    if not data:
        abort(400, description="No update data provided.")

    allowed_fields = ['status', 'expected_harvest_date', 'actual_harvest_date', 'notes']
    allowed_statuses = ['active', 'harvested', 'failed', 'canceled']
    update_fields = []
    update_values = []
    new_status = None

    for field in allowed_fields:
        if field in data:
            value = data[field]
            if field == 'status':
                if value not in allowed_statuses:
                    abort(400, description=f"Invalid status. Allowed values: {', '.join(allowed_statuses)}")
                new_status = value
            elif field in ['expected_harvest_date', 'actual_harvest_date'] and value is not None:
                try:
                    # Validate date format, allow null
                    value = datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).date().isoformat()
                except ValueError:
                     abort(400, description=f"Invalid date format for {field}. Use YYYY-MM-DD.")

            update_fields.append(f"{field} = ?")
            update_values.append(value)

    if not update_fields:
        abort(400, description="No valid fields provided for update.")

    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    update_values.append(planting_id) # For WHERE clause

    sql = f"UPDATE plantings SET {', '.join(update_fields)} WHERE id = ?"
    execute_db(sql, tuple(update_values))

    # If status changed *away* from 'active', update the corresponding land's current_planting_id to NULL
    # Check if the status *actually* changed and the *new* status is not 'active'
    was_active = planting_check['current_status'] == 'active'
    is_no_longer_active = new_status is not None and new_status != 'active'

    if was_active and is_no_longer_active:
         land_id = planting_check['land_id']
         print(f"Planting {planting_id} status changed to {new_status}. Unlinking from land {land_id}.")
         # Only unlink if this planting *was* the current one for the land
         execute_db("UPDATE lands SET current_planting_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND current_planting_id = ?",
                    (land_id, planting_id))
    # If status changes *to* 'active', check if land has another active planting? (should be handled by POST logic mostly)

    updated_planting = get_planting(planting_id).get_json() # Reuse GET logic
    return jsonify(updated_planting), 200

# 8. Diagnostics / Disease Scan (/diagnostics)
def ensure_diagnosis_log_columns():
    diagnosis_columns = query_db("PRAGMA table_info(diagnosis_logs)")
    diagnosis_column_names = {column['name'] for column in diagnosis_columns}
    if 'crop_name_context' not in diagnosis_column_names:
        execute_db("ALTER TABLE diagnosis_logs ADD COLUMN crop_name_context TEXT NULL")
    if 'lang' not in diagnosis_column_names:
        execute_db("ALTER TABLE diagnosis_logs ADD COLUMN lang TEXT DEFAULT 'English'")
    if 'error_message' not in diagnosis_column_names:
        execute_db("ALTER TABLE diagnosis_logs ADD COLUMN error_message TEXT NULL")
    if 'result_json' not in diagnosis_column_names:
        execute_db("ALTER TABLE diagnosis_logs ADD COLUMN result_json TEXT NULL")


def run_diagnosis_analysis_once(log_id, force=False):
    log = query_db("SELECT * FROM diagnosis_logs WHERE id = ?", (log_id,), one=True)
    if not log:
        print(f"AI analysis skipped: log_id {log_id} not found.")
        return

    if log['processing_status'] == 'processing' and not force:
        print(f"AI analysis not re-run for log_id {log_id}; status is already processing.")
        return

    if log['processing_status'] != 'processing':
        print(f"AI analysis skipped for log_id {log_id}; status is {log['processing_status']}.")
        return

    print(f"AI analysis started for log_id: {log_id}")
    result = None
    detected_disease_id = None
    confidence = None
    error_message = None

    try:
        image_path = os.path.join(app.root_path, log['image_storage_url'])
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        with open(image_path, "rb") as f:
            image_data = {"data": f.read(), "mime_type": "image/jpeg"}

        soil_data = {}
        crop_name = (log.get('crop_name_context') or '').strip()
        if log['land_id']:
            latest_reading = query_db("SELECT * FROM soil_readings WHERE land_id = ? ORDER BY timestamp DESC LIMIT 1", (log['land_id'],), one=True)
            if latest_reading:
                soil_data = {
                    "Nitrogen": latest_reading.get('nitrogen_value'),
                    "Phosphorus": latest_reading.get('phosphorus_value'),
                    "Potassium": latest_reading.get('potassium_value'),
                    "pH": latest_reading.get('ph_value')
                }

            planting = query_db("SELECT c.crop_name FROM plantings p JOIN crops c ON p.crop_id = c.id WHERE p.land_id = ? AND p.status='active'", (log['land_id'],), one=True)
            if not crop_name and planting:
                crop_name = planting['crop_name']
        if not crop_name:
            raise ValueError("Selected crop is required.")

        diagnosis_agent = DiseaseDiagnosis(GEN_API_KEY)
        result = diagnosis_agent.execute(
            image=image_data,
            location="Maharashtra",
            WEATHER_API_KEY=WEATHER_API_KEY,
            soil_data=soil_data,
            crop=crop_name,
            lang=log.get('lang', 'English')
        )

        if result.get("is_diseased"):
            disease_data = result.get('detected_disease') or {}
            disease_name = disease_data.get('disease_name') or 'Unknown Disease'
            disease = query_db("SELECT id FROM diseases WHERE disease_name = ?", (disease_name,), one=True)
            if disease:
                detected_disease_id = disease['id']
            else:
                detected_disease_id = execute_db(
                    "INSERT INTO diseases (disease_name, description, symptoms) VALUES (?, ?, ?)",
                    (
                        disease_name,
                        disease_data.get('description'),
                        disease_data.get('symptoms')
                    )
                )
                for remedy in result.get('remedies', []):
                    execute_db(
                        "INSERT INTO remedies (disease_id, remedy_type, description, application_instructions) VALUES (?, ?, ?, ?)",
                        (
                            detected_disease_id,
                            remedy.get('remedy_type'),
                            remedy.get('description'),
                            remedy.get('application_instructions')
                        )
                    )

        confidence = result.get('confidence_score', 1.0 if not result.get("is_diseased") else 0.9)
        completion_status = 'completed'
        print(f"AI analysis completed for log_id: {log_id}")
    except Exception as e:
        print(f"AI analysis failed for log_id {log_id}: {e}")
        completion_status = 'failed'
        error_message = str(e)

    execute_db("""
        UPDATE diagnosis_logs
        SET processing_status = ?, detected_disease_id = ?, confidence_score = ?, error_message = ?,
            result_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?""",
        (completion_status, detected_disease_id, confidence, error_message, json.dumps(result) if result else None, log_id))


@app.route('/api/v1/diagnostics/scan-plant', methods=['POST'])
@auth_required
def scan_plant_disease():
    print("Yayy")
    print(f"DEBUG: Content-Type: {request.content_type}")
    print(f"DEBUG: Files keys: {request.files.keys()}")
    print(f"DEBUG: Form keys: {request.form.keys()}")
    if 'image' in request.form:
         print(f"DEBUG: request.form['image'] content (first 100 chars): {str(request.form['image'])[:100]}")

    if 'image' not in request.files:
        print(f"DEBUG: 'image' not found in files. Aborting 400.")
        abort(400, description="Missing 'image' file in request.")

    image_file = request.files['image']
    # Consider adding file size and type validation
    # filename = secure_filename(image_file.filename) # Use secure_filename

    land_id = request.form.get('land_id', type=int) # Optional, but recommended
    planting_id = request.form.get('planting_id', type=int) # Optional
    crop_name_context = (request.form.get('crop_name') or '').strip()
    if crop_name_context.lower() == 'unknown':
        abort(400, description="Selected crop is required.")

    # --- Verify land/planting ownership if IDs are provided ---
    if land_id:
        owner_check = query_db("SELECT l.id, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
        if not owner_check or owner_check['user_id'] != g.user['id']:
             abort(403, description="Access denied to the specified land plot.")
    if planting_id:
        owner_check = query_db("SELECT p.id, f.user_id FROM plantings p JOIN lands l ON p.land_id=l.id JOIN farms f ON l.farm_id = f.id WHERE p.id = ?", (planting_id,), one=True)
        if not owner_check or owner_check['user_id'] != g.user['id']:
             abort(403, description="Access denied to the specified planting.")
        # Optional: Check if planting_id belongs to land_id if both provided

    # --- Real File Handling ---
    uploads_dir = os.path.join(app.root_path, 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        
    filename = f"{g.user['id']}_{int(datetime.datetime.utcnow().timestamp())}_{image_file.filename}"
    file_path = os.path.join(uploads_dir, filename)
    image_file.save(file_path)
    
    # Store the actual local path or a relative URL
    image_storage_url = f"uploads/{filename}"
    print(f"Received image: {filename}. Saved to: {file_path}")
    # --- End Real File Handling ---

    lang = request.form.get('lang', 'English')
    ensure_diagnosis_log_columns()
    sql = """
        INSERT INTO diagnosis_logs (user_id, land_id, planting_id, image_storage_url, crop_name_context, processing_status, lang)
        VALUES (?, ?, ?, ?, ?, 'processing', ?)
    """
    log_id = execute_db(sql, (g.user['id'], land_id, planting_id, image_storage_url, crop_name_context or None, lang))
    run_diagnosis_analysis_once(log_id, force=True)
    log = query_db("SELECT processing_status FROM diagnosis_logs WHERE id = ?", (log_id,), one=True)

    return jsonify({"log_id": log_id, "status": log['processing_status'], "image_url": absolute_upload_url(image_storage_url), "message": "Image received and analysis triggered."}), 202


@app.route('/api/v1/diagnostics/logs/<int:log_id>', methods=['GET'])
@app.route('/api/v1/diagnostics/<int:log_id>', methods=['GET'])
@auth_required
def get_diagnosis_log(log_id):
    # Verify ownership
    ensure_diagnosis_log_columns()
    log = query_db("SELECT * FROM diagnosis_logs WHERE id = ? AND user_id = ?", (log_id, g.user['id']), one=True)
    if not log:
        abort(404, description="Diagnosis log not found or access denied.")

    print(f"Diagnosis poll for log_id: {log_id}, status: {log['processing_status']}")
    if log['processing_status'] in ('pending', 'processing'):
        return jsonify({"log_id": log_id, "status": "processing"}), 200
    if log['processing_status'] == 'failed':
        return jsonify({"log_id": log_id, "status": "failed", "error_message": log.get('error_message')}), 200

    # Prepare response data from the (potentially updated) log
    response_data = normalize_image_urls(log)
    response_data['status'] = log['processing_status']
    response_data['result'] = json.loads(log['result_json']) if log.get('result_json') else None

    # If completed and a disease was detected, fetch related disease details and remedies
    response_data['detected_disease'] = None  # type: ignore
    response_data['remedies'] = [] # Use list even if empty  # type: ignore

    if log['processing_status'] == 'completed' and log['detected_disease_id']:
        disease = query_db("SELECT id, disease_name, description, symptoms, image_url FROM diseases WHERE id = ?",
                           (log['detected_disease_id'],), one=True)
        if disease:
            response_data['detected_disease'] = normalize_image_urls(disease)  # type: ignore
            # Fetch associated remedies
            remedies = query_db("SELECT id, remedy_type, description, application_instructions FROM remedies WHERE disease_id = ?",
                                (log['detected_disease_id'],))
            response_data['remedies'] = remedies if remedies else []  # type: ignore

    return jsonify(response_data), 200

@app.route('/api/v1/diagnostics/logs', methods=['GET'])
@auth_required
def list_diagnosis_logs():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    land_id = request.args.get('land_id', type=int)
    status = request.args.get('status')
    if limit > 100: limit = 100

    sql_base = """
        SELECT l.id as log_id, l.scan_timestamp, l.processing_status, l.image_storage_url,
               l.land_id, land.land_name,
               l.detected_disease_id, d.disease_name as detected_disease_name
        FROM diagnosis_logs l
        LEFT JOIN diseases d ON l.detected_disease_id = d.id
        LEFT JOIN lands land ON l.land_id = land.id -- Join to filter/display land name
        LEFT JOIN farms f ON land.farm_id = f.id -- Needed if filtering by farm
        WHERE l.user_id = ?
    """
    count_base = """
        SELECT COUNT(*) as count
        FROM diagnosis_logs l
        LEFT JOIN lands land ON l.land_id = land.id
        LEFT JOIN farms f ON land.farm_id = f.id
        WHERE l.user_id = ?
    """
    params = [g.user['id']]
    count_params = [g.user['id']]

    if land_id:
        # Ensure user owns this land
        owner_check = query_db("SELECT l.id, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
        if not owner_check or owner_check['user_id'] != g.user['id']:
             abort(403, description="Access denied to the specified land plot's logs.")
        sql_base += " AND l.land_id = ?"
        count_base += " AND l.land_id = ?"
        params.append(land_id)
        count_params.append(land_id)

    if status:
        sql_base += " AND l.processing_status = ?"
        count_base += " AND l.processing_status = ?"
        params.append(status)
        count_params.append(status)


    sql = sql_base + " ORDER BY l.scan_timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    logs = [normalize_image_urls(log) for log in query_db(sql, tuple(params))]
    total = query_db(count_base, tuple(count_params), one=True)['count']

    return jsonify({"logs": logs, "total": total}), 200

# 9. Recommendations (Crops, Fertilizers, Tips)
@app.route('/api/v1/lands/<int:land_id>/crop-suggestions', methods=['GET'])
@auth_required
def get_crop_suggestions(land_id):
     # Verify ownership
    land = query_db("SELECT l.id, l.soil_type_detected, l.soil_type_manual, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
    if not land or land['user_id'] != g.user['id']:
        abort(404, description="Land not found or access denied.")

    # --- Placeholder: Crop Suggestion Logic ---
    suggestions = []
    latest_reading = query_db("""
        SELECT timestamp, nitrogen_value, phosphorus_value, potassium_value, rainfall, ph_value, temperature_value, humidity_value
        FROM soil_readings
        WHERE land_id = ?
          AND nitrogen_value IS NOT NULL
          AND phosphorus_value IS NOT NULL
          AND potassium_value IS NOT NULL
          AND rainfall IS NOT NULL
          AND ph_value IS NOT NULL
          AND temperature_value IS NOT NULL
          AND humidity_value IS NOT NULL
        ORDER BY timestamp DESC LIMIT 1
        """, (land_id,), one=True)
    if not latest_reading:
        abort(400, description="Please add soil data first")

    latest_reading_ts = latest_reading['timestamp'] if latest_reading else "N/A"
    current_n = latest_reading.get('nitrogen_value')
    current_p = latest_reading.get('phosphorus_value')
    current_k = latest_reading.get('potassium_value')
    current_r = latest_reading.get('rainfall')
    ph_value = latest_reading.get('ph_value')
    current_t = latest_reading.get('temperature_value')
    current_h = latest_reading.get('humidity_value')

    lang = request.args.get('lang', 'English')
    address = land.get('address') or "Maharashtra"
    lat = land.get('location_latitude')
    lon = land.get('location_longitude')
    try:
        soil_payload = {
            "Nitrogen" : current_n,
            "Phosphorus" : current_p,
            "Potassium" : current_k,
            "rainfall" : current_r,
            "pH" : ph_value
        }
        soil_payload["temperature"] = current_t
        soil_payload["humidity"] = current_h

        crop = Crop_Suggestion(GEN_API_KEY).execute(
            location=address, 
            WEATHER_API_KEY=WEATHER_API_KEY, 
            soil_data=soil_payload,
            lang=lang,
            lat=lat,
            lon=lon
        )
    except CropSuggestionInputError as e:
        abort(400, description=str(e))
    except Exception as e:
        print(f"Error executing Crop_Suggestion agent: {e}")
        abort(500, description="Crop suggestion service failed. Please retry.")

    def require_crop_field(data, key):
        value = data.get(key)
        if value is None:
            abort(500, description=f"Crop suggestion response is missing '{key}'.")
        return value

    top_predictions = crop.get("top_crops") or [{"crop": crop.get("Crop"), "confidence": crop.get("Match")}]
    primary_crop = crop.get("primary_crop")

    # --- Dynamic Crop Integration ---
    for prediction_item in top_predictions:
        crop_name = str(prediction_item.get("crop", "")).strip()
        if not crop_name or crop_name.lower() == "unknown":
            continue

        confidence = prediction_item.get("confidence")
        if confidence is None:
            confidence = crop.get("Match", DEFAULT_CROP["Match"])

        try:
            crop_details = get_crop_details(crop_name)
        except Exception:
            crop_details = {
                **DEFAULT_CROP,
                "Description": f"{crop_name.title()} is recommended by the trained crop model for the current farm conditions.",
                "Explanation": (
                    f"{crop_name.title()} is suitable based on the current N, P, K, "
                    "temperature, humidity, pH, and rainfall values."
                ),
            }

        db_crop = query_db("SELECT * FROM crops WHERE crop_name = ?", (crop_name,), one=True)
        if db_crop:
            crop_id = db_crop['id']
            crop_description = db_crop['description'] or crop_details["Description"]
            image_url = db_crop['image_url'] or f"https://source.unsplash.com/featured/?{crop_name},agriculture"
            ph_min = db_crop['optimal_ph_min']
            ph_max = db_crop['optimal_ph_max']
            moisture_range = db_crop['optimal_moisture_range']
        else:
            print(f"Registering new crop: {crop_name}")
            crop_description = crop_details["Description"]
            image_url = f"https://source.unsplash.com/featured/?{crop_name},field"
            ph_min = None
            ph_max = None
            moisture_range = None

            crop_id = execute_db(
                "INSERT INTO crops (crop_name, description, image_url, optimal_ph_min, optimal_ph_max, optimal_moisture_range) VALUES (?, ?, ?, ?, ?, ?)",
                (crop_name, crop_description, image_url, ph_min, ph_max, moisture_range)
            )

        explanation = crop_details["Explanation"]
        suggestions.append({
            "crop": {
                "id": crop_id,
                "crop_name": crop_name,
                "description": crop_description,
                "image_url": absolute_upload_url(image_url),
                "optimal_ph_min": ph_min,
                "optimal_ph_max": ph_max,
                "optimal_moisture_range": moisture_range
            },
            "cropName": crop_name,
            "match": float(confidence),
            "suitability_score": float(confidence),
            "explanation": explanation,
            "reasoning": explanation,
            "growing_season": crop_details.get("growing_season", DEFAULT_CROP["growing_season"]),
            "best_season": "Local Kharif or Rabi cycles",
            "growth_duration": "--",
            "water_requirement": crop_details.get("water_requirement", DEFAULT_CROP["water_requirement"]),
            "total_water_liters": "--",
            "spacing": "--",
            "expected_yield" : crop_details.get("expected_yield", DEFAULT_CROP["expected_yield"]),
            "Recommendations" : crop_details.get("Recommendations", DEFAULT_CROP["Recommendations"]),
            "top_crops": top_predictions,
            "primary_crop": primary_crop,
            "details": {
                 "ph_match": float(confidence),
                 "npk_match": float(confidence),
                 "Nitrogen" : current_n,
                 "Phosphorus" : current_p,
                 "Potassium" : current_k,
                 "pH" : ph_value
             }
        })

    if not suggestions:
        abort(500, description="Crop suggestion service returned no valid crops.")
    print(suggestions)

    # Sort suggestions by score descending
    suggestions.sort(key=lambda x: x['suitability_score'], reverse=True)
    # --- End Placeholder ---

    return jsonify({
        "based_on_reading_ts": latest_reading_ts,
        "land_id": land_id,
        "suggestions": suggestions
    }), 200

@app.route('/api/v1/lands/<int:land_id>/fertilizer-recommendations', methods=['GET'])
@auth_required
def get_fertilizer_recommendations(land_id):
     # Verify ownership
    land = query_db("SELECT l.id, l.soil_type_detected, l.soil_type_manual, f.user_id FROM lands l JOIN farms f ON l.farm_id = f.id WHERE l.id = ?", (land_id,), one=True)
    if not land or land['user_id'] != g.user['id']:
        abort(404, description="Land not found or access denied.")

    # --- Placeholder: Crop Suggestion Logic ---
    suggestions = []
    latest_reading = query_db("""
        SELECT sr.timestamp, sr.nitrogen_value, sr.phosphorus_value, sr.potassium_value,
               sr.rainfall, sr.ph_value, sr.temperature_value, sr.humidity_value,
               p.crop_id, c.crop_name
        FROM soil_readings sr
        LEFT JOIN plantings p ON p.land_id = sr.land_id AND p.status = 'active'
        LEFT JOIN crops c ON c.id = p.crop_id
        WHERE sr.land_id = ?
          AND sr.nitrogen_value IS NOT NULL
          AND sr.phosphorus_value IS NOT NULL
          AND sr.potassium_value IS NOT NULL
          AND sr.rainfall IS NOT NULL
          AND sr.ph_value IS NOT NULL
          AND sr.temperature_value IS NOT NULL
        ORDER BY sr.timestamp DESC
        LIMIT 1
    """, (land_id,), one=True)
    if not latest_reading:
        abort(400, description="Please add soil data first")

    latest_reading_ts = latest_reading['timestamp'] if latest_reading else "N/A"
    current_n = latest_reading.get('nitrogen_value')
    current_p = latest_reading.get('phosphorus_value')
    current_k = latest_reading.get('potassium_value')
    current_r = latest_reading.get('rainfall')
    current_t = latest_reading.get('temperature_value')
    current_h = latest_reading.get('humidity_value')
    ph_value = latest_reading.get('ph_value')
    crop_id = latest_reading.get('crop_id') if latest_reading else None


    lang = request.args.get('lang', 'English')
    soil_color = request.args.get('soil_color', type=int)
    crop_name = (request.args.get('crop') or '').strip()
    if not crop_name or crop_name.lower() == 'unknown':
        abort(400, description="Selected crop is required.")
    print(f"Mapped crop: {crop_name}")
    print(f"Encoded soil: {soil_color}")
    valid_soil_colors = {0, 1, 2, 3, 4}
    if soil_color not in valid_soil_colors:
        abort(400, description="Invalid soil_color. Expected encoded value 0, 1, 2, 3, or 4.")
    
    soil_data = {
        "Nitrogen" : current_n,
        "Phosphorus" : current_p,
        "Potassium" : current_k,
        "rainfall" : current_r,
        "temperature" : current_t,
        "humidity" : current_h,
        "pH" : ph_value
    }
    
    soil_data["Soil_color"] = soil_color

    try:
        fertilizer = FertilizerRecommender(GEN_API_KEY).execute(
            crop=crop_name,
            location="Maharashtra",
            WEATHER_API_KEY=WEATHER_API_KEY,
            soil_data=soil_data,
            lang=lang
        )
    except ValueError as e:
        abort(400, description=str(e))
    active_recommendations = []
    active_recommendations.append({
         "recommendation_type": "fertilizer",
         "title": f"Apply {fertilizer['Fertilizer_Product']}",
         "details": fertilizer['Description'],
         "reasoning": fertilizer['Explanation'],
         "amount" : fertilizer['Amount'],
         "price" : fertilizer["Price"],
         "buyat" : fertilizer['Buy at'],
         "severity": "medium", # Optimal severity for standard recommendation
    })
    # --- End Live Logic ---

    return jsonify({
        "based_on_reading_ts": latest_reading_ts,
        "land_id": land_id,
        "recommendations": active_recommendations
    }), 200

@app.route('/api/v1/recommendations', methods=['GET'])
@auth_required
def get_recommendations():
    try:
        # Parameters with validation
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        rec_type = request.args.get('type')
        is_read_filter = request.args.get('is_read')
        farm_id = request.args.get('farm_id', type=int)
        land_id = request.args.get('land_id', type=int)

        # Validate boolean filter
        if is_read_filter and is_read_filter.lower() not in ['true', 'false']:
            return jsonify({"error": "Invalid is_read parameter"}), 400

        # Base query
        sql_base = """
            SELECT r.*, l.land_name AS related_land_name, f.farm_name AS related_farm_name
            FROM recommendations r
            LEFT JOIN lands l ON r.land_id = l.id
            LEFT JOIN farms f ON l.farm_id = f.id
            WHERE r.user_id = ? AND r.is_archived = 0
        """
        count_base = "SELECT COUNT(*) AS count FROM recommendations r WHERE r.user_id = ? AND r.is_archived = 0"
        params = [g.user['id']]
        count_params = [g.user['id']]

        # Filters
        if rec_type:
            sql_base += " AND r.recommendation_type = ?"
            count_base += " AND r.recommendation_type = ?"
            params.append(rec_type)
            count_params.append(rec_type)

        if is_read_filter is not None:
            is_read_val = 1 if is_read_filter.lower() == 'true' else 0
            sql_base += " AND r.is_read = ?"
            count_base += " AND r.is_read = ?"
            params.append(is_read_val)
            count_params.append(is_read_val)

        if land_id:
            sql_base += " AND r.land_id = ?"
            count_base += " AND r.land_id = ?"
            params.append(land_id)
            count_params.append(land_id)

        # Final query
        sql_base += " ORDER BY r.recommendation_date DESC, r.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        recommendations = query_db(sql_base, tuple(params))
        total = query_db(count_base, tuple(count_params), one=True)['count']

        return jsonify({"recommendations": recommendations, "total": total}), 200

    except Exception as e:
        logging.error(f"Error fetching recommendations: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/recommendations/<int:recommendation_id>/status', methods=['PUT'])
@auth_required
def update_recommendation_status(recommendation_id):
    # Verify ownership
    rec = query_db("SELECT id, user_id FROM recommendations WHERE id = ?", (recommendation_id,), one=True)
    if not rec or rec['user_id'] != g.user['id']:
        abort(404, description="Recommendation not found or access denied.")

    data = request.get_json()
    if not data or ('is_read' not in data and 'is_archived' not in data):
        abort(400, description="Missing 'is_read' or 'is_archived' boolean field.")

    updates = []
    params = []
    valid_update = False
    if 'is_read' in data:
        if isinstance(data['is_read'], bool):
            updates.append("is_read = ?")
            params.append(1 if data['is_read'] else 0)
            valid_update = True
        else:
            abort(400, description="'is_read' must be a boolean (true/false).")

    if 'is_archived' in data:
        if isinstance(data['is_archived'], bool):
            updates.append("is_archived = ?")
            params.append(1 if data['is_archived'] else 0)
            valid_update = True
        else:
             abort(400, description="'is_archived' must be a boolean (true/false).")

    if not valid_update:
         abort(400, description="No valid status field provided.")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(recommendation_id) # For WHERE

    sql = f"UPDATE recommendations SET {', '.join(updates)} WHERE id = ?"
    execute_db(sql, tuple(params))

    # Return No Content as the update was successful, client can refetch if needed.
    return '', 204


# 10. Reference Data (Generally public or requires basic auth)
@app.route('/api/v1/crops', methods=['GET'])
# @auth_required # Decide if this needs auth
def list_crops():
    # Add caching here if data doesn't change often
    crops = [normalize_image_urls(crop) for crop in query_db("SELECT id, crop_name, description, image_url, optimal_ph_min, optimal_ph_max FROM crops ORDER BY crop_name")]
    return jsonify(crops if crops else []), 200

@app.route('/api/v1/diseases', methods=['GET'])
# @auth_required # Decide if this needs auth
def list_diseases():
    # Add caching
    diseases = [normalize_image_urls(disease) for disease in query_db("SELECT id, disease_name, description, symptoms, image_url FROM diseases ORDER BY disease_name")]
    return jsonify(diseases if diseases else []), 200

@app.route('/api/v1/fertilizers', methods=['GET'])
# @auth_required # Decide if this needs auth
def list_fertilizers():
    # Add caching
    fertilizers = query_db("SELECT id, fertilizer_name, type, description, n_percentage, p_percentage, k_percentage FROM fertilizers ORDER BY fertilizer_name")
    return jsonify(fertilizers if fertilizers else []), 200

@app.route('/api/v1/market/prices', methods=['GET'])
@auth_required
def get_market_prices():
    crop_name = request.args.get('crop', 'Rice')
    location = request.args.get('location', 'Maharashtra') # Default to Maharashtra if no specific city/location provided
    lang = request.args.get('lang', 'English')

    # Use the Agent to generate realistic market data
    try:
        agent = Agent(GEN_API_KEY)
        today_date = datetime.date.today().strftime("%d/%m/%Y")
        
        task = f"""
        Role: Market Data Generator.
        Task: Generate realistic agricultural market price data for '{crop_name}' in {location}, India for date {today_date}.
        Output Language: Respond EXCLUSIVELY in {lang}. All text values in the JSON (market names, districts, varieties, etc.) MUST be in {lang}.

        Output Format: A JSON object containing a key "records" which is a list of 5 objects.
        Each object MUST have these exact ENGLISH keys: "State", "District", "Market", "Commodity", "Variety", "Arrival_Date", "Min_Price", "Max_Price", "Modal_Price".
        
        Constraints:
        - "Commodity" should be "{crop_name}" (translated to {lang}).
        - "Arrival_Date" should be "{today_date}".
        - Prices should be realistic for the Indian market (in INR/Quintal).
        - "Market" should be real market names close to or in "{location}" (translated to {lang}).
        - Output ONLY valid JSON. Do not include markdown formatting.
        - ABSOLUTELY NO English text in values if {lang} is not English.
        """
        
        response_text = agent.execute(task)
        
        # Clean up response to ensure it's valid JSON
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned_text)
        
        return jsonify(data), 200
        
    except Exception as e:
        print(f"Error fetching market data from Gemini: {e}")
        # Knowledge Base Fallback Records (Professional estimations)
        return jsonify({
            "status": "Knowledge Base Fallback",
            "records": [
                {
                    "State": "Maharashtra",
                    "District": location if location != "Maharashtra" else "Pune",
                    "Market": location if location != "Maharashtra" else "Pune APMC",
                    "Commodity": crop_name,
                    "Variety": "Local",
                    "Arrival_Date": datetime.date.today().strftime("%d/%m/%Y"),
                    "Min_Price": "3200",
                    "Max_Price": "4200",
                    "Modal_Price": "3700"
                },
                {
                    "State": "Maharashtra",
                    "District": "Nashik",
                    "Market": "Lasalgaon",
                    "Commodity": crop_name,
                    "Variety": "Hybrid",
                    "Arrival_Date": datetime.date.today().strftime("%d/%m/%Y"),
                    "Min_Price": "3400",
                    "Max_Price": "4500",
                    "Modal_Price": "4000"
                }
            ]
        }), 200

# 11. Static File Serving
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(os.path.join(app.root_path, 'uploads'), filename)

# --- Error Handlers ---
@app.errorhandler(400)
def bad_request(error):
    response = jsonify({'error': 'Bad Request', 'message': error.description})
    response.status_code = 400
    return response

@app.errorhandler(401)
def unauthorized(error):
    response = jsonify({'error': 'Unauthorized', 'message': error.description})
    response.status_code = 401
    return response

@app.errorhandler(403)
def forbidden(error):
    response = jsonify({'error': 'Forbidden', 'message': error.description})
    response.status_code = 403
    return response

@app.errorhandler(404)
def not_found(error):
    response = jsonify({'error': 'Not Found', 'message': error.description})
    response.status_code = 404
    return response

@app.errorhandler(409)
def conflict(error):
    response = jsonify({'error': 'Conflict', 'message': error.description})
    response.status_code = 409
    return response

@app.errorhandler(500)
def internal_server_error(error):
    response = jsonify({'error': 'Internal Server Error', 'message': error.description})
    response.status_code = 500
    return response

# --- Weather API ---
@app.route('/api/v1/weather', methods=['GET'])
def get_weather():
    """Fetch current weather data from OpenWeatherMap.
    Query params: lat, lon (preferred) or city.
    Returns: { temperature, humidity, rainfall }
    """
    from agents.weather_agent import get_weather_data

    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    city = request.args.get('city', None)

    if lat is None or lon is None:
        if not city:
            abort(400, description="Provide lat & lon, or city query parameter.")

    try:
        data = get_weather_data(city_name=city, WEATHER_API_KEY=WEATHER_API_KEY, lat=lat, lon=lon)
        if data is None:
            abort(502, description="Failed to fetch weather data from external service.")
        return jsonify(data), 200
    except Exception as e:
        print(f"Weather API error: {e}")
        abort(500, description=f"Weather fetch failed: {str(e)}")


# --- Main Execution ---
if __name__ == '__main__':
    from create_db import main as createdb
    # Check if DB exists, if not, inform user to run create_db.py
    if not os.path.exists(DATABASE):
        print(f"Database file '{DATABASE}' not found.")
        print("Running the `create_db.py` script first to initialize the database schema.")
        createdb()

    # --- Initialize Database with Agricultural Standards ---
    # Connect once to check and potentially add data
    needs_commit = False
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = dict_factory
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # Keep existing databases compatible with the rainfall-based soil reading schema.
        cursor.execute("PRAGMA table_info(soil_readings)")
        soil_reading_columns = {row['name'] for row in cursor.fetchall()}
        if 'rainfall' not in soil_reading_columns:
            cursor.execute("ALTER TABLE soil_readings ADD COLUMN rainfall REAL NULL")
            needs_commit = True

        # Check for users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        if user_count == 0:
            print("Initializing default system user.")
            # Use the same hashing as the register endpoint
            hashed_password = generate_password_hash('password')
            cursor.execute("INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
                        (1, 'Test User', 'test@example.com', hashed_password))
            needs_commit = True

        # Check for crops
        cursor.execute("SELECT COUNT(*) as count FROM crops")
        crop_count = cursor.fetchone()['count']
        if crop_count == 0:
            print("Initializing baseline crop standards (Corn, Tomato).")
            cursor.execute("INSERT INTO crops (crop_name, optimal_ph_min, optimal_ph_max) VALUES (?, ?, ?)", ('Corn', 5.8, 7.0))
            cursor.execute("INSERT INTO crops (crop_name, optimal_ph_min, optimal_ph_max) VALUES (?, ?, ?)", ('Tomato', 6.0, 6.8))
            needs_commit = True

        # Check for diseases
        cursor.execute("SELECT COUNT(*) as count FROM diseases")
        disease_count = cursor.fetchone()['count']
        if disease_count == 0:
            print("Adding dummy disease (Leaf Blight)")
            disease_id = cursor.execute("INSERT INTO diseases (disease_name, description, symptoms) VALUES (?,?,?)",
                        ('Leaf Blight', 'Fungal disease causing spots on leaves', 'Yellowish or brown spots, often with concentric rings.')).lastrowid
            # Add a dummy remedy
            cursor.execute("INSERT INTO remedies (disease_id, remedy_type, description) VALUES (?, ?, ?)",
                           (disease_id, 'fungicide', 'Apply a broad-spectrum fungicide according to label instructions.'))
            needs_commit = True

        # Check for fertilizers
        cursor.execute("SELECT COUNT(*) as count FROM fertilizers")
        fertilizer_count = cursor.fetchone()['count']
        if fertilizer_count == 0:
             print("Adding dummy fertilizers")
             cursor.execute("INSERT INTO fertilizers (fertilizer_name, type, n_content_percent, p_content_percent, k_content_percent) VALUES (?, ?, ?, ?, ?)",
                            ('Balanced NPK 10-10-10', 'npk_compound', 10, 10, 10))
             cursor.execute("INSERT INTO fertilizers (fertilizer_name, type, n_content_percent) VALUES (?, ?, ?)",
                            ('Urea', 'nitrogen_source', 46))
             needs_commit = True

        if needs_commit:
            conn.commit()
            print("Dummy data added.")

    except sqlite3.Error as e:
        print(f"Error during initial data check/add: {e}")
    finally:
        if conn:
            conn.close()
    # --- End initial data add ---

    print(f"Starting Flask app on http://127.0.0.1:5000")
    print("Using SECRET_KEY: " + ("Set from environment variable." if os.environ.get('SECRET_KEY') else f"'{SECRET_KEY}' (Development Only!)"))
    print("=" * 60)
    print("🚀 KisanSarthi Backend Server Started")
    print("=" * 60)
    print("Server running on http://0.0.0.0:5000")
    print("Access from emulator: http://10.0.2.2:5000")
    print("Access from device: Use your computer's LAN IP (e.g., http://192.168.X.X:5000)")
    print("")
    print("📌 Available Endpoints:")
    print("   - GET  /              → Health check")
    print("   - POST /api/v1/auth/register → Register")
    print("   - POST /api/v1/auth/login    → Login")
    print("   - GET  /api/v1/farms        → List farms (auth required)")
    print("   - GET  /api/v1/courses      → List courses (auth required)")
    print("   - POST /api/v1/disease/diagnose → Disease diagnosis")
    print("   - POST /api/v1/fertilizer/recommend → Fertilizer recommendation")
    print("   - POST /api/v1/crop/suggest   → Crop suggestion")
    print("   - GET  /api/v1/weather/current → Weather (auth required)")
    print("")
    print("🔐 Authentication: Use 'Bearer demo-token-user-<user_id>'")
    print("   Example: Authorization: Bearer demo-token-user-1")
    print("=" * 60)
    # Use debug=True ONLY for development. It enables auto-reloading and detailed error pages.
    # Set debug=False and use a production WSGI server (like Gunicorn or uWSGI) in production.
    app.run(host='0.0.0.0', port=5000, debug=True)
