
""" 
This Script pull RSS feed from a given address , the last update to find if there are ongoing 
    issues listed in the feed update and output a JSON block
exit codes
 """
import os
import sys
import json
import datetime
import logging
import tempfile
from typing import Self
import xml.etree.ElementTree as ET
from enum import Enum
from bs4 import BeautifulSoup
import requests
from xmlrpc.client import boolean
from logging.handlers import RotatingFileHandler


import xml.etree.ElementTree as ET  #This is one of the standard Python tools for parsing XML files. 
from enum import Enum
from logging.handlers import RotatingFileHandler

#classify the severity of the Incident
class IcingaStatus(Enum):
    OK = "OK" # 0 
    WARNING =  "WARNING" # 1
    CRITICAL = "CRITICAL" # 2


class StatusPageTracker:
  # The log file will be rotated when it reaches 100,000 bytes. 
  # The backupCount parameter specifies the number of old log files to keep. In this case, we will keep 50 old log files.
  tag_prefix = ".//{http://www.w3.org/2005/Atom}" #Tag prefix 
  HelpPage = '''
  This is the help page
  '''
  
  logger = logging.getLogger()
  handler = logging.handlers.RotatingFileHandler(f'PublicStatusPageMonitor.log', maxBytes=100000, backupCount=50)
  logger.addHandler(handler)
  def __init__(Self ,config_file_path : os.path ):
      '''
      event_tag |-> time_tag  
      
      :param      event_tag:       If existent, the tag that inidicate an incident
      :param      dat_format:      The date format in the statusapage feed. 
      :param      service_names:   List of the relevant service names that should be monitored.
      
      :returns:   A StatusPageTracker object. 
      '''
  try:
     with open(config_file_path, 'r') as config_file:
      config_data = json.load(config_file)

      # Load information from JSON to object fields
      Self.url = config_data["url"]
      Self.name = config_data["name"]
      Self.event_tag = config_data["event_tag"]
      Self.time_tag = config_data["time_tag"]
      Self.service_names = config_data["service_names"]
      Self.date_format = config_data.get("date_format", "%Y-%m-%dT%H:%M:%SZ")

      # Create a Python dictionary from the nested object in the JSON file's 'keywords'
      Self.keywords_map = dict(map(lambda keyword: (item[0], item[1]), config_data["keywords"].items()))

  except FileNotFoundError as e:
    print(f"Error: the JSON file {os.path.basename(config_file_path)} is not found.")
    logging.error(f"Error: the JSON file {os.path.basename(config_file_path)} is not found.")

  except json.JSONDecodeError as e:
    print("Error: the file is not a valid JSON file")
    logging.error("Error: the file is not a valid JSON file")

  logging.info(f'Object {Self.name} created successfully.')



  def GetXML(Self , name, url) -> ET:
      ''' Get the RSS feed ''' 
      try:
          currentTime = datetime.datetime.now()
          response = requests.get(url, verify=False)  # False FOR TESTING ONLY
          response.raise_for_status()
          
          if response.status_code == 200: 
              xml_content = response.content
              logging.info(f"XML for {name} acquired successfully")
              
              # Use a temporary file to store the XML content
              temp_file = tempfile.NamedTemporaryFile(mode='w+b' ,delete=False)
              temp_file.write(xml_content)
              logging.info(f'XML file for {name} downloaded successfully at {currentTime.strftime("%H:%M:%S")}')
              temp_file.close() #In Windows the file has to be closed before opened again, not relevant in Unix
              try:
                  tree = ET.parse(temp_file.name)
                  return tree
              
              except ET.ParseError as parse_error:
                  logging.error(f'Error parsing XML: {parse_error}')
                  #need to add here lost connection to http server-icinga unknown
              os.unlink(temp_file)
      except requests.exceptions.RequestException as e:
          logging.error(f'Error during request: {e}')

      except Exception as e:
          print(f"ERROR:  {e}")
          logging.error(f'An error occurred: {e}')

  def search_for_strings(Self ,time_delta) -> list:
    """
    Searches an XML file for the given search strings.

    Args:
      xml_file: The path to the XML file to search.
      search_strings: A list of strings to search for.
      time_delta: The number of seconds ago to start the search.

    Returns:
      A list of entries containing the given search strings.
    """
    service_names = Self.service_names
    
    full_time_tag = "{http://www.w3.org/2005/Atom}%s" % Self.time_tag
    entries = []
    start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta) #adjust for time zones using ISO 8601

    for entry in Self.tree.findall("entry"):
      published = datetime.datetime.strptime(entry.find(full_time_tag).text, "%Y-%m-%dT%H:%M:%SZ")
      if published >= start_time:
        for service in service_names:
          if service in entry.text:
            entries.append(entry)
            break
    #If the keyword is found,sets the icinga_status to the value in the keyword_to_status dictionary that corresponds to the keyword.
    for entry in entries:
      for key_word in Self.keywords:
        if key_word in entry.find("description").text:
          entry.set("icinga_status", Self.keyword_to_status[key_word])

      return entries

   

  def parse_Html_Content(html_content):
    """"
    using BeautifulSoup to parser the html content part of the RSS feed into plain text

    Args:content label inside the rss feed

    Returns:only the text inside the label
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.find_all(text=True)
    return ' '.join(text)
      

  def Parse_Feed(self, time_delta=1) -> IcingaStatus:
    
    """
    Parses an XML feed for incidents that started or updated in the last TIME_DELTA seconds.

    Args:
      time_delta: The number of seconds ago to start the search.

    Returns:
      An IcingaStatus enum value indicating the relevant exit code.
    """
    bool = False
    start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta)

    entries = Self.search_for_strings(time_delta)
    new_text = None
    for entry in entries:
       new_text = Self.parse_html_content(entry.content)
       print(new_text)
       bool = True
    if not bool:
      IcingaStatus=3 
    return IcingaStatus.OK


if __name__ == '__main__':
  
    #change to relative path on local machine-SSA
    config_file_path="C:\Users\yahavn\PublicStatusPageMonitoring\tests\Auto0_statuspPage.json"
   
    page = StatusPageTracker(config_file_path)
    page.ParseFeed()
    