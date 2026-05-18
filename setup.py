import sys
import subprocess

# Update pip
print("\nUpdating pip...\n")
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--no-cache-dir"])

# Install dependencies
print("\nInstalling dependencies...\n")

dependencies = [
    "botocore",
    "boto3",
    "cartopy",
    "datetime",
    "geopandas",
    "matplotlib",
    #"os",
    "pandas",
    "git+https://github.com/ARM-DOE/pyart.git", # "arm_pyart" is updated for python3; "pyart" is not.
    "PyQt5",
    #"re",
    "requests",
    "shapely",
    #"sys",
    #"zipfile",
]
for dependency in dependencies:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", dependency, "--no-cache-dir"])
    print("")
