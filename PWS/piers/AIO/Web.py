# apt install python3-aiofiles
# apt install python3-aiohttp

from aiohttp import web,web_request,ClientSession
from aiofiles import open as async_open
from asyncio import CancelledError
from mimetypes import guess_type
from os import path as Path
from re import compile as createRE, fullmatch as matchRE, search as searchRE
from json import loads as parse_json
from time import time
import ssl
import traceback

from piers.Data import JObj, Cache
from piers.AIO import add as addTask

class XI(Exception) :
	def __init__( self, code, msg="") :
		super().__init__( code, msg )

async def httpGET( url ) :
	async with ClientSession() as session:
		async with session.get(url) as resp:
			if resp.status == 200 :
				return await resp.text()
			else :
				return (resp.status,"Failed")

async def httpPOST( url, obj ) :
	async with ClientSession() as session:
		async with session.post(url,json=obj) as resp:
			if resp.status == 200 :
				return await resp.json()
			else :
				return (resp.status,"Failed")

async def httpPUT( url, data ) :
	async with ClientSession() as session:
		async with session.put(url,data=data) as resp:
			if resp.status == 200 :
				return await resp.json()
			else :
				return (resp.status,"Failed")

class RIO: ## {{{

	RE_FilterDirDot = createRE("/\\.+")
	RE_FilterSlashes = createRE("//+")
	RE_MimeTypeJSON = createRE("^(application)/(json)(;.*)?")
	RE_MimeTypeText = createRE("^(text)/(.*)(;.*)?")
	RE_MimeTypeImage = createRE("^(image)/(.*)(;.*)?")
	RE_MimeTypeBytes = createRE("^(application)/(octet-stream)(;.*)?")

	def __init__ (self, req, srv) :
		self.request=req
		self.server=srv
		self.headers=self.server.CORS.copy()
		self.path=RIO.RE_FilterDirDot.sub("/",req.path)
		self.path=RIO.RE_FilterSlashes.sub("/",req.path)
		self.path="/" + ( self.path[1:] if self.path.startswith('/') else self.path )
		self.Req=(None,None,None) ## content-type, body, header
		self.Session={}
		self.server._log_("%s %s %s" % (req.remote,req.method,self.path), 7)

	async def __prepare__ (self) :
		req,opt=self.request, self.server.Options
		if hasattr(req, "content_length") and req.content_length :
			if req.content_length > opt["MAXREQSIZE"] :
				raise XI("OUT_OF_RESOURCE", "Request body too large.")

		ct=req.content_type if hasattr(req, "content_type") else "application/octet-stream"
		if RIO.RE_MimeTypeJSON.match(ct) :
			self.Req=("JSON", await req.json(), req.headers)
		elif RIO.RE_MimeTypeText.match(ct) :
			self.Req=("Text", await req.text(), req.headers)
		else :
			self.Req=(ct, None, req.headers)

	async def read (self) :
		yield await self.request.read()

	async def save (self, path) :
		if not self.ReqBody :
			async with async_open(path, "wb") as fo :
				async for buf in self.read() :
					await fo.write(buf)
		elif "Text" == self.ReqType :
			async with async_open(path, "w", encoding="utf8") as fo :
				await fo.write(self.ReqBody)
		elif "JSON" == self.ReqType :
			async with async_open(path, "w", encoding="utf8") as fo :
				await fo.write(JObj(self.ReqBody).stringify())

	def addHeader (self, name, value) :
		self.headers[name]=value

	def JSON (self, data) :
		return self.Bytes(JObj(data).stringify().encode('utf8'), "application/json")

	def Bytes (self, data, ctype="application/json") :
		return web.Response(body=data, headers=self.headers, content_type=ctype)

	def Redirect (self, url) :
		return web.HTTPFound(url)

	async def File (self, path, mtype=None) :
		try :
			async with async_open(path, "rb") as fd :
				ctype, ec=mtype or guess_type(path)
				if ec : ctype+="; charset="+ec
				self.headers["Content-Type"]=ctype

				rs = web.StreamResponse(status=200, reason="OK", headers=self.headers)
				if web_request.BaseRequest == type(self.request) :
					await rs.prepare(self.request)

				while self.server.Playing :
					buf = await fd.read(self.server.Options["BUFSIZE"])
					if not buf : break
					await rs.write(buf)
			return rs
		except Exception as x :
			return web.HTTPNotFound(text="Error")
## }}}

