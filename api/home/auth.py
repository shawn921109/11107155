from piers.AIO.Web import WebHome
from hashlib import sha256
from base64 import b64encode 
from time import time
from os import path as Path
from aiofiles import open as async_open
from json import loads as readJSON, dumps as writeJSON

def sha (s) :
	sha = sha256()
	sha.update(s.encode('utf8'))
	return b64encode(sha.digest()).decode('ascii')

class H (WebHome.PostHandler) :
	def __init__ (self, args) :
		super().__init__(args)
		self.Root=args["Root"]
		self.UserTable=None

	def __del__ (self) :
		pass

	async def querySecret (self, uid) :
		while True :
			if self.UserTable :
				return self.UserTable[uid] if uid in self.UserTable else None
			try :
				async with async_open(Path.join(self.Root,"users.json"),"r",encoding="utf8") as fo :
					self.UserTable=readJSON(await fo.read())
			except :
				break
		return None
		
	async def handle (self, rio) :
		"""
		[Request]  curl --json '{"A":"porshenlai"}' http://localhost/auth
		[Response] {"R":"OK","A":{"A":"porshenlai","T":"TS"}}
				   {"R":"FAIL","A":"Error Message"}

		[Request]  curl --json '{"A":"porshenlai","T":"TS","S":"1234"}' http://localhost/auth
		[Response] {"R":"OK","A":{"A":"porshenlai","SK":"SK"}}
				   {"R":"FAIL","A":"Error Message"}
		"""
		# assert "N" in rio.Session, "Violation"
		# print("path",rio.path)
		# s, dbn=[], rio.path.group(2)
		ct, arg, hdrs=rio.Req
		if not "A" in arg :
			return rio.JSON({"R":"FAIL","A":"發生錯誤"})
		if "S" in arg :
			if "S" in arg :
				if "T" in arg :
					secret = await self.querySecret(arg["A"])
					if secret and sha(arg["A"]+":"+arg["T"]+":"+secret) == arg["S"] : ## authenticate
						return rio.JSON({"R":"OK","A":{
							"A":arg["A"],
							"SK":"{0:s}:{1:s}:{2:s}".format(
								arg["A"],
								arg["T"],
								sha(":".join([arg["A"],arg["T"],rio.server.MasterKey]))
							)
						}})
					else :
						return rio.JSON({"R":"FAIL","A":"認證失敗"})
				else : ## passwd
					if "User" not in rio.Session :
						return rio.JSON({"R":"FAIL","A":"NOT LOGIN"})
					await self.querySecret(arg["A"])
					self.UserTable[arg["A"]] = arg["S"]
					async with async_open(Path.join(self.Root,"users.json"),"w",encoding="utf8") as fo :
						await fo.write(writeJSON(self.UserTable,ensure_ascii=False))
					return rio.JSON({"R":"OK","A":[arg["A"],arg["S"]]})
			else :
				return rio.JSON({"R":"FAIL","A":"發生錯誤"})
		else : ## request_login
			ts = b64encode(int((time()%3600)*1000).to_bytes(3)).decode('ascii')
			return rio.JSON({"R":"OK","A":{ "A":arg["A"], "T":ts }})
			
PHMClass=H
