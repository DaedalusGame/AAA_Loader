import sys
import os
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_loader
from collections import namedtuple, defaultdict, UserList

HELLO_MY_NAME_IS = "Loader"
MODS_FLAG = "loadmods"

print("Starting up %s" % HELLO_MY_NAME_IS)

Mod = namedtuple("Mod", "name path module_path")

#List of all currently active mods, including their name, path and module path
all_mods = []
#Lookup for modname -> path so I don't have to do a linear search through all mods when making an asset loader
mod_path_lookup = {}

class AssetLoader:
	
	def __init__(self, path):
		self.base_path = path
		
	def get_asset(self, path):
		assert(path)
		assert(isinstance(path, list))
		assert(isinstance(path[0], str))
		
		desired_path = os.path.join(self.base_path, *path)
		relative_path = os.path.relpath(desired_path, os.path.abspath('rl_data'))
		
		return relative_path.split(os.sep)
		
#TODO: Would be good to have a late loading functionality that runs with a customized negotiated order

def is_mod_active(modname):
	return modname in mod_path_lookup

def get_asset_loader(modname):
	return AssetLoader(mod_path_lookup[modname])

#This is a fix for the inability to import RiftWizard directly without using a stack inspection.
import inspect 
stack = inspect.stack()

frm = stack[-1]
RiftWizard = inspect.getmodule(frm[0])
frm = stack[0]
AAA_Loader = inspect.getmodule(frm[0])

class ConstantImporter(MetaPathFinder, Loader):
	def __init__(self, fullname, module):
		self.fullname = fullname
		self.module = module

	def find_spec(cls, fullname, path=None, target=None):
		if(fullname == cls.fullname):
			spec = spec_from_loader(fullname, cls, origin=cls.fullname)
			return spec
		return None

	def create_module(cls, spec):
		return cls.module

	def exec_module(cls, module=None):
		pass

	def get_code(cls, fullname):
		return None

	def get_source(cls, fullname):
		return None

	def is_package(cls, fullname):
		return False


sys.meta_path.insert(0, ConstantImporter("RiftWizard", RiftWizard))
sys.meta_path.insert(0, ConstantImporter("mods.AAA_Loader.AAA_Loader", AAA_Loader))

def discover_mods(mods_path):
	for f in os.listdir(mods_path):
		if not os.path.isdir(os.path.join(mods_path, f)):
			continue
				
		if not os.path.exists(os.path.join(mods_path, f, f + '.py')):
			continue
				
		yield Mod(f, os.path.join(mods_path, f), '.'.join(['mods', f, f]))

def load_mods(path):
	for package in os.listdir(path):
		print("Checking %s for mods..." % package)
		
		mods_path = os.path.join(path, package, 'mods')
		
		if not os.path.isdir(mods_path):
			print("%s is not a valid directory, skipping" % mods_path)
			continue
			
		sys.path.append(os.path.join(path, package))
			
		for mod in discover_mods(mods_path):
			print("Found %s (%s)" % (mod.name, mod.path))
			all_mods.append(mod)

def complain_about_duplicates():
	check_set = defaultdict(list)
	for mod in all_mods:
		check_set[mod.module_path].append(mod)
	for key, group in check_set.items():
		if len(group) > 1:
			print("WARNING: Found duplicate module path %s (%d duplicates). Only one will be loaded." % (key, len(group)))
	#We could also just crash at this point.
			
def import_mod(mod):
	print("Loading %s (%s)" % (mod.name, mod.path))
	if not mod.name in imported_mods:
		imported_mods.append(mod.name)
	if mod.module_path in sys.modules:
		print("Already loaded, skipping")
		return
	module = import_module(mod.module_path)

#Add all mods from the base game mod folder
print("Checking base game mod folder for mods...")
for mod in discover_mods("mods"):
	print("Found %s (%s)" % (mod.name, mod.path))
	all_mods.append(mod)

#If the startup flag is set, find mods from the specified path
if MODS_FLAG in sys.argv:
	mods_path = sys.argv[sys.argv.index(MODS_FLAG) + 1]
	
	print("Found mod sideloading path: %s" % mods_path)
	
	load_mods(mods_path)
	
complain_about_duplicates()

for mod in all_mods:
	if not mod.name in mod_path_lookup:
		mod_path_lookup[mod.name] = mod.path

#Readonly list type for stopping duplicate mod list entries in crashlogs
class ReadOnlyList(UserList):
	def append(*args, **kwargs):
		pass
		
from importlib import import_module
	
imported_mods = []
	
for mod in all_mods:
	import_mod(mod)
	
RiftWizard.loaded_mods = ReadOnlyList(imported_mods)
		
print("%s Loaded" % HELLO_MY_NAME_IS)