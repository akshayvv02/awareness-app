import pandas as pd
import pytz
import os
from datetime import datetime

def logEntry(level, endpoint, user, status, comment):
    file_path = 'data/logs.csv'
    est = pytz.timezone('US/Eastern')
    
    # Get the current time in EST
    timestamp = datetime.now(est).strftime('%Y-%m-%d %I:%M:%S %p')
    
    # Create the new log entry as a DataFrame
    new_entry = pd.DataFrame({
        'level': [level],
        'endpoint': [endpoint],
        'timestamp': [timestamp],
        'user': [user],
        'status': [status],
        'comment': [comment]
    })
    
    try:
        # Check if the file exists before appending
        if os.path.exists(file_path):
            # Append the new entry without writing headers again
            new_entry.to_csv(file_path, mode='a', header=False, index=False)
        else:
            # If the file doesn't exist, create it and write the headers
            new_entry.to_csv(file_path, mode='w', header=True, index=False)
    except Exception as e:
        print(f"An error occurred while logging: {e}")
    
    print(f"Log entry added successfully: {level}, {endpoint}, {timestamp}, {user}, {status}, {comment}")