class Server : ## {{{
	"""
	class XXX (Server) {
		async def _authenticate_ (self, rio) :
			return response or None
		def _log_ (self, message, level=0) :
			...
	}
	s = XXX(
		host = "0.0.0.0:80",
		options = { "BUFSIZE":1048576, "MAXREQ":32, "MAXREQSIZE":8388608 },
		cors = { "Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers":"*" },
		cafiles = None
	)
	await s.play()
	s.stop()
	"""

	def __init__ (
		self, addr,
		options = None,
		cors = None,
		cafiles = None
	) :
		addr = matchRE(r"(.*):(\d+)", addr)
		if not addr : raise Exception("Bad Argument: addr(%s)" % addr)
		self.Host, self.Port = addr.group(1), int(addr.group(2))

		self.Options = {"BUFSIZE":1048576, "MAXREQ":32, "MAXREQSIZE":8388608}
		if options : self.Options.update(options)
		self.CORS = {"Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers":"*"}
		if cors : self.CORS.update(cors)

		self.P = None # TCPSite
		self.Playing = None # Future
		self.LogLevel = 0
		self.ReqCounts = 0
		self.SSLCtx = None
		if cafiles :
			self.SSLCtx = ssl.create_default_context( ssl.Purpose.CLIENT_AUTH )
			self.SSLCtx.load_cert_chain( *cafiles ) # crt,key


	async def _authenticate_ (self, rs) :
		return None
	def _log_ (self, message, level=0) :
		if level > self.LogLevel :
			print("I","[%d]:%s" % (level,message))

	async def _handle_OPTIONS_ (self, rs) :
		return rs.JSON({"R": "OK"})

	async def _handle_POST_ (self, rs) :
		return rs.JSON({"E": "NOT_SUPPORT"})

	async def _handle_GET_ (self, rs) :
		return rs.JSON({"E": "NOT_SUPPORT"})

	async def _handle_PUT_ (self, rs) :
		return rs.JSON({"E": "NOT_SUPPORT"})

	async def __handle__ (self, request) :
		try :
			if self.ReqCounts >= self.Options["MAXREQ"] :
				return web.HTTPTooManyRequests()
			self.ReqCounts += 1
			request._client_max_size = self.Options["BUFSIZE"]
			r = RIO(request, self)
			await r.__prepare__()
			## authenticate
			rs = await self._authenticate_(r)
			if rs != None :
				return rs
			## dispatch
			return await getattr(self, "_handle_"+request.method+"_")(r)
		except web.HTTPException as x :
			return x
		except AttributeError as x :
			self._log_(str(x), level=7)
			return web.HTTPBadRequest(reason="Unhandled Method: "+request.method)
		except CancelledError :
			await self.stop()
			return web.HTTPBadRequest(reason="Cancelled")
		except XI as x :
			self._log_(str(x), level=7)
			return web.HTTPBadRequest(reason=str(x))
		except Exception as x :
			self._log_(str(x), level=7)
			return web.HTTPBadRequest(reason=str(x))
		finally:
			self.ReqCounts -= 1
		return web.HTTPBadRequest(reason="Unhandle Exception")

	async def __aenter__ (self) :
		try :
			self._log_("Init Host: %s, Port: %d" % (self.Host, self.Port), 9)

			runner = web.ServerRunner(web.Server(self.__handle__))
			await runner.setup()

			host = self.Host
			if host.startswith("[") and host.endswith("]") :
				host = host[1:len(host)-1]
			self.P = web.TCPSite(runner, host, self.Port, ssl_context=self.SSLCtx) if self.SSLCtx else web.TCPSite(runner, host, self.Port)
			await self.P.start()
			self._log_("Ready", 9)
		except Exception as e :
			print("Exception 232", e)
			await self.__aexit__(None, None, None)

	async def __aexit__ (self, type, value, traceback) :
		if self.P :
			await self.P.stop()
			self.P = None

	async def play (self) :
		async with self :
			self.Playing=addTask()
			await self.Playing

	def stop (self) :
		self.Playing.set_result(True)
		self.Playing=None
## }}}

