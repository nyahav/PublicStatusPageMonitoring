""" 
This Script pull RSS feed from a given address , the last update to find if there are ongoing 
    issues listed in the feed update and output a JSON block
exit codes
 """
import os
from re import S
import sys
import json
import datetime
import logging
import inspect
import tempfile
import xml.etree.ElementTree as ET
from enum import Enum
from bs4 import BeautifulSoup
import requests
from xmlrpc.client import boolean
from logging.handlers import RotatingFileHandler

class IcingaStatus(Enum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 4 

class StatusPageTracker:
    tag_prefix = ".//{http://www.w3.org/2005/Atom}"
    HelpPage = '''
    This is the help page
    '''

    logger = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler('{}.log'.format('PublicStatusPageMonitor'), maxBytes=100000, backupCount=50)
    script_path = inspect.getfile(inspect.currentframe())
    logger.addHandler(logging.FileHandler(script_path))


    def __init__(self, config_file_path):
            try:
                with open(config_file_path, 'r') as config_file:
                    config_data = json.load(config_file)

                    # Load information from JSON to object fields
                    self.url = config_data["url"]
                    self.name = config_data["name"]
                    self.event_tag = config_data["event_tag"]
                    self.time_tag = config_data["time_tag"]
                    self.service_names = config_data["service_names"]
                    self.date_format = config_data.get("date_format", "%Y-%m-%dT%H:%M:%SZ")

                    # Create ET object from fields 
                    self.tree = self.GetXML()

                    # Create a Python dictionary from the nested object in the JSON file's 'keywords'
                    self.keywords_map = dict(map(lambda keyword: (keyword[0], keyword[1]), config_data["keywords"].items()))
                    logging.info('Object {} StatusPageTracker created successfully.'.format(self.name))

            except FileNotFoundError as e:
                logging.error("Error: the JSON file {} is not found.".format(os.path.basename(config_file_path)))
                # Handle the error as needed

            except json.JSONDecodeError as e:
                logging.error("Error: the file is not a valid JSON file")
                # Handle the error as needed

            

    def GetXML(self) -> ET:
        ''' Get the RSS feed ''' 
        try:
            currentTime = datetime.datetime.now()
            response = requests.get(self.url, verify=False)  # False FOR TESTING ONLY
            response.raise_for_status()
            
            if response.status_code == 200: 
                xml_content = response.content
                logging.info(f"XML for {self.name} acquired successfully")
                
                # Use a temporary file to store the XML content
                temp_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
                temp_file.write(xml_content)
                logging.info(f'XML file for {self.name} downloaded successfully at {currentTime.strftime("%H:%M:%S")}')
                temp_file.close() # In Windows the file has to be closed before opened again, not relevant in Unix
                try:
                    tree = ET.parse(temp_file.name)
                    return tree
                
                except ET.ParseError as parse_error:
                    logging.error(f'Error parsing XML: {parse_error}')
                    # Need to add here lost connection to http server-icinga unknown
                os.unlink(temp_file)
        except requests.exceptions.RequestException as e:
            logging.error(f'Error during request: {e}')

        except Exception as e:
            print(f"ERROR:  {e}")
            logging.error(f'An error occurred: {e}')

    def search_for_strings(self, time_delta) -> list:
        """
        Searches an XML file for the given search strings.

        Args:
          xml_file: The path to the XML file to search.
          search_strings: A list of strings to search for.
          time_delta: The number of seconds ago to start the search.

        Returns:
          A list of entries containing the given search strings.
        """
        service_names = self.service_names
        
        full_time_tag = "{http://www.w3.org/2005/Atom}%s" % self.time_tag
        entries = []
        start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta) #adjust for time zones using ISO 8601

        for entry in self.tree.findall("entry"):
            published = datetime.datetime.strptime(entry.find(full_time_tag).text, "%Y-%m-%dT%H:%M:%SZ")
            if published >= start_time:
                for service in service_names:
                    if service in entry.text:
                        entries.append(entry)
                        break
        # If the keyword is found, sets the icinga_status to the value in the keyword_to_status dictionary that corresponds to the keyword.
        for entry in entries:
            for key_word in self.keywords:
                if key_word in entry.find("description").text:
                    entry.set("icinga_status", self.keyword_to_status[key_word])

        return entries

    def parse_Html_Content(html_content):
        """"
        Using BeautifulSoup to parse the HTML content part of the RSS feed into plain text

        Args:
            content: Label inside the RSS feed

        Returns:
            Only the text inside the label
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

        entries = self.search_for_strings(time_delta)
        new_text = None
        for entry in entries:
            new_text = self.parse_html_content(entry.content)
            print(new_text)
            # TURN ON flag if one or more entry was created in time-delta
            bool = True
        if not bool:
            # No changes have been commited to the statusapge in time-delta
            return IcingaStatus.OK
        else:
            # A new status update was posted to the statuspage and we shuold send an alert
            return IcingaStatus.CRITICAL

if __name__ == '__main__':
    # Change to relative path on local machine-SSA
    config_file_path = "tests/Auto0_statuspPage.json"
    page = StatusPageTracker(config_file_path)
    status = page.Parse_Feed()
    print(status)
