"""
This test starts a preview HTTP server that serves a sample XML file with a new entry created at test runtime.
The test expects a critical exit code from our script.

NOTE:   * Please run the test from the main project folder since all file paths are relative to that.
        * Folder seperator are unix like. 
"""

from http.server import SimpleHTTPRequestHandler, HTTPServer
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import os
import subprocess

### TO REMOVE
def update_xml_file2():
    # Load the existing XML file
    tree = ET.parse("tests/preview_server_files/sample_template.xml")
    root = tree.getroot()

    # Update the 'updated' timestamp with the current time
    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    print(current_time)
    entry = root.find('.//{http://www.w3.org/2005/Atom}entry')
    entry.find('{http://www.w3.org/2005/Atom}updated').text = current_time
    

    # Save the updated XML back to the file
    tree.write("tests/preview_server_files/sample.xml")

    print(f"XML file updated with new timestamp: {current_time}")

    # Sleep for a while to simulate a time difference
    time.sleep(3)  # Sleep for 3 seconds and than run the script

def update_xml_file():
    tree = ET.parse("tests/preview_server_files/sample_template.xml")
    root = tree.getroot()
    entry_tags = root.findall('.//{http://www.w3.org/2005/Atom}entry')
    for entry in entry_tags:
        updated_tag = entry.find('{http://www.w3.org/2005/Atom}updated')
        if updated_tag is not None:
            # Update the content of <updated> tag with the current time
            current_time = datetime.utcnow().isoformat() + 'Z'
            updated_tag.text = current_time
    # Write the xml file with updated time
    with open('preview_server_files'+os.sep+'sample.xml' , 'wb') as f:
        tree.write(f)
        print(f"XML file updated with new timestamp: {current_time}")


# Start an HTTP server to serve the XML file
def start_http_server():
    try:
        port = 9000  # Choose a suitable port
        server_address = ('localhost', port)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        print(f'Serving on port {port}...')
        httpd.server_activate() 
    except KeyboardInterrupt:
        httpd.server_close()
        print('HTTP server stopped.')

# Update the XML file and start the HTTP server
if __name__ == "__main__":
    update_xml_file()
    start_http_server()
    print("now running the script >> ")
    subprocess.run(["python3","modules/xml_parser.py"]) 




