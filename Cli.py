import subprocess

#cd scraper

#scrapy crawl scraping -a topic=<blah> -O sources.json 

#scrapy crawl sources -O sources.json

try:
    topic=input("What topic are you researching? ")
    process = subprocess.Popen(
        [
            "scapy",
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
    stdout, stderr = process.communicate(timeout=15)

    if process.returncode == 0:
        print("Output: ", stdout)
    else:
        print("Error: ", stderr)

except subprocess.TimeoutExpired:
    process.kill()
    print("Command timed out")
except FileNotFoundError:
    print("The command was not found. Check your command or path.")
