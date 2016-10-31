"""
This module specifies another layer for PokeAPI v2, which stores a cache for the
requests already made.
"""

import requests
import bisect
from sorted_collection import SortedCollection
import pickle
import os
import logging

BASE_URL = "http://pokeapi.co/api/v2/"
DATA_DIR = 'data/'
LOCALE = 'es'
DEFAULT_LOCALE = 'en'
VERSION = 'omega-ruby-alpha-sapphire'
ORDERED_STATS = {
	'hp' : 0,
	'attack' : 1,
	'defense' : 2,
	'special-attack': 3,
	'special-defense': 4,
	'speed': 5,
}
MOVE_CLASS_SYMBOL = {
	'physical' : 💥,
	'special' : 🔵,
	'status' : 🔶,
}

logger = logging.getLogger(__name__)

class MoveData:
	"""
	Stores the data dictionary on all the Move's data returned by PokeAPI.
	This dictionary is the same that is returned by requests.Request.json()
	"""
	def __init__(self, data):
		self.data = data
		self.name = data['name'] # Fetches the name to make searches faster

		# Localised name
		self.l_name = [n['name'] for n in data['names'] if n['language']['name'] == LOCALE][0]
		self.move_class = data['damage_class']['name']
		self.flavor_text = None

	def get_localised_name(self):
		return self.l_name

	def get_flavor_text(self):
		if self.flavor_text is None:
			fts = self.data['flavor_text_entries']
			for ft in fts:
				if ft['language']['name'] == LOCALE and \
				   ft['version_group']['name'] == VERSION:

					self.flavor_text = ft['flavor_text']
					break

		return self.flavor_text

	def human_readable(self):
		r = self.get_localised_name() + '\n'

class AbilityData:
	"""
	Stores the data dictionary on all the Pokemon Ability data returned by PokeAPI.
	This dictionary is the same that is returned by requests.Request.json()
	"""

	def __init__(self, data):
		self.data = data
		self.name = data['name'] # Fetches the name to make searches faster

		# Localised name
		self.l_name = [n['name'] for n in data['names'] if n['language']['name'] == LOCALE][0]
		self.flavor_text = None

	def get_localised_name(self):
		return self.l_name

	def get_flavor_text(self):
		if self.flavor_text is None:
			fts = self.data['flavor_text_entries']
			for ft in fts:
				if ft['language']['name'] == LOCALE and \
				   ft['version_group']['name'] == VERSION:

					self.flavor_text = ft['flavor_text']
					break

		return self.flavor_text

# Represents an empty slot (for when a )
class NoAbilityData(AbilityData):
	"""
	Represents an empty ability slot, for when the Pokemon has no hidden
	ability.
	"""
	def __init__(self):
		self.data = None
		self.name = None
		self.l_name = None

class TypeData:
	"""
	Stores the data dictionary on all the Pokemon Type data returned by PokeAPI.
	This dictionary is the same that is returned by requests.Request.json()
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
	This dictionary is the same that is returned by requests.Request.json()
	"""

	def __init__(self, data):
		""" Creates a Pokemon entry given its data (but doesn't save it)"""
		self.data = data
		self.id = data['id']     # Fetches the id to make searches faster
		self.name = data['name'] # Idem for the name

		# Unpopulated data
		self.types = None # Pokemon's types
		self.abilities = None # Pokemon's abilities
		self.h_ability = None # Pokemon's hidden ability
		self.l_name = None # Localised name

	def get_types(self):
		if self.types is None:
			ts = [t['type']['name'] for t in self.data['types']]
			self.types = [get_type_by_name(tn) for tn in ts]
		return self.types

	def get_abilities(self):
		if self.abilities is None:
			ablts = [a['ability']['name'] for a in self.data['abilities'] if not a['is_hidden']]
			ablts = [get_ability_by_name(a) for a in ablts]
			self.abilities = ablts

		return self.abilities

	def get_hidden_ability(self):
		if self.h_ability is None:
			h_ab = [a['ability']['name'] for a in self.data['abilities'] if a['is_hidden']]
			if h_ab: #Pokemon HAS hidden ability
				h_ab = get_ability_by_name(h_ab[0])
			else: #Pokemon does NOT have hidden ability
				h_ab = NoAbilityData()
			self.h_ability = h_ab

		return self.h_ability

	def get_stats(self):
		sts = [(s['stat']['name'], s['base_stat']) for s in self.data['stats']]
		return [s[1] for s in sorted(sts, key=lambda x : ORDERED_STATS[x[0]])]

	def get_localised_name(self):
		if self.l_name is None:
			species_id = self.data['species']['url'].split('/')[-2]
			with open(DATA_DIR + 'pokemon-species/' + species_id, 'rb') as f:
				data = pickle.load(f)
			names = data['names']
			for n in names:
				if n['language']['name'] == LOCALE:
					self.l_name = n['name']
					break

		return self.l_name

	def human_readable(self):
		"""
		Returns the Pokemon data in human readable form, intended to be sent to
		a user.
		"""
		s =  self.get_localised_name() + '\n'
		s += 'Tipos: ' + ', '.join((t.get_localised_name() for t in self.get_types())) + '\n\n'

		# Abilities
		s += 'Habilidades:\n'
		for a in self.get_abilities():
			s += '- {0}: {1}\n'.format(a.get_localised_name(), a.get_flavor_text())

		h_a = self.get_hidden_ability()
		if h_a.name is not None:
			s += '- {0} (Oculta): {1}\n'.format(h_a.get_localised_name(), h_a.get_flavor_text()) # Rellenar
		s += '\n'

		#Stats
		sts = self.get_stats()
		s += 'Estadísticas:\n'
		s += 'PS: {0}\n'.format(sts[0])
		s += 'Ataque: {0}\n'.format(sts[1])
		s += 'Defensa: {0}\n'.format(sts[2])
		s += 'Ataque especial: {0}\n'.format(sts[3])
		s += 'Defensa especial: {0}\n'.format(sts[4])
		s += 'Velocidad: {0}\n'.format(sts[5])

		return s


