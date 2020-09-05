import requests
from bs4 import BeautifulSoup
from langdetect import detect
from multiprocessing import Pool, Value
import random
import sqlite3

conn = sqlite3.connect("steamgroups.db", isolation_level=None)
conn.execute("CREATE TABLE IF NOT EXISTS SteamGroups(GID INT, Title TEXT, Tag TEXT, Members INT, URL Text, Date TEXT, Language TEXT, Owner TEXT, Level INT, SteamID INT)")

def generate_random_useragent() -> str:
    """
    Generates an authentic-looking user agent with random version numbers
    """
    user_agent = (f"Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.{random.randint(1, 50)} (KHTML, like Gecko) "
                  f"Chrome/{random.randint(60,78)}.0.{random.randint(1000, 4000)}.{random.randint(1, 99)} Safari/{random.randint(535, 540)}.{random.randint(1, 80)} "
                 )
    return user_agent

def parse_owner_information(steamid, headers):
    URL = f"https://steamcommunity.com/profiles/{steamid}?xml=1"
    html = requests.get(URL, headers=headers, timeout=5).text
    soup = BeautifulSoup(html, "html.parser")
    display_name = soup.find("steamid").text
    return str(display_name)

def detect_the_group_language(title):
    return detect(title)

def parse_xml_information(gid, headers):
    URL = f"https://steamcommunity.com/gid/{gid}/memberslistxml/?xml=1"
    html = requests.get(URL, headers=headers, timeout=5).text
    soup = BeautifulSoup(html, "html.parser")
    group_name = soup.find("groupname").text
    group_url = soup.find("groupurl").text
    group_member_count = soup.find("membercount").text
    steamid = soup.find("members").text.strip().split("\n")[0]
    return str(group_name), group_url, group_member_count, steamid
    
def parse_group_tag_and_date(gid, headers):
    URL = f"https://steamcommunity.com/gid/{gid}/"
    html = requests.get(URL, headers=headers, timeout=5).text
    soup = BeautifulSoup(html, "html.parser")
    group_tag = soup.find("span", {"class": "grouppage_header_abbrev"}).text
    group_date = soup.find("div", {"class": "data"}).text
    group_date = group_date.replace(',', '')
    return str(group_tag), group_date

def parse_persona_level(steamid, headers):
    URL = f"https://steamcommunity.com/profiles/{steamid}"
    html = requests.get(URL, headers=headers, timeout=5).text
    soup = BeautifulSoup(html, "html.parser")
    try:
        steamlevel = soup.find("span", {"class": "friendPlayerLevelNum"}).text
        return steamlevel   
    except:
        return "hidden"

def initialize(counter):
    global x 
    x = counter

def dostuff(i):
    fails = open(f"group_db_fails.txt", "a+", encoding="utf-8")    
    try:
        headers = {'User-Agent': generate_random_useragent()}
        group_name, group_url, group_member_count, steamid = parse_xml_information(i, headers)
        group_tag, group_date = parse_group_tag_and_date(i, headers)
        steamlevel = parse_persona_level(steamid, headers)
        display_name = parse_owner_information(steamid, headers)
        group_language = detect_the_group_language(str(group_name))
        conn.execute("INSERT INTO SteamGroups (GID, Title, Tag, Members, URL, Date, Language, Owner, Level, SteamID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (i, group_name, group_tag, group_member_count, group_url, group_date, group_language, display_name, steamlevel, steamid))        
        with x.get_lock():
            x.value +=1
            print('Groups parsed:', x.value, end='\r')
    except:
        fails.write(f"{i}\n")
        pass
     
def main(threads, array):
    x = Value('i', 0)
    with Pool(threads, initializer=initialize, initargs=(x,)) as p:   
        p.map(dostuff, array)
      
if __name__ == "__main__":
    print("github.com/hell")
    threads = int(input("How many threads would you like to use/run?\n"))
    START_GID = int(input("Start GID: "))
    END_GID = int(input("End GID: "))
    array = range(START_GID, END_GID)
    main(threads, array)
