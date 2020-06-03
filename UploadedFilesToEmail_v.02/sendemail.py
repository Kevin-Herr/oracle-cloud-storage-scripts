import smtplib
import subprocess
import hashlib
import base64
import os
import glob
import sys
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

# Importing the variable from the command line to be passed as a year.
contentYear = sys.argv[1]
###
# Modify these based on your needs.
###
MY_ADDRESS = 'email@your.org'
OBJECT_STORAGE_NAMESPACE = 'namespaceidhere'
SMTP_SERVER = 'exch.your.org'
BUCKET_NAME = 'BucketPrefix' + contentYear
FILES_LOCATION = 'D:\\FILES\\' + contentYear
ORACLE_CONFIG_FILE = 'C:\Oracle\.oci\config'

def get_contacts(filename):
    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails

def read_template(filename):
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def failMail(fileList, yearCheck):
    names, emails = get_contacts('contacts.txt') # read contacts
    message_template = read_template('messagefail.txt')

    # set up the SMTP server
    s = smtplib.SMTP(host=SMTP_SERVER, port=25)
    s.starttls()
    ### s.login(MY_ADDRESS, PASSWORD)

    # For each contact, send the email:
    for name, email in zip(names, emails):
        msg = MIMEMultipart()       # create a message

        # add in the actual person name to the message template
        message = message_template.substitute(MISSINGFILES=fileList,ARCHIVEYEAR=yearCheck)

        # Prints out the message body for our sake
        print(message)

        # setup the parameters of the message
        msg['From']=MY_ADDRESS
        msg['To']=email
        msg['Subject']="FAILURE: Oracle: Call Archives"
        msg['X-Priority']="2"
        
        # add in the message body
        msg.attach(MIMEText(message, 'plain'))
        
        # send the message via the server set up earlier.
        s.send_message(msg)
        del msg
        
    # Terminate the SMTP session and close the connection
    s.quit()
	
def successMail(fileList, yearCheck):
    names, emails = get_contacts('contacts.txt') # read contacts
    message_template = read_template('messagesuccess.txt')

    # set up the SMTP server
    s = smtplib.SMTP(host=SMTP_SERVER, port=25)
    s.starttls()
    ### s.login(MY_ADDRESS, PASSWORD)

    # For each contact, send the email:
    for name, email in zip(names, emails):
        msg = MIMEMultipart()       # create a message

        # add in the actual person name to the message template
        message = message_template.substitute(MISSINGFILES=fileList,ARCHIVEYEAR=yearCheck)
		
        # Prints out the message body for our sake
        print(message)

        # setup the parameters of the message
        msg['From']=MY_ADDRESS
        msg['To']=email
        msg['Subject']="Oracle: Call Archive Uploads Successful"
        
        # add in the message body
        msg.attach(MIMEText(message, 'plain'))
        
        # send the message via the server set up earlier.
        s.send_message(msg)
        del msg
        
    # Terminate the SMTP session and close the connection
    s.quit()
	
def main():
	# Pull the year from the command line.
	try:
		if sys.argv[1] is None: # The variable
			print("Variable is None.") 
	except:
		print("Please specify a year.\n\n COMMAND: python "+sys.argv[0]+" yyyy")
	else:
		contentYear = sys.argv[1]
		print(contentYear)
		
		localFilenames = glob.glob(FILES_LOCATION + '\\**', recursive=True)

		queryOracle = subprocess.check_output('oci os object list -ns ' + OBJECT_STORAGE_NAMESPACE + ' -bn ' + BUCKET_NAME + ' --query \"data [*].{Name:\"name\",MD5:\"md5\"}\" --all --output table --config-file ' + ORACLE_CONFIG_FILE, shell=True)
		queryOracle = str(queryOracle).replace(" | ",",").replace("| ","").replace(" |","").replace('\\r',"").replace("+--","").replace("--+","").replace("-","").replace("b'","").replace(" ","").replace("\\nMD5","MD5").replace("\\n\\n","\\n").replace("'","").replace("MD5,Name","")
		queryOracle = queryOracle.split("\\n")
	
		# Get current date.
		now = datetime.datetime.now()
		timeSearch = now.strftime("\\%Y\\%m\\%d\\")
		
		# Check the list that was pulled from Oracle to see which files have or haven't been uploaded.
		strqueryOracle = str(queryOracle)
		notUploaded = "---\n"
		uploadFailure = 0
		for filename in localFilenames:
			if os.path.isfile(filename):
				with open(filename, 'rb') as inputfile:
					data = inputfile.read()
					filename = filename
					filename = str(filename)
					filename = filename.replace(" ","").replace("('","").replace("')","").replace("','",",").replace("\\\\", "\\").replace("\\\\", "\\")
					filenameSplit = filename.split("\\")
					if (strqueryOracle.find(filenameSplit[7]) == -1):
						notUploaded += filename+" not found on Oracle servers.\n"
						if (filename.find(timeSearch) == -1):
							uploadFailure = 1
		if uploadFailure == 0:
			successMail(notUploaded, contentYear)
		else:
			failMail(notUploaded, contentYear)
    
if __name__ == '__main__':
    main()