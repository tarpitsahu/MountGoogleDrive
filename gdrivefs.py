#!/usr/bin/env python
#from __future__ import print_function
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


class Passthrough(Operations):
	def __init__(self, root):
		print "Init Called : ",root
		self.root = root

	# Helpers
	# =======

	def _full_path(self, partial):
		partial = partial.lstrip("/")
		path = os.path.join(self.root, partial)
		return path

	# Filesystem methods
	# ==================

	def show_files(self,parentid,full_path):
		global service
		print "show_files : ",full_path
		try:
			full_path=full_path.rstrip('/')
			files = glob.glob(full_path)
			for f in files:
			    os.remove(f)
		except Exception as e:
			pass

		print "1"
		try:	
			results = service.files().list(q="'"+parentid+"' in parents",pageSize=100, fields="files(id, name, mimeType)").execute()
			items = results.get('files', [])
			print "2"
			if not items:
				print 'No files found.'
			else:
				print 'Files:'
				for item in items:
					try:
						print "Name : ",item['name'],"\nId : ",item['id'],"\n"
						if item['mimeType']=="application/vnd.google-apps.folder":
							os.mkdir(full_path+"/"+item['name']) 
						else:
							os.mknod(full_path+"/"+item['name']) 
					except:
						pass

		except Exception as e:
			print e


	def access(self, path, mode):
		global service
		full_path = self._full_path(path)

		print "access called : ",full_path
		
	
		if not os.access(full_path, mode):
			raise FuseOSError(errno.EACCES)

	def chmod(self, path, mode):
		print "chmod called : ",path
		full_path = self._full_path(path)
		return os.chmod(full_path, mode)

	def chown(self, path, uid, gid):
		print "chown called : ",path
		full_path = self._full_path(path)
		return os.chown(full_path, uid, gid)

	def getattr(self, path, fh=None):
		# print "getattr called : ",path
		full_path = self._full_path(path)
		st = os.lstat(full_path)
		return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
					 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

	def readdir(self, path, fh):
		
		full_path = self._full_path(path)
		print "readir : ",full_path

		if(full_path!=".backend/"):
			print "Here"
			try:
				req_id=self.getidfrompath(full_path)		
			except Exception as e:
				print "readdir : ",e

		else:
			req_id='root'

		print "req_id", req_id
		self.show_files(req_id,full_path)



		dirents = ['.', '..']
		if os.path.isdir(full_path):
			dirents.extend(os.listdir(full_path))
		for r in dirents:
			yield r

	def readlink(self, path):
		print "readlink called : ",path
		pathname = os.readlink(self._full_path(path))
		if pathname.startswith("/"):
			# Path name is absolute, sanitize it.
			return os.path.relpath(pathname, self.root)
		else:
			return pathname

	def mknod(self, path, mode, dev):
		print "mknod called : ",path
		return os.mknod(self._full_path(path), mode, dev)

	def rmdir(self, path):
		print "rmdir called : ",path
		full_path = self._full_path(path)
		return os.rmdir(full_path)

	def mkdir(self, path, mode):
		print "mkdir called : ",path
		return os.mkdir(self._full_path(path), mode)

	def statfs(self, path):
		print "statfs called : ",path
		full_path = self._full_path(path)
		stv = os.statvfs(full_path)
		return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
			'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
			'f_frsize', 'f_namemax'))

	def unlink(self, path):
		print "ulink called : ",path
		return os.unlink(self._full_path(path))

	def symlink(self, name, target):
		print "symlink called : ",path
		return os.symlink(name, self._full_path(target))

	def rename(self, old, new):
		print "rename called : ",path
		return os.rename(self._full_path(old), self._full_path(new))

	def link(self, target, name):
		print "link called : ",path
		return os.link(self._full_path(target), self._full_path(name))

	def utimens(self, path, times=None):
		print "utimens called : ",path
		return os.utime(self._full_path(path), times)

	# File methods
	# ============

	def open(self, path, flags):
		print "open called : ",path
		full_path = self._full_path(path)
		return os.open(full_path, flags)

	def create(self, path, mode, fi=None):
		print "create called : ",path
		full_path = self._full_path(path)
		return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

	def read(self, path, length, offset, fh):
		print "read called : ",path
		os.lseek(fh, offset, os.SEEK_SET)
		return os.read(fh, length)

	def write(self, path, buf, offset, fh):
		print "write called : ",path
		os.lseek(fh, offset, os.SEEK_SET)
		return os.write(fh, buf)

	def truncate(self, path, length, fh=None):
		print "truncate called : ",path
		full_path = self._full_path(path)
		with open(full_path, 'r+') as f:
			f.truncate(length)

	def flush(self, path, fh):
		print "flush called : ",path
		return os.fsync(fh)

	def release(self, path, fh):
		print "release called : ",path
		return os.close(fh)

	def fsync(self, path, fdatasync, fh):
		print "fsync called : ",path
		return self.flush(path, fh)

	def getidfrompath(self,path):
		try:
			path=path.split('/')
			ln=len(path)
			ids=['root']
			for i in range(1,len(path)):
				q="'"+ids[i-1]+"' in parents and name='"+path[i]+"'"
				results = service.files().list(q=q,pageSize=100, fields="files(id)").execute()
				for file in results.get('files', []):
					print file.get('id')
					ids.append(file.get('id'))

			return ids[ln-1]
		except Exception as e:
			print "getidfrompath",e

def main(mountpoint):
	FUSE(Passthrough(root_folder), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
	main(sys.argv[1])