"""
This module specifies another layer for PokeAPI v2, which stores a cache for the
requests already made.
"""

import requests
import bisect
from sorted_collection import SortedCollection

BASE_URL = "http://pokeapi.co/api/v2/"

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


pokemon_list = list()
pokemon_sorted_id   = SortedCollection(key=lambda poke : poke.id)
pokemon_sorted_name = SortedCollection(key=lambda poke : poke.name)

def insert_pokemon(pokemon):
	index = len(pokemon_list)
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

		p = insert_pokemon(PokemonData(req.json()))
		return p

def get_pokemon_by_name(name):
	"""
	Gets a Pokemon data given its id. Raises ValueError if the name doesn't
	exist. Raises AssertError if the argument is not a string
	"""

	assert type(name) == str, "A Pokemon's name must be a string"

	try:
		return pokemon_sorted_name.find(name)
	except ValueError: # Data not requested
		req = requests.get(BASE_URL + 'pokemon/' + name)
		if req.status_code == 404:
			raise ValueError

		p = insert_pokemon(PokemonData(req.json()))
		return p
