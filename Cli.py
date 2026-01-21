import subprocess
import shutil
import os
#cd scraper

#scrapy crawl scraping -a topic=<blah> -O sources.json 

# note: MOVE THE SOURCES FILE INTO SCRAPER OR THE SUN WILL EXPLODE

#scrapy crawl sources

try:
    topic=input("What topic are you researching? ")
    python_path = r"C:/Users/noahk/OneDrive/Documents/GitHub/tech-fair-submission/.venv/Scripts/python.exe"
    process = subprocess.Popen(
        [
            python_path,
            "-m",
            "scrapy",
            "crawl",
            "scraping",
            "-a",
            f"topic={topic}",
            "-O",
            "sources.json",
        ],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text=True,
        cwd="scraper"
    )
    stdout, stderr = process.communicate(timeout=30)

    if process.returncode == 0:
        print("Output: ", stdout)
    else:
        print("Error: ", stderr)

    source_file = "scraper\\sources.json"
    goal_source = "scraper\\scraper"

    shutil.move(source_file, goal_source)

    process = subprocess.Popen(
        [
            python_path,
            "-m",
            "scrapy",
            "crawl",
            "sources",
        ],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text=True,
        cwd="scraper"
    )
    stdout, stderr = process.communicate(timeout=300)

    if process.returncode == 0:
        print("Output: ", stdout)
    else:
        print("Error: ", stderr)

    process = subprocess.Popen(
        [
            python_path,
            "ai.py",
        ],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text=True,
        cwd="."
    )
    stdout, stderr = process.communicate(timeout=1800)

    if process.returncode == 0:
        print("Output: ", stdout)
    else:
        print("Error: ", stderr)

except subprocess.TimeoutExpired:
    process.kill()
    print("Command timed out")
except FileNotFoundError:
    print("The command was not found. Check your command or path.")
