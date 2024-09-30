from flask import Blueprint, jsonify, request, Response, abort
import pandas as pd
from io import StringIO
import requests
import logging
import json
from datetime import datetime
import bcrypt
import MySQLdb
from functools import wraps
from .logging import logEntry
import pytz

logging.basicConfig(level=logging.DEBUG)
global_endpoint = 'login'

api = Blueprint('api', __name__)
# Define the database connection function
def get_db_connection():
    connection = None
    try:
        connection = MySQLdb.connect(
            host="mysql",
            user="myuser",
            password="mypassword",
            db="mydatabase"
        )
    except MySQLdb.Error as err:
        print(f"Error connecting to database: {err}")
    return connection

# Login route using Basic Authentication
# Login route using Basic Authentication
@api.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({"message": "Missing credentials"}), 401

    # Get a database connection
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:
        # Fetch the user details from the database
        cursor.execute("SELECT username, password FROM users WHERE username=%s", (auth.username,))
        user = cursor.fetchone()

        if user is None:
            logEntry('LOGIN', 'login', auth.username, '401', 'Invalid username')
            return jsonify({"message": "Invalid username"}), 401

        username, hashed_password = user
        print(f"Retrieved hashed password: {hashed_password}")  # Debugging line

        # Verify the password using bcrypt
        if bcrypt.checkpw(auth.password.encode('utf-8'), hashed_password.encode('utf-8')):
            logEntry('LOGIN', 'login', auth.username, '200', 'Login successful')
            return jsonify({"message": "Login successful!", "name": auth.username}), 200
        else:
            logEntry('LOGIN', 'login', auth.username, '401', 'Invalid password')
            return jsonify({"message": "Invalid password"}), 401

    except MySQLdb.Error as err:
        logEntry('LOGIN', 'login', auth.username, '500', 'Internal Server Error')
        print(f"Error during login: {err}")
        return jsonify({"message": "Internal Server Error"}), 500

    finally:
        cursor.close()
        conn.close()
    

def basic_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.authorization:
            logEntry('LOGIN', global_endpoint, auth.username, '401', 'Missing credentials')
            return jsonify({"message": "Missing credentials"}), 401
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            logEntry('LOGIN', global_endpoint, auth.username, '401', 'Missing credentials')
            return jsonify({"message": "Missing credentials"}), 401

        # Get a database connection
        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed"}), 500

        cursor = conn.cursor()

        try:
            cursor.execute("SELECT username, password FROM users WHERE username=%s", (auth.username,))
            user = cursor.fetchone()

            if user is None or not bcrypt.checkpw(auth.password.encode('utf-8'), user[1].encode('utf-8')):
                logEntry('LOGIN', global_endpoint , auth.username, '401', 'Invalid credentials')
                return jsonify({"message": "Invalid credentials"}), 401
            
            return f(*args, **kwargs)

        except MySQLdb.Error as err:
            print(f"Error during authentication: {err}")
            logEntry('LOGIN', global_endpoint, auth.username, '500', 'Internal Server Error')
            return jsonify({"message": "Internal Server Error"}), 500

        finally:
            cursor.close()
            conn.close()

    return decorated_function




@api.route('/health', methods=['GET'])
@basic_auth_required
def content():
    auth = request.authorization
    logEntry('INFO', 'health', auth.username, '200', 'Healthy Server')
    logging.info('Health endpoint called')
    return jsonify({"status": "healthy", "message": "APIs up & runing"}), 200


