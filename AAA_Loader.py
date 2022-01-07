import sys
import os
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_loader
from collections import namedtuple, defaultdict, UserList

HELLO_MY_NAME_IS = "Loader"
MODS_FLAG = "loadmods"

print("Starting up %s" % HELLO_MY_NAME_IS)

Mod = namedtuple("Mod", "name path module_path")

all_mods = []

#This is a fix for the inability to import RiftWizard directly without using a stack inspection.
import inspect 

frm = inspect.stack()[-1]
RiftWizard = inspect.getmodule(frm[0])

class RiftWizardImporter(MetaPathFinder, Loader):
	def find_spec(cls, fullname, path=None, target=None):
		if(fullname == "RiftWizard"):
			spec = spec_from_loader(fullname, cls, origin="RiftWizard")
			return spec
		return None

	def create_module(cls, spec):
		return RiftWizard

	def exec_module(cls, module=None):
		pass

	def get_code(cls, fullname):
		return None

	def get_source(cls, fullname):
		return None

	def is_package(cls, fullname):
		return False


sys.meta_path.insert(0, RiftWizardImporter())

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

class ReadOnlyList(UserList):
	def append(*args, **kwargs):
		pass
		
from importlib import import_module
	
imported_mods = []
	
for mod in all_mods:
	print("Loading %s (%s)" % (mod.name, mod.path))
	imported_mods.append(mod.name)
	if mod.module_path in sys.modules:
		print("Already loaded, skipping")
		continue
	import_module(mod.module_path)
	
RiftWizard.loaded_mods = ReadOnlyList(imported_mods)
		
print("%s Loaded" % HELLO_MY_NAME_IS)