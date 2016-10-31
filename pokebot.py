#!/usr/bin/env python3

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
import logging

import pykache

def query(**kwargs):
	"""
	Receives a dictionary containing the query fields:
		id : The Pokemon ID to retrieve
		name : The Pokemon name to retrieve
	Returns the corresponding pykache.Pokemon.
	"""
	p = None

	try:
		if 'id' in kwargs:
			p = pykache.get_pokemon_by_id(kwargs['id'])
		elif 'name' in kwargs:
			p = pykache.get_pokemon_by_name(kwargs['name'])
		elif 'move_name' in kwargs:
			p = pykache.get_move_by_name(kwargs['move_name'])
		else:
			raise KeyError('A query accepts an id or a name as an argument')

	except ValueError: # Raised by the pykache module if the resource doesn't exist
		return 'El recurso especificado no existe'

	return p.human_readable()

def q_name(bot, update, args):
	message = bot.send_message(chat_id=update.message.chat_id, text='Retomando información...')

	if len(args) != 1:
		response = 'El comando /nombre toma un solo argumento'
	else:
		response = query(name=args[0])

	message.edit_text(text=response)

def q_fuzzy(bot, update):
	search_term = update.message.text
	results = pykache.fuzzy_find(search_term)

	if len(results) == 0:
		bot.send_message(chat_id=update.message.chat_id,
		                 text='No se ha encontrado ninguna coincidencia')
	elif len(results) == 1:
		r = results[0]
		result_type, result_title = r.split(':')
		if result_type == 'pokemon':
			reply = query(name=result_title)
		elif result_type == 'move':
			reply = query(move_name=result_title)

		bot.send_message(chat_id=update.message.chat_id,
		                 text=reply)
	else:
		response =  'Te refieres a...\n'
		inline_keyboard_buttons = list()

		format_result = {
			'pokemon' : 'Pokemon: ',
			'move' : 'Movimiento: ',
		}
		for r in results:
			result_type, result_title = r.split(':')
			button_text = format_result[result_type] + result_title.capitalize()
			button = telegram.InlineKeyboardButton(text=button_text,
			                                       callback_data='{0}'.format(r))
			inline_keyboard_buttons.append([button])
		markup = telegram.InlineKeyboardMarkup(inline_keyboard_buttons)

		bot.send_message(chat_id=update.message.chat_id,
		                 text=response,
						 reply_markup=markup)


def q_id(bot, update, args):
	message = bot.send_message(chat_id=update.message.chat_id, text='Retomando información...')

	if (len(args) != 1) or (not args[0].isdigit()):
		response = 'El comando /numero toma un solo argumento numérico'
	else:
		response = query(id=int(args[0]))

	message.edit_text(text=response)

def pokemon_search_callback(bot,update):
	cb = update.callback_query
	chat_id = cb['message']['chat']['id']
	message = bot.send_message(chat_id=chat_id, text='Retomando información...')
	response = query(name=cb['data'].split(':')[1])
	message.edit_text(text=response)

def move_search_callback(bot,update):
	cb = update.callback_query
	chat_id = cb['message']['chat']['id']
	message = bot.send_message(chat_id=chat_id, text='Retomando información...')
	response = query(move_name=cb['data'].split(':')[1])
	message.edit_text(text=response)

if __name__ == '__main__':
	# Load token
	TOKEN_FILE = 'token.txt'
	TOKEN = ''
	with open(TOKEN_FILE, 'r') as f:
		TOKEN = f.readline().split()[0]

	# Enable logging
	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	                    level=logging.INFO)

	logger = logging.getLogger(__name__)

	# Create the EventHandler and pass the bot's token.
	updater = Updater(TOKEN)

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	dp.add_handler(CommandHandler("nombre", q_name, pass_args=True))
	dp.add_handler(CommandHandler("id", q_id, pass_args=True))
	dp.add_handler(CallbackQueryHandler(pokemon_search_callback, pattern='pokemon:(.*)'))
	dp.add_handler(CallbackQueryHandler(move_search_callback, pattern='move:(.*)'))
	dp.add_handler(MessageHandler(Filters.text, q_fuzzy))

	# Start the Bot
	updater.start_polling()

	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()