@api.route('/report', methods=['GET'])
@basic_auth_required
def report():
    auth = request.authorization
    report_type = request.args.get('type')
    domain = request.args.get('domain')
    file_path = "data/course_members_output.csv"  # Adjust path based on your structure
    try:
        # Read CSV using pandas
        data = pd.read_csv(file_path)
        logging.info('CSV file read')
        if report_type == 'json':
            # Return CSV content as JSON
            logEntry('INFO', 'report', auth.username, '200', 'JSON Exported')
            return jsonify(data.to_dict(orient="records")), 200
        elif report_type == 'csv':
            # Return CSV content as plain text (comma-separated values)
            csv_text = data.to_csv(index=False)  # Generate CSV string
            logEntry('INFO', 'report', auth.username, '200', 'CSV Exported')
            return Response(csv_text, mimetype='text/plain'), 200
        else:
            logEntry('ERROR', 'report', auth.username, '400', 'Invalid type')
            return jsonify({"error": "Invalid report type. Must be 'csv' or 'json'."}), 400
    except FileNotFoundError:
        logEntry('ERROR', 'report', auth.username, '404', 'CSV not found')
        return jsonify({"error": "Data not found. Please try later"}), 404

@api.route('/datarefresh', methods=['GET'])
@basic_auth_required
def data_refresh():
    auth = request.authorization
    if not auth:
        auth = request.authorization if request and request.authorization else {"username": "system_refresh"}
    logging.info('Data Refresh endpoint called')
    
    # First API call to get the access token
    token_url = 'https://accounts.zoho.com/oauth/v2/token'
    token_payload = {
        'client_id': '1000.OH05NTPXN097SVV244ROKHZ6EKY6KM',
        'client_secret': 'd992479798bb3afadc96b6112e1b21a256b45ed5ce',
        'redirect_uri': 'https://learn.usf-cyber-awareness.org',
        'grant_type': 'refresh_token',
        'refresh_token': '1000.6700636d66c17dcf5ddb82b0b97f5d77.5e1cb26a15e8c2759d4a457f6fdc03b5',
        'scope': 'TrainerCentral.courseapi.READ'
    }

    try:
        # Request access token
        token_response = requests.post(token_url, data=token_payload)
        token_response.raise_for_status()  # Raise an error for bad responses
        access_token = token_response.json().get('access_token')
        logging.info('Access Token Received')

        # Second API call to fetch course members using the access token
        members_url = 'https://learn.usf-cyber-awareness.org/api/v4/846647484/course/3297785000000008005/courseMembers.json'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Cookie': 'TC_CSRF_TOKEN=a0fb4428-a5e8-493e-aacb-ba9d65572b82; _zcsr_tmp=a0fb4428-a5e8-493e-aacb-ba9d65572b82; zalb_4073c92bba=5194a7bdf55a1e81ebbd0c33ed47baec'
        }

        # Make the request to get course members
        members_response = requests.get(members_url, headers=headers)
        members_response.raise_for_status()  # Raise an error for bad responses
        logging.info('Learners Report Response Received')

        # Parse the JSON response
        data = members_response.json()
        filtered_members = [member for member in data['courseMembers'] if member.get('role') == '3']
        
        # Create a DataFrame from the filtered list
        df = pd.DataFrame(filtered_members)

        # Ensure the required columns exist in the DataFrame
        df['name'] = df.get('name', 'N/A')
        df['email'] = df.get('email', 'N/A')
        df['completionPercentage'] = df.get('completionPercentage', '0')
        df['enrolledTime'] = df.get('enrolledTime', None)
        df['lastLogin'] = df.get('lastLogin', None)
        df['completedTime'] = df.get('completedTime', None)

        # Remove rows with any missing values in columns other than 'enrolledTime'
        df = df.dropna(subset=['name', 'email', 'completionPercentage', 'enrolledTime'])

        # Convert 'enrolledTime' from Unix time to a human-readable date (formatted)
        df['e_time'] = pd.to_datetime(df['enrolledTime'].astype('int64'), unit='ms', errors='coerce')
        df['e_time'] = df['e_time'].dt.strftime("%B %d, %Y, %H:%M:%S UTC")

        df['enrolledTime'] = pd.to_datetime(df['enrolledTime'], unit='ms', errors='coerce').dt.date

        # Convert 'lastLogin' from Unix time to a human-readable date (formatted)
        df['lastLogin'] = pd.to_datetime(df['lastLogin'].astype('int64'), unit='ms', errors='coerce')
        df['lastLogin'] = df['lastLogin'].dt.strftime("%B %d, %Y, %H:%M:%S UTC")

        # Convert 'completedTime' from Unix time to a human-readable date (formatted)
        df.fillna(0, inplace=True)
        df['completedTime'] = pd.to_datetime(df['completedTime'].astype('int64'), unit='ms', errors='coerce')
        df['completedTime'] = df['completedTime'].dt.strftime("%B %d, %Y, %H:%M:%S UTC")

        final_df = df[['name', 'email', 'enrolledTime', 'completionPercentage', 'lastLogin', 'completedTime', 'e_time']]
        final_df.columns = ['Name', 'Email', 'Enrolled date', 'Course progress', 'Last Login', 'Completed Time', 'Enrollment Time']

        # Add an 'S.No' column as a series of numbers starting from 1
        final_df.insert(0, 'ID', range(1, len(final_df) + 1))

        
        # Write the DataFrame to a CSV file
        final_df.to_csv('data/course_members_output.csv', index=False)
        logging.info("CSV file created successfully!")
        logEntry('INFO', 'data_refresh', auth.username, '200', 'Refresh Success')
        # Define the path to your CSV file
        csv_file_path = 'data/scheduler.csv'
        # Read the existing CSV file
        try:
            df = pd.read_csv(csv_file_path)
        except FileNotFoundError:
            # If the file doesn't exist, create an empty DataFrame
            df = pd.DataFrame(columns=['timestamp'])
        # Define the EST timezone using pytz
        est = pytz.timezone('US/Eastern')
        # Get the current time in EST
        current_timestamp = datetime.now(est).strftime('%Y-%m-%d %I:%M:%S %p')
        # Create a new DataFrame with the new row to add
        new_row = pd.DataFrame({'timestamp': [current_timestamp]})
        # Concatenate the new row to the existing DataFrame
        df = pd.concat([df, new_row], ignore_index=True)
        # Save the updated DataFrame back to the CSV
        df.to_csv(csv_file_path, index=False)
        updateMetrics()
        return jsonify({"message": "Data refreshed successfully!"}), 200  # Informative response

    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {str(err)}")
        logEntry('ERROR', 'data_refresh', auth.username, '500', 'Refresh Failed')
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logEntry('ERROR', 'data_refresh', auth.username, '500', 'Refresh Failed')
        return jsonify({"error": str(e)}), 500
    