class WebService (Server) : ## {{{
	"""
	s = WebService (
		host = "0.0.0.0:80",
		home = "./index.html",
		options = { "BUFSIZE":1048576, "MAXREQ":32, "MAXREQSIZE":8388608 },
		cors = { "Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers":"*" },
		cafiles = None
	)
	s.reg("DC/path/.*",self.FUNCTION)
	"""
	def __init__( self, addr="0.0.0.0:9980", home="./index.html", options=None, cors=None, cafiles=None ) :
		super().__init__( addr, options=options, cors=cors, cafiles=cafiles )
		self.Home = home
		self.APIs = {"GET":set(),"POST":set(),"PUT":set()}
		self.URLPrefixes = {}
		self.Modules = {}

	async def __aexit__( self, type, value, traceback ) :
		await super().__aexit__( type, value, traceback )
		for m in self.Modules :
			self.Modules[m].__release__()

	def reg( self, prefix, handler, method="POST" ) :
		r = (prefix, handler)
		if str == type(prefix) :
			key = method+":"+prefix
			if key in self.URLPrefixes :
				self.APIs[method].remove(self.URLPrefixes[key])
			r = self.URLPrefixes[key] = (createRE(prefix), handler)
		self.APIs[method].add(r)

	def reg_module( self, mod, args={}, prefix="" ) :
		class MH :
			def __init__( self, inst ) :
				self.WS = inst
			async def GET( self, rio ) :
				return await getattr(self.WS, "GET_"+rio.path.group(1))( rio )
			async def POST( self, rio ) :
				return await getattr(self.WS, "POST_"+rio.path.group(1))( rio )
			async def PUT( self, rio ) :
				return await getattr(self.WS, "PUT_"+rio.path.group(1))( rio )
		s,m = mod.WebService(**args), {}
		if hasattr(mod.WebService,"Name") and hasattr(s,"__release__") :
			self.Modules[mod.WebService.Name] = s
		for fn in dir( s ) :
			if fn.startswith("GET_") : m["GET"] = True
			elif fn.startswith("POST_") : m["POST"] = True
			elif fn.startswith("PUT_") : m["PUT"] = True
		if prefix and not prefix.endswith("/") : prefix += "/"
		prefix += mod.WebService.URLPrefix
		if prefix.endswith("/") : prefix = prefix[:-1]
		mh = MH( s )
		for k in m :
			self.reg( prefix+"/([^/]*)/?(.*)", getattr(mh,k), method=k )
		return s

	def __find_api__( self, apis, rio ) :
		for (t,h) in apis :
			m = t.match( rio.path[1:] )
			if m :
				rio.path = m
				return h

	async def _handle_POST_( self, rio ) :
		h = self.__find_api__( self.APIs["POST"], rio )
		if h :
			r = h( rio )
			return (await r) if asyncio.iscoroutine( r ) else r
		return await super()._handle_POST_( rio )

	async def _handle_GET_( self, rio ) :
		h = self.__find_api__( self.APIs["GET"], rio )
		if h :
			r = h( rio )
			return (await r) if asyncio.iscoroutine( r ) else r
		p = Path.abspath(Path.join(self.Root, rio.path[1:]))
		if Path.isdir(p) :
			p = Path.join(p, self.Index)
		return await rio.File(p)
## }}}

class WebHome (Server) : ## {{{
	"""
	s = WebHome (
		host = "0.0.0.0:80",
		home = {"GET":"./GET","POST":"./POST","PUT":"./PUT"},
		pages = {"INDEX":"index.html","ERROR":"error.html"},
		options = {"BUFSIZE":1048576, "MAXREQ":32, "MAXREQSIZE":8388608},
		cors = {"Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers":"*"},
		cafiles = None
	)
	"""

	class PostHandler () :
		def __init__ (self, args) :
			self.Args = args
		def __flush__ (self) :
			pass
		def handle (self, rio) :
			return rio

	def __init__ (
		self, addr, home, pages,
		options = {
			"BUFSIZE":1048576,
			"MAXREQ":32,
			"MAXREQSIZE":8388608,
			"NO_API_CACHE":False
		},
		cors = None,
		cafiles = None
	) :
		super().__init__(addr, options=options, cors=cors, cafiles=cafiles)
		self.Home = home
		self.Pages = pages
		class PHMC(Cache) :
			async def create(self, name) :
				G = { "PHMClass":None }
				async with async_open( name+".py", "r", encoding="utf8" ) as fo :
					exec(await fo.read(), G)
				assert G["PHMClass"], "No such module"
				Arg = {"Root":Path.dirname(name)}
				try :
					async with async_open( name+".json", "r" ) as fo :
						Arg.update(parse_json(await fo.read()))
				except : pass
				print("Reload module",name);
				return (G["PHMClass"](Arg),time())

			async def get(self, name, reload=False) :
				c,t = await super().get(name, reload)
				if not reload and t < Path.getmtime(name+".py") :
					c,t = await super().get(name, True)
				if not callable(getattr(c,"__del__",None)) :
					del self.DB[name]
				return c 
		self.PHMCache = PHMC(32)

	async def _handle_GET_ (self, rio) :
		try :
			p = Path.join(
				self.Home["GET"],
				searchRE("[^/\\\\].*",rio.path).group(0)
			)
		except :
			p = self.Home["GET"]
		if Path.isdir(p) :
			p = Path.join(p, self.Pages["INDEX"])
		return await rio.File(p)

	async def _handle_POST_( self, rio ) :
		try :
			phm = await self.PHMCache.get(Path.join(
				self.Home["POST"],
				searchRE("[^/\\\\].*",rio.path).group(0)
			),reload="NO_API_CACHE" in self.Options and self.Options["NO_API_CACHE"])
			return await phm.handle(rio)
		except Exception as x :
			# print("Exception 399:",x)
			print(traceback.format_exc())
			return rio.JSON({"E": "NO SUCH HANDLER"})
## }}}
