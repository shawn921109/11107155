#!/usr/bin/env python3

from hashlib import sha256
from base64 import b64encode 
from sys import argv
from json import load, dumps

def sha (s) :
	sha = sha256()
	sha.update(s.encode('utf8'))
	return b64encode(sha.digest()).decode('ascii')

users = {}
try :
	with open("api/home/users.json","r") as fo :
		users = load(fo)
except Exception as x :
	pass

if argv[2] :
	users[argv[1]] = sha(argv[1]+":"+argv[2])
else :
	del users[argv[1]]

try :
	with open("api/home/users.json","w") as fo :
		fo.write(dumps(users,ensure_ascii=False))
except Exception as x :
	pass
