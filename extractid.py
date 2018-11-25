from __future__ import with_statement
from googleapiclient.discovery import build
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools
import time
import os
import sys
import errno
import random
import datetime
import io
import threading
import glob
from fuse import FUSE, FuseOSError, Operations

# If modifying these scopes, delete the file token.json.

CURRENT_PARENT_ID="root"
root_folder=".backend"

SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
	flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
	creds = tools.run_flow(flow, store)
service = build('drive', 'v3', http=creds.authorize(Http()))




def getidfrompath(self,path):
	path=path.split('/')
	ids=['root']

	for i in range(1,len(path)):
		q="'"+ids[i-1]+"' in parents and name='"+path[i]+"'"
		results = service.files().list(q=q,pageSize=100, fields="files(id)").execute()
		for file in results.get('files', []):
			print file.get('id')
			ids.append(file.get('id'))

	return ids


