"""
This module specifies another layer for PokeAPI v2, which stores a cache for the
requests already made.
"""

import requests
import bisect
from sorted_collection import SortedCollection

BASE_URL = "http://pokeapi.co/api/v2/"
LOCALE = 'es'

class TypeData:
	"""
	Stores the data dictionary on all the Pokemon Type data returned by PokeAPI.
	This dictionary is the same that is returns by requests.Request.json()
	"""

	def __init__(self, data):
		self.data = data
		self.name = data['name'] # Fetches the name to make searches faster

		# Localised name
		self.l_name = [n['name'] for n in data['names'] if n['language']['name'] == LOCALE][0]

	def get_localised_name(self):
		return self.l_name


class PokemonData:
	"""
	Stores the data dictionary on all the Pokemon data returned by PokeAPI.
	This dictionary is the same that is returns by requests.Request.json()
	"""

	def __init__(self, data):
		""" Creates a Pokemon entry given its data (but doesn't save it)"""
		self.data = data
		self.id = data['id']     # Fetches the id to make searches faster
		self.name = data['name'] # Idem for the name

		# Unpopulated data
		self.types = None # Pokemon's types
		self.l_name = None # Localised name
		self.l_types = None # Localised types' names

	def get_types(self):
		if self.types is None:
			ts = [t['type']['name'] for t in self.data['types']]
			self.types = [get_type_by_name(tn) for tn in ts]
		return self.types

	def get_localised_name(self):
		if self.l_name is None:
			r = requests.get(self.data['species']['url'])
			names = r.json()['names']
			for n in names:
				if n['language']['name'] == LOCALE:
					self.l_name = n['name']

		return self.l_name

	def get_localised_types(self):
		if self.l_types is None:
			self.l_types = [t.get_localised_name() for t in self.get_types()]

		return self.l_types


pokemon_list = list()
pokemon_sorted_id   = SortedCollection(key=lambda poke : poke.id)
pokemon_sorted_name = SortedCollection(key=lambda poke : poke.name)

type_list = list()
type_sorted_name = SortedCollection(key=lambda ptype : ptype.name)

def insert_pokemon(pokemon):
	pokemon_list.append(pokemon)

	# Create indices
	pokemon_sorted_id.insert(pokemon)
	pokemon_sorted_name.insert(pokemon)

def get_pokemon_by_id(id):
	"""
	Gets a Pokemon data given its id. Raises ValueError if the ID doesn't exist.
	Raises AssertError if the value is not an integer.
	"""

	assert type(id) == int, "A Pokemon's ID must be an integer"

	try:
		return pokemon_sorted_id.find(id)
	except ValueError: # Data not requested
		req = requests.get(BASE_URL + 'pokemon/' + str(id))
		if req.status_code == 404:
			raise ValueError

		p = PokemonData(req.json())
		insert_pokemon(p)
		return p

def get_pokemon_by_name(name):
	"""
	Gets a Pokemon data given its name. Raises ValueError if the name doesn't
	exist. Raises AssertError if the argument is not a string
	"""

	assert type(name) == str, "A Pokemon's name must be a string"

	try:
		return pokemon_sorted_name.find(name)
	except ValueError: # Data not requested
		req = requests.get(BASE_URL + 'pokemon/' + name)
		if req.status_code == 404:
			raise ValueError

		p = PokemonData(req.json())
		insert_pokemon(p)
		return p

def insert_type(ptype):
	type_list.append(ptype)

	# Create indices
	type_sorted_name.insert(ptype)

def get_type_by_name(name):
	"""
	Gets a Type data given its id. Raises ValueError if the name doesn't
	exist. Raises AssertError if the argument is not a string.
	"""

	assert type(name) == str, "A Type's name must be a string"

	try:
		return type_sorted_name.find(name)
	except ValueError: # Data not requested
		req = requests.get(BASE_URL + 'type/' + name)
		if req.status_code == 404:
			raise ValueError

		t = TypeData(req.json())
		insert_type(t)
		return t
