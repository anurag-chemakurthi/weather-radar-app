import pyart
import boto3
import botocore
import re
from datetime import datetime

def get_files_in_time_range(bucket_name, prefix, start_time, end_time):
    # Anonymous S3 client for public access
    s3 = boto3.client('s3', config=botocore.config.Config(signature_version=botocore.UNSIGNED))
    
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    if 'Contents' not in response:
        return []

    # Extract times from file names
    time_pattern = re.compile(r'_(\d{6})_V06')
    files = [(obj['Key'], time_pattern.search(obj['Key']).group(1))
             for obj in response['Contents']
             if time_pattern.search(obj['Key'])]
    
    # Parse times and sort
    files = [(key, datetime.strptime(time, '%H%M%S')) for key, time in files]
    files.sort(key=lambda x: x[1])

    # Parse start and end times
    start_time = datetime.strptime(start_time, '%H%M%S')
    end_time = datetime.strptime(end_time, '%H%M%S')

    # Filter files that are within the time range
    filtered_files = [key for key, time in files if start_time <= time <= end_time]

    return filtered_files

def download_and_read_files(bucket_name, file_keys):
    radar_data = []
    print("Downloading files...")
    for key in file_keys:
        if '_MDM' in key:
            print(f"Metadata file. Skipping {key}")
            continue
        file_url = f's3://{bucket_name}/{key}'
        try:
            print(f"Downloading {key}")
            radar = pyart.io.read_nexrad_archive(file_url)
            radar_data.append(radar)
        except OSError as e:
            print(f"Error reading {file_url}: {e}")
    print("All files downloaded.")
    return radar_data

# Example usage
bucket = 'noaa-nexrad-level2'
year, month, day = 2024, 1, 1
station = 'KAMA'
start_time = '000000'  # HHMMSS format
end_time = '235959'    # HHMMSS format

prefix = f'{year}/{month:02}/{day:02}/{station}/{station}{year}{month:02}{day:02}_'
files = get_files_in_time_range(bucket, prefix, start_time, end_time)
print("Files in the time range:")
for file in files:
    print(file)
print("")
radar_data = download_and_read_files(bucket, files)
for radar in radar_data:
    print(f"{radar} stored in local memory")
