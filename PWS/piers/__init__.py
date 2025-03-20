from traceback import print_exc

def nf () : pass
debug = print
trace = print_exc

def set_debug( level ) :
	global debug
	debug = [nf,print][level]