pokemon_list = list()
pokemon_sorted_id   = SortedCollection(key=lambda poke : poke.id)
pokemon_sorted_name = SortedCollection(key=lambda poke : poke.name)

type_list = list()
type_sorted_name = SortedCollection(key=lambda ptype : ptype.name)

ability_list = list()
ability_sorted_name = SortedCollection(key=lambda ability : ability.name)

move_list = list()
move_sorted_name = SortedCollection(key=lambda move : move.name)

def insert_pokemon(pokemon):
	pokemon_list.append(pokemon)

	# Create indices
	pokemon_sorted_id.insert(pokemon)
	pokemon_sorted_name.insert(pokemon)

def insert_ability(ability):
	ability_list.append(ability)

	#Create indices
	ability_sorted_name.insert(ability)

def insert_move(move):
	move_list.append(move)

	#Create indices
	move_sorted_name.insert(move)

def get_pokemon_by_id(pid):
	"""
	Gets a Pokemon data given its id. Raises ValueError if the ID doesn't exist.
	Raises AssertError if the value is not an integer.
	"""

	assert type(pid) == int, "A Pokemon's ID must be an integer"

	try:
		return pokemon_sorted_id.find(pid)
	except ValueError: # Data not requested
		try:
			f = open(DATA_DIR + 'pokemon/' + str(pid), 'rb')
		except FileNotFoundError:
			raise ValueError # ID doesn't exist
		else:
			data = pickle.load(f)
			f.close()
			p = PokemonData(data)
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
		try:
			f = open(DATA_DIR + 'pokemon/name/' + name, 'rb')
		except FileNotFoundError:
			raise ValueError # Name doesn't exist
		else:
			data = pickle.load(f)
			f.close()
			p = PokemonData(data)
			insert_pokemon(p)
			return p


def insert_type(ptype):
	type_list.append(ptype)

	# Create indices
	type_sorted_name.insert(ptype)

def get_type_by_name(name):
	"""
	Gets a Type data given its name. Raises ValueError if the name doesn't
	exist. Raises AssertError if the argument is not a string.
	"""

	assert type(name) == str, "A Type's name must be a string"

	try:
		return type_sorted_name.find(name)
	except ValueError: # Data not requested
		try:
			f = open(DATA_DIR + 'type/' + name, 'rb')
		except FileNotFoundError:
			raise ValueError # Name doesn't exist
		else:
			data = pickle.load(f)
			f.close()

		t = TypeData(data)
		insert_type(t)
		return t

def get_ability_by_name(name):
	"""
	Gets an Ability data given its name. Raises ValueError if the name doesn't
	exist. Raises AssertError if the argument is not a string.
	"""

	assert type(name) == str, "An ability's name must be a string"

	try:
		return ability_sorted_name.find(name)
	except ValueError: # Data not requested
		try:
			f = open(DATA_DIR + 'ability/name/' + name, 'rb')
		except FileNotFoundError:
			raise ValueError # Name doesn't exist
		else:
			data = pickle.load(f)
			f.close()

		a = AbilityData(data)
		insert_ability(a)
		return a

def get_move_by_name(name):
	"""
	Gets a Move data given its name. Raises ValueError if the name doesn't
	exist. Raises AssertError if the argument is not a string.
	"""

	assert type(name) == str, "A move's name must be a string"

	try:
		return move_sorted_name.find(name)
	except ValueError: # Data not requested
		try:
			f = open(DATA_DIR + 'move/name/' + name, 'rb')
		except FileNotFoundError:
			raise ValueError # Name doesn't exist
		else:
			data = pickle.load(f)
			f.close()

		m = MoveData(data)
		insert_movey(m)
		return m

# Fuzzy find
search_dir = dict()

# Create a list with the Pokemons' localised names
SPECIES_DIR = 'data/pokemon-species/'
files = os.listdir(SPECIES_DIR)
files.remove('name')

for filename in files:
	path = SPECIES_DIR + filename
	with open(path, 'rb') as f:
		data = pickle.load(f)
	localised_name = [n['name'] for n in data['names'] if n['language']['name'] == LOCALE][0]
	varieties = [v['pokemon']['name'] for v in data['varieties']]

	search_dir[localised_name] = varieties

logger.info('Search terms created') #Doesn't work?

def fuzzy_find(term):
	"""
	Performs a fuzzy search in the search_dir given a search term. This term
	is split into keywords and tried to match the registered entries. Returns
	a list of tuples containing the names for matching entries in order	of
	similarity.
	"""
	keywords = [k.lower() for k in term.split()] # Make lowercase for easy comparison

	matches = list()
	for entry in search_dir.keys():
		e = entry.lower()
		if e in keywords:
			matches = search_dir[entry] + matches # Add to beginning
		else:
			for k in keywords:
				if k in e: # If the keyword is a substring of the entry
					matches = matches + search_dir[entry]
					break # Do not check any more keywords (avoid repeated entries)

	return matches
