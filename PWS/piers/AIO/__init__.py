import asyncio
from piers import debug, trace

"""
asynchronous I/O related function or base classes.

EXAMPLE:

async def sig_handler() :
	async for sig in AIO.Signal(captures={SIGINT}).play() :
		print(sig)

add(sig_handler)
play()
"""


def getLoop() :
	"""
	> Async.getLoop() => asyncio.loop
	"""
	try :
		loop = asyncio.get_running_loop()
	except RuntimeError :
		try :
			loop = asyncio.get_event_loop()
		except RuntimeError :
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
	return loop

async def resolve( rv ) :
	"""
	await resolve( promise or value ) => value
	"""
	return (await rv) if asyncio.iscoroutine( rv ) else rv

async def sleep(dur) :
	"""
	await sleep(1.234)
	"""
	await asyncio.sleep(dur)

def add( co=None ) :
	"""
	> add( async_function() ) => awaitable
	> add( [ async_function_1(), async_function_2() ] ) => awaitable
	> add( ) => future(awaitable)
	"""
	if not co :
		f = getLoop().create_future()
	elif isinstance( co, list ) :
		f = asyncio.ensure_future(asyncio.gather( *co ))
	else :
		f = asyncio.ensure_future(co)
	return f

__RUNNING_LOOP__ = None

def play() :
	"""
	> play() # wait all tasks until all finished.
	"""
	global __RUNNING_LOOP__
	async def playing() :
		while True :
			ts = asyncio.all_tasks()
			ts.remove(asyncio.current_task())
			if not ts : 
				break;
			for t in ts :
				try :
					await asyncio.sleep(1)
				except asyncio.CancelledError :
					debug("[I] AIO.play: cancelled")
				except KeyboardInterrupt :
					debug("[I] AIO.play: keyboard interrupted")
				except Exception as e :
					trace(e,"AIO.play:")
				break
			await asyncio.sleep(0)
	if not __RUNNING_LOOP__ :
		__RUNNING_LOOP__ = getLoop()
	if not __RUNNING_LOOP__.is_running() :
		__RUNNING_LOOP__.run_until_complete(playing())

def flush() :
	"""
	> flush() # Cancel all running tasks
	"""
	async def fQ() :
		c = None
		for t in asyncio.all_tasks() : # asyncio.Task.all_tasks()
			if t == asyncio.current_task() : # asyncio.Task.current_task()
				continue
			if c ==  t :
				await asyncio.sleep(1)
			else :
				c = t
				t.cancel()
	asyncio.ensure_future(fQ())