def updateMetrics():
    # Convert time columns to datetime
    final_df = pd.read_csv('data/course_members_output.csv')
    final_df['Completed Time'] = pd.to_datetime(final_df['Completed Time'])
    final_df['Enrollment Time'] = pd.to_datetime(final_df['Enrollment Time'])
    final_df['Last Login'] = pd.to_datetime(final_df['Last Login'])
    final_df['Enrolled date'] = pd.to_datetime(final_df['Enrolled date'])
    completion_percentage = final_df['Course progress'].mean()
    # Convert 'Enrolled date' to datetime
    final_df['Enrolled date'] = pd.to_datetime(final_df['Enrolled date'], errors='coerce')
    # Extract month and year from 'Enrolled date'
    final_df['Enrollment Month'] = final_df['Enrolled date'].dt.to_period('M')
    # Count enrollments per month and sort by the actual month (newest first)
    enrollment_months_count = final_df['Enrollment Month'].value_counts().sort_index(ascending=False)
    # Now format the result in the desired format
    enrollment_months_sorted = [{'month': month.strftime('%B'), 'value': count} for month, count in enrollment_months_count.items()]
    # Select the latest 4 months
    latest_4_months = enrollment_months_sorted[:4]
    # 2. Inactive Participants (No login in the last 14 days)
    # Define the inactive threshold
    inactive_threshold = pd.Timestamp.utcnow() - pd.Timedelta(days=14)

    # Filter rows where 'Last Login' is less than the inactive threshold and 'Course progress' is >= 90
    inactive_participants = final_df[
        (final_df['Last Login'] < inactive_threshold) & 
        (final_df['Course progress'] < 90)
    ].shape[0]
    total_participants = final_df.shape[0]
    count = final_df[final_df['Course progress'] >= 90].shape[0]
    count = round(count/total_participants,2)*100
    # Prepare the result as a JSON object
    result = {
        'total_participants': total_participants,
        'average_completion_rate' : count,
        "completion_percentage": round(completion_percentage,2),
        "inactive_participants": inactive_participants,
        "enrollment_months": enrollment_months_sorted,  # Updated to return counts
    }
    # Write the result to a JSON file
    with open('data/metrics.json', 'w') as json_file:
        json.dump(result, json_file, indent=4)

    # Display the result
    logging.info(json.dumps(result, indent=4))


@api.route('/db_test', methods=['GET'])
@basic_auth_required
def db_test():
    auth = request.authorization
    connection = get_db_connection()
    if connection:
        try:
            # Execute a simple query to verify the connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                db_version = cursor.fetchone()
            connection.close()
            logEntry('INFO', 'db_test', auth.username, '200', 'Database connection successful')
            return jsonify({
                "status": "success",
                "message": "Database connection successful",
                "db_version": db_version[0]
            }), 200
        
        except MySQLdb.Error as err:
            logEntry('INFO', 'db_test', auth.username, '500', 'Error executing query')
            return jsonify({
                "status": "error",
                "message": f"Error executing query: {err}"
            }), 500
    
    else:
        logEntry('ERROR', 'db_test', auth.username, '500', 'Database connection failed')
        return jsonify({
            "status": "error",
            "message": "Could not connect to the database"
        }), 500
    

@api.route('/getDataRefresh', methods=['GET'])
@basic_auth_required
def getDataRefresh():
    auth = request.authorization
    logEntry('INFO', 'getDataRefresh', auth.username, '200', 'Last Data Refresh Time')
    df = pd.read_csv('data/scheduler.csv')
    last_row_timestamp = df['timestamp'].iloc[-1]
    date, time_part, am_pm = last_row_timestamp.rsplit(' ', 2)
    # Combine time and AM/PM
    time_str = f"{time_part} {am_pm}"
    full_datetime_str = f"{date} {time_str}"

    # Parse the full datetime
    last_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %I:%M:%S %p")

    # Set timezone for the last data timestamp (assuming the timestamp is in EST)
    est = pytz.timezone('US/Eastern')
    last_datetime_est = est.localize(last_datetime)

    # Get the current time in UTC and convert it to EST
    current_utc_time = datetime.utcnow()
    current_est_time = pytz.utc.localize(current_utc_time).astimezone(est)

    # Calculate the time difference in minutes
    time_difference = current_est_time - last_datetime_est
    minutes_ago = int(time_difference.total_seconds() // 60)  # Convert seconds to minutes


    # Return response with date, time, and minutes_ago
    return jsonify({
        "status": "okay",
        "date": date,
        "time": time_str,
        "minutes_ago": minutes_ago
    }), 200

    
@api.route('/metrics', methods=['GET'])
@basic_auth_required
def metrics():
    auth = request.authorization
    file_path = 'data/metrics.json'   
    try:
        with open(file_path, 'r') as f:
                data = json.load(f)
                logEntry('INFO', 'stats', auth.username, '200', 'Stats of Course')
        return jsonify(data), 200
    except json.JSONDecodeError:
            # If there's an error in decoding the JSON, return empty dict
        logEntry('INFO', 'stats', auth.username, '200', 'Stats of Course')
        return jsonify({}), 200
    
@api.route('/test', methods=['GET'])
@basic_auth_required
def test_updatemetrics():
    updateMetrics()
    return jsonify({}), 200