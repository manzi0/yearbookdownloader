
"""
Script for scraping Chinese provincial statistical yearbook data.
Updated: 20250521

"""


from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import pandas as pd
from io import StringIO
import urllib.request
import urllib.parse
import re
import ast
import sys
import json


# GLOBAL VARIABLES

# Translation filter for cleaning file names: change as necessary.
clean_n = str.maketrans('','','abcdefghijklmnopqrstuvwxyz&.,:;<>?/=#":\n\t ')

# Directory of download URLs (read in from file)
with open("urls.json") as json_file:
    URLs = json.load(json_file)


# FUNCTIONS

def init_sel(path, proxy=False):
    '''Initializes selenium. Sets default browser options.'''
    option = webdriver.ChromeOptions()
    option.add_argument('--disable-blink-features=AutomationControlled')
    option.add_argument("--headless")
    prefs = {"download.default_directory": path}
    option.add_experimental_option("prefs", prefs)
    if proxy:
        option.add_argument(f'--proxy-server={proxy_server}')
    driver=webdriver.Chrome(options=option)
    return driver


def get_path(prov, yr: int):
    '''Defines path for downloads and creates necessary directories'''
    prov_dir = os.path.join(base_dir, prov)
    path = os.path.join(prov_dir, str(yr))
    try:
        os.mkdir(prov_dir)
        print(prov + ' directory created')
    except:
        print(prov + ' directory already exists')
    try:
        os.mkdir(path)
        print(prov + ' ' + str(yr) + ' directory created')
    except:
        print(prov + ' ' + str(yr) + ' directory already exists')
    return path


def get_downloaded(path):
    '''Returns list of files in specified directory.'''
    downloaded = set()
    for file_name in os.listdir(path):
            downloaded.add(file_name[:file_name.rfind('.')])
    return downloaded


def get_pages_std(driver):

    '''Obtains page list for yearbook in standard format'''

    page_list = []
    rename_dict = dict()

    subpages = driver.find_elements(By.XPATH, "//a[@href]")
    for page in subpages:
        if page.get_attribute('href'):
            u = page.get_attribute('href')
            f_raw = u[u.rfind('/')+1:u.rfind('.')]
            f = urllib.parse.unquote_to_bytes(f_raw).decode('utf-8')
            n = page.get_attribute('innerHTML').translate(clean_n).strip()
            page_list.append((u, f))
            rename_dict.update({f: n})
    
    return page_list, rename_dict


def get_pages_ah_06(driver):

    '''Obtains page list for yearbooks in 2006-2022 Anhui format.'''

    frameu = driver.current_url
    root = frameu[:frameu.rfind('/')+1]

    page_list = []
    rename_dict = dict()

    menusoup = driver.find_element(By.XPATH, "//div[@class='dtree']/script").get_attribute('innerHTML')
    items = re.findall(r'd.add(.*);', menusoup)

    for item in items:
        tup = ast.literal_eval(item)
        if tup[3]:
            u = root + tup[3]
            f = u[u.rfind('/')+1:u.rfind('.')]
            n = tup[2]
            page_list.append((u, f))
            rename_dict.update({f: n})
            print("Found page: " + u)

    return page_list, rename_dict


def get_pages_ah_23(driver):
    
    '''Obtains page list for yearbooks in 2023+ Anhui format.'''
  
    page_list = []
    rename_dict = dict()
    url = driver.current_url
    root = url[:url.rfind('/')+1] + 'statics/'

    menusoup = driver.find_element(By.XPATH, '//script[contains(text(),"const contents")]').get_attribute('innerHTML')
    items = re.findall(r'{"index":.*?}', menusoup)

    for item in items:
        d = ast.literal_eval(item.replace(',"opened":false', ''))
        if d['link']:
            u = root + d['link']
            ff = d['link']
            f = ff[:ff.rfind('.')]
            n = d['label']
            page_list.append((u, f))
            rename_dict.update({f: n})

    return page_list, rename_dict


def get_pages_ah_04(driver):

    '''Obtains page list for yearbooks in 2004-05 Anhui format.'''

    page_list = []
    rename_dict = dict()

    driver.switch_to.frame("mainFrame")

    if driver.find_elements(By.XPATH, "//td[@class='menuFont']/a"):
        subpages = driver.find_elements(By.XPATH, "//td[@class='menuFont']/a")
        for page in subpages:
            if page.get_attribute('href'):
                u = page.get_attribute('href')
                f_raw = u[u.rfind('/')+1:u.rfind('.')]
                f = urllib.parse.unquote_to_bytes(f_raw).decode('utf-8')
                n = page.get_attribute('innerHTML').translate(clean_n).strip()
                page_list.append((u, f))
                rename_dict.update({f: n})
    else:
        chapters = driver.find_elements(By.XPATH, "//a[@href]")
        ch_list = []
        for c in chapters:
            if c.get_attribute('href'):
                ch_list.append(c.get_attribute('href'))
        for ch in ch_list:
            driver.get(ch)
            root = ch[:ch.rfind('/')+1]
            subpages = driver.find_elements(By.XPATH, "//a[contains(@href, 'javascript:hf')]")
            for page in subpages:
                soup = page.get_attribute('href').replace('javascript:hf', '')
                cleansoup = urllib.parse.unquote_to_bytes(soup).decode('utf-8')
                tup = ast.literal_eval(cleansoup)
                if tup[0]:
                    u = root + tup[0]
                    f = u[u.rfind('/')+1:u.rfind('.')]
                    n = tup[1]
                    page_list.append((u, f))
                    rename_dict.update({f: n})
    
    return page_list, rename_dict


def get_pages_js(driver):
    
    '''Obtains page list for yearbooks in 2011+ Jiangsu format.'''
    
    # obtain list of subsection urls
    chapters = driver.find_elements(By.XPATH, "//td[@onclick]")
    ch_list = []
    clean_ch = str.maketrans("","","'")
    url = driver.current_url
    root = url[:url.rfind('/')+1]
    for c in chapters:
        suff = c.get_attribute('onclick').replace('location.href=', '').translate(clean_ch)
        ch = root + suff
        ch_list.append(ch)

    # obtain list of subpage urls and names, set up renaming dictionary
    page_list = []
    rename_dict = dict()
    
    for ch in ch_list:
        driver.get(ch)
        subpages = driver.find_elements(By.XPATH, "//a[contains(@href,'nj')]")
        for page in subpages:
            u = page.get_attribute('href')
            f_raw = u[u.rfind('/')+1:u.rfind('.')]
            f = urllib.parse.unquote_to_bytes(f_raw).decode('utf-8')
            n = page.get_attribute('innerHTML').replace('电子表格链接', '').translate(clean_n)
            page_list.append((u, f))
            rename_dict.update({f: n})
    
    return page_list, rename_dict


def get_pages_zj(driver):

    '''Obtains page list for yearbooks in Zhejiang format.'''

    url = driver.current_url

    # for pages in pre-2020 format
    if driver.find_elements(By.XPATH, '//frame[@name="top"]'):
        try:
            driver.switch_to.frame('top')
            print("Identified frame: top")
            contents = driver.find_element(By.XPATH, "//area[contains(@href,'excel')]").get_attribute('href')
            driver.get(contents)
        except:
            print('No excel menu found. Analyzing default menu.')
            driver.get(url)
            driver.switch_to.frame('contents')
        page_list, rename_dict = get_pages_std(driver)
    
    # for pages in 2020+ format (excels already in full-name format, no renaming needed, empty rename_dict returned)
    else:
        subpages = driver.find_elements(By.XPATH, "//li[@class='yb-menu-item']//a")
        page_list = []
        rename_dict = dict()
        for page in subpages:
            u = url[:url.rfind('/')] + page.get_attribute('main')[1:].replace('/html/', '/excel/').replace('.html', '.xlsx')
            f_raw = u[u.rfind('/')+1:u.rfind('.')]
            f = urllib.parse.unquote_to_bytes(f_raw).decode('utf-8')
            page_list.append((u, f))

    return page_list, rename_dict


