
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tempfile

options = Options()
arguments = [
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-setuid-sandbox",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--window-size=800,600",
    "--blink-settings=imagesEnabled=false",
    "--disable-extensions",
    "--disable-infobars",
    "--disable-notifications",
    "--disable-software-rasterizer",
]
for argument in arguments:
    options.add_argument(argument)

temp_data_dir = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={temp_data_dir}")
DRIVER = webdriver.Chrome(options=options)