from piers.AIO.Web import WebHome
from os import path as Path, makedirs
from aiofiles import open as async_open
from json import loads as readJSON, dumps as writeJSON

class H (WebHome.PostHandler) :
	def __init__ (self, args) :
		super().__init__(args)
		self.Root = Path.join(args["Root"], "files")
		makedirs(self.Root,exist_ok=True);
		print("建構")

	def __del__ (self) :
		print("解構")

	async def handle_r (self, args, ss) :
		path=Path.join(self.Root,ss["User"]+"_"+args["N"])
		try :
			assert Path.exists(path), "No such file"
			async with async_open(path,"r") as fo :
				return {"R":"OK","D":readJSON(await fo.read())}
		except Exception as x :
			return {"R":"Failed","D":repr(x)}

	async def handle_w (self, args, ss) :
		path=Path.join(self.Root,ss["User"]+"_"+args["N"])
		try :
			assert ("D" in args), "No data object to save"
			async with async_open(path,"w") as fo :
				await fo.write(writeJSON(args["D"]))
			return {"R":"OK"}
		except Exception as x :
			return {"R":"Failed","D":repr(x)}

	async def handle (self, rio) :
		"""
		{"F":"w","N":"storage_name","D":{...}} => {"R":"OK"}
		{"F":"r","N":"storage_name"} => {"R":"OK","D":{...}}
		"""
		try:
			assert ("User" in rio.Session), "Login required"
			ct, args, hdrs = rio.Req
			assert ("F" in args and "N" in args and args["F"] and args["N"]), "Bad Arguments"
			f = getattr(self, "handle_"+args["F"], None)
			if callable(f) : return rio.JSON(await f(args, rio.Session))
			return rio.JSON({"R":"No such task"})
		except Exception as x :
			return rio.JSON({"R":"Failed","D":repr(x)})

PHMClass=H