def download_missing(driver, path, page_list, disable_csv=False, disable_img=False, disable_htmlpage=False):
    
    '''Tabulates missing files and initiates download after user confirmation.'''
    
    downloaded = get_downloaded(path)
    missing = [(u, f) for u, f in page_list if f not in downloaded]

    while len(missing) > 0:

        # prompt for download confirmation
        print("Number of potential targets: " + str(len(page_list)))
        print("Number of files downloaded: " + str(len(downloaded)))
        moreinfo = input("List missing files? (y/n) ")
        if moreinfo == 'y':
            print("Missing: ")
            for u, f in missing:
                print(f + ': ')
                print(u)
        resp = input("Download missing files? (y/n) ")
        if resp != 'y':
                break

        # process subpages
        for u, f in missing:
            process_subpage(driver, path, u, f, disable_csv, disable_img, disable_htmlpage)
                    
        time.sleep(5) #pause to allow completion of downloads

        # update list of missing files
        downloaded = get_downloaded(path)
        missing = [(u, f) for u, f in page_list if f not in downloaded]


def process_subpage(driver, path, u, f, disable_csv=False, disable_img=False, disable_htmlpage=False):
    '''Processes subpage. Depending on contents, saves excel, image, pdf, doc, or html table (as csv).'''
    if '.xls' in u.lower():
        print("Downloading: " + u)
        driver.get(u)
        time.sleep(0.2)
    elif ('.jpg' in u.lower() or '.png' in u.lower() or '.pdf' in u.lower() or '.doc' in u.lower()) and not disable_img:
        print("Saving: " + u)
        try:
            f_add = path + '/' + f + u[u.rfind('.'):]
            urllib.request.urlretrieve(u, f_add)   
        except:
            print('Unable to save: ' + u)
    elif '.htm' in u.lower():
        print("Analyzing page: " + u)
        driver.get(u)
        if driver.find_elements(By.XPATH, "//a[contains(@href,'xls')]"):
            xl = driver.find_element(By.XPATH, "//a[contains(@href,'xls')]").get_attribute('href')
            print("Found excel: " + xl)
            driver.get(xl)
        elif driver.find_elements(By.XPATH, '//table') and not disable_csv:
            # identifies table element by xpath rather than delivering whole page to pandas, as former is often blocked
            try:
                dFsoup = driver.find_element(By.XPATH, '//table').get_attribute('outerHTML')
                dFs = pd.read_html(StringIO(dFsoup))
                print("Found table")
                for dF in dFs:
                    dF.to_csv(path + '/' + f + '.csv', index=False, header=False)
            except:
                print('Unable to scrape table: ' + u)
        elif not disable_htmlpage:
            print('Saving page as html.')
            try:
                file_name = u[u.rfind('/'):]
                f_add = path + file_name
                data = driver.page_source
                with open(f_add, "x") as f:
                    f.write(data)
            except:
                print('Unable to save: ' + u)
    else:
        print('No relevant formats found: ' + u)


def rename(path, rename_dict):
    '''Renames files in download directory based on passed dictionary.'''
    print("Renaming files")
    for file_name in os.listdir(path):
        try:
            source = path + "/" + file_name
            key = file_name[:file_name.rfind('.')]
            ext = file_name[file_name.rfind('.'):]
            if rename_dict[key][0].isdigit():
                destination = path + "/" + rename_dict[key] + ext
            else:
                code = ''.join(c for c in key if c.isdigit())
                destination = path + "/" + code + " " + rename_dict[key] + ext
            os.rename(source, destination)
        except:
            print("Rename failed for " + file_name)


def scrape(prov, yr: int, proxy=False, disable_csv=False, disable_img=False, disable_htmlpage=False):
    
    """Scrapes data based on specified province/year and url.
    Note: Change default directory here."""
    
    # get path and URL
    path = get_path(prov, yr)
    url = URLs[prov][y]

    # initiate browser and move to menu frame
    driver = init_sel(path, proxy)
    print("Loading main page")
    driver.get(url)

    # obtain list of subpage urls and names, set up renaming dictionary
    if driver.find_elements(By.XPATH, "//frame[@name = 'contents']"):
        driver.switch_to.frame('contents')
        print("Identified frame: contents")
        page_list, rename_dict = get_pages_std(driver)
    elif driver.find_elements(By.XPATH, "//ul[@id='foldinglist']") or \
        driver.find_elements(By.XPATH, "//ul[@class='mainlists']"):
        page_list, rename_dict = get_pages_std(driver)
    elif driver.find_elements(By.XPATH, "//frame[@name = 'left']"):
        frameu = driver.find_element(By.XPATH, "//frame[@name = 'left']").get_attribute('src')
        driver.get(frameu)
        print("Identified frame: left")
        if driver.find_elements(By.XPATH, "//div[@class='dtree']/script"):
            page_list, rename_dict = get_pages_ah_06(driver)
        else:
            page_list, rename_dict = get_pages_std(driver)
    elif driver.find_elements(By.XPATH, "//script[contains(text(),'const contents')]"):
        page_list, rename_dict = get_pages_ah_23(driver)
    elif driver.find_elements(By.XPATH, "//frame[@name='mainFrame']"):
        page_list, rename_dict = get_pages_ah_04(driver)
    elif driver.find_elements(By.XPATH, "//iframe"):
        iframe = driver.find_element(By.XPATH, '//iframe').get_attribute('src')
        print("Identified iframe: " + iframe)
        driver.get(iframe)
        if driver.find_elements(By.XPATH, "//td[@onclick]"):
            page_list, rename_dict = get_pages_js(driver)
        else:
            page_list, rename_dict = get_pages_zj(driver)
    else:
        page_list, rename_dict = [], dict()
        print("Unable to detect yearbook format")

    # download missing files if page_list available
    if page_list:
        download_missing(driver, path, page_list, disable_csv, disable_img, disable_htmlpage)
    
    # rename files once all downloads complete if rename_dict available
    if rename_dict:
        ver_rename = input("Rename files? (y/n) ")
        if ver_rename == 'y':
            rename(path, rename_dict)

    driver.close()



# MAIN PROGRAM

print("\nCHINA PROVINCIAL STATISTICAL YEARBOOK DOWNLOADER\n")
print("See readme for usage instructions.\n")

# Set parameters
print("Please provide the requested parameters to initiate your download.")
print("Note: Files will be saved with directory structure 'download_directory > province > year > file'")

base_dir = input("\nPath to download directory (leave empty for current working directory): ")
if not base_dir:
    base_dir = os.getcwd()
while not os.path.exists(base_dir):
    print("Download directory does not exist. Please re-enter: ")
    base_dir = input("Path to download directory (leave empty for current working directory): ")
    if not base_dir:
        base_dir = os.getcwd()

prov = input("\nProvince name (full pinyin, no spaces): ").strip().lower()
while prov not in URLs:
    prov = input("Province name not recognized. Please re-enter or enter 'ls' for list of provinces: ").strip().lower()
    if prov == "ls":
        print(sorted(URLs.keys()))

print("\n" + URLs[prov]["NOTE"])
start = end = 0
while not start:
    years = input("Enter the year or range of years you would like to download ('yyyy' or 'yyyy-yyyy'): ")
    if years.isdigit():
        start = end = int(years)
    else:
        try:
            start, end = (int(y) for y in years.split('-'))
        except:
            print("Unable to parse download year. Please re-enter.")
    
    if start and start < 1998 or end > 2025 or start > end:
        print("Year range invalid. Please enter year or year range between 1999 and current year.")
        start = end = 0

proxy_server = input("\nEnter proxy server (optional): ").strip()

print()
toDownload = [str(y) for y in range(start, end+1)]
i = 0
while i < len(toDownload):
    y = toDownload[i]
    if y in URLs[prov]:
        i += 1
    else:
        print(f"Yearbook URL for {prov} {y} not found.")
        url = input("Please input yearbook URL or 's' to skip year: ").strip()
        if url == "s":
            toDownload.pop(i)
        else:
            URLs[prov][y] = url
            i += 1

# Download
print("Starting download...")
for y in toDownload:
    scrape(prov, int(y), proxy=bool(proxy_server), disable_htmlpage=True)