""" 
This Script pull RSS feed from a given address ,parses the last update to find if there are ongoing 
    issues listed in the feed update and output a JSON block
exit codes
 """
import datetime
import requests
import os
import re
import json
import logging
import argparse
import tempfile
import sys
import xml.etree.ElementTree as ET  #This is one of the standart Python tools for parsing XML files. 
from enum import Enum

class IcingaStatus(Enum):
    OK = "OK" # 0 
    WARNING =  "WARNING" # 1
    CRITICAL = "CRITICAL" # 2

# Configure logging
class StatusPageTracker:

    def __init__(self , url ,name = "Statuspage" , event_tag :str ,  time_tag:str ,service_names : list = None , date_format : str = "%Y-%m-%dT%H:%M:%SZ"  ):
        '''
        event_tag |-> time_tag  
        
        :param      event_tag:       If existent, the tag that inidicate an incident
        :param      dat_format:      The date format in the statusapage feed. 
        :param      service_names:   List of the relevant service names that should be monitored.
        
        :returns:   A StatusPageTracker object. 
        '''
        logging.basicConfig(filename='test_log.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.tree  = self.GetXML(name = name , url=url)
        self.event_tag = event_tag
        self.time_tag = time_tag
        self.service_names = service_names
        self.date_format = date_format
        logging.info(f'Object {name} created succesfuly.')


    def GetXML(self , name, url) -> ET:
        ''' Get the RSS feed ''' 
        try:
            currentTime = datetime.datetime.now()
            response = requests.get(url, verify=False)  # False FOR TESTING ONLY
            response.raise_for_status()
            
            if response.status_code == 200:
                xml_content = response.content
                logging.info(f"XML for {name} acquired successfully")
                
                # Use a temporary file to store the XML content
                print(os.getcwd())
                temp_file = tempfile.NamedTemporaryFile(mode='w+b' ,delete=False)
                temp_file.write(xml_content)
                logging.info(f'XML file for {name} downloaded successfully at {currentTime.strftime("%H:%M:%S")}')
                temp_file.close() #In Windows the file has to be closed before opened again, not relevant in Unix
                try:
                    tree = ET.parse(temp_file.name)
                    return tree
                
                except ET.ParseError as parse_error:
                    logging.error(f'Error parsing XML: {parse_error}')
                os.unlink(temp_file)
            
           


            
        except requests.exceptions.RequestException as e:
            logging.error(f'Error during request: {e}')

        except Exception as e:
            print(f"ERROR:  {e}")
            logging.error(f'An error occurred: {e}')



    def ParseFeed(self , time_delta : int  = 1) -> IcingaStatus:
        '''
        
         
        :param      time_delta :     Find incidents that started or updated in that time since now. defaults to 1 min ago.
        :return:    IcingaStatus     enum value indicating the relevant exit code 
        '''
        start_time =  datetime.datetime.now()  - datetime.timedelta(seconds=time_delta) # the time TIME_DELTA seconds ago 
        # TODO - Create an array of string that every owner insert the services they need and than we look for the same strings in the array 
         # Get the root of the XML tree. 
        root = self.tree.getroot()
        # Iterate throgh the events with tag 'event_tag' and 
        full_name_tag  = "{http://www.w3.org/2005/Atom}%s" %  self.event_tag
        full_time_tag = "{http://www.w3.org/2005/Atom}%s" %  self.time_tag
        for event in root.findall(full_name_tag):



        
        


        





if __name__ == '__main__':
    
    '''
    if len(sys.argv) != 5:
        print("Usage:  --name <name> --url <url>")
        sys.exit(0)

    name_index = sys.argv.index('--name')
    url_index = sys.argv.index('--url')
    name = sys.argv[name_index + 1]
    url = sys.argv[url_index + 1]
    '''
    page = StatusPageTracker(name = "elastic" , url= "https://status.elastic.co/history.atom")
    page.ParseFeed(event_tag='".//{http://www.w3.org/2005/Atom}entry"' , service_names=[1])
    