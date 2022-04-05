from tinydb import TinyDB, Query   
from threading import Timer
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from requests.exceptions import ConnectionError
from telebot import types
from flask import Flask, request
import requests
import bs4
import lxml
import os
import re
import telebot
import telepot
import time
import json

bot_token = "XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
bot = telebot.TeleBot(token = bot_token)
server = Flask(__name__)

db = TinyDB("product.json")
User = Query()
json_data = json.load(open("product.json"))


def upload_json_file():
    url = "https://api.jsonbin.io/b/5f38dedbaf209d1016bc6ea3"
    headers = {"secret-key": "$2b$10$wpEWftP/FgAhxd1Q8aByBOPKCbWvyUyNiSQgyIrcYuC6OwB4Au57G", "versioning": "false"} 
    json_data = json.load(open("product.json"))
    res = requests.put(url, json=json_data, headers=headers)

    Timer(43200, upload_json_file).start()

upload_json_file()


def get_json_file():
	json_file = json.load(open("product.json"))
	if len(str(json_file)) <= 744:
		url = "https://api.jsonbin.io/b/5f38dedbaf209d1016bc6ea3/latest"
		headers = {"secret-key": "$2b$10$wpEWftP/FgAhxd1Q8aByBOPKCbWvyUyNiSQgyIrcYuC6OwB4Au57G", "versioning": "false"}
		res = requests.get(url, headers=headers)
		data = json.loads(res.text)
		with open("product.json", "w") as jsonFile:
			json.dump(data, jsonFile)
	
	Timer(60, get_json_file).start()

get_json_file()

@bot.message_handler(commands = ["start"])
def send_welcome(message):
	bot.send_message(message.from_user.id, "Benvenuto! Io sono EbayPrices e posso aiutarti a tracciare i prezzi dei prodotti eBay che ti interessano. Inviami l'indirizzo link di un prodotto eBay per iniziare!", parse_mode = "HTML")


@bot.message_handler(commands = ["help"])
def send_help(message):
	bot.send_message(message.from_user.id, "Ciao, io sono EbayPrices e posso aiutarti a tenere traccia dei prodotti eBay che ti interessano, quando un prodotto cambia di prezzo verrai informato tramite un messaggio" + "\n\n" + "Usa /start per iniziare ad usare EbayPrices" + "\nUsa /help per ottenere informazioni utili riguardanti il bot" + "\nUsa /list per ottenere la lista dei prodotti che stai tracciando" + "\nUsa /delete per eliminare i prodotti che vuoi smettere di tracciare" + "\n\nSe trovi un bug segnalalo a @Giorgio_Papini", parse_mode = "HTML")


product_list = []

@bot.message_handler(func = lambda message: message.text is not None and "https://www.ebay" in message.text)
def send_about(message):
	with open("product.json", "r") as jsonFile:
		data = json.load(jsonFile)
		user_id = message.from_user.id
		url_e = message.text
		is_in_db = False
		for ele in data["_default"]:
			if data["_default"][str(ele)]["User_id"] == str(user_id) and data["_default"][str(ele)]["Url"] == str(url_e):
				is_in_db = True
		if is_in_db == True:
			bot.send_message(user_id, "🚫 Stai già tracciando questo prodotto, non puoi monitorare due prodotti identici 🚫", parse_mode = "HTML")
		else:
			res_e = requests.get(url_e)
			soup_e = bs4.BeautifulSoup(res_e.text, "lxml")
			price_e = soup_e.select("#prcIsum")
			title_e = soup_e.find(id="itemTitle")
			garanzia = soup_e.find_all("div", class_="vi-swc-header")
			ebay_premium = "❌"
			if len(garanzia) >= 2:
				ebay_premium = "✅"
				real_garanzia = re.split(">|<", str(garanzia))[6].lower().capitalize()
			else:
				try:
					real_garanzia = re.split(">|<", str(garanzia))[2].lower().capitalize()
				except IndexError:
					real_garanzia = "❌"
			image_html = soup_e.find(id = "icImg")
			conditions_e = soup_e.find(id="vi-itm-cond")
			real_price_e = ""
			real_title_e = []
			for child in title_e:
				real_title_e.append(child)
			real_title_e = real_title_e[1]
			for i in soup_e.select("#prcIsum"):
				real_price_e = (i.text)
			json_price_in = re.split(" |,", real_price_e)[1] + "." + re.split(" |,", real_price_e)[2]
			coin = re.split(" |,", real_price_e)[0]
			result ="<b>" + str(real_title_e) + "</b>" + "\n" + "\n💰 Prezzo -> " + str(json_price_in) + " " + str(coin) + "\n\n🧾 Garanzia -> " + str(real_garanzia) + "\n\n🚚 Servizio eBay Premium -> " + str(ebay_premium) + "\n\n📦 Condizioni del prodotto -> " + str(conditions_e.text)
			product = db.insert({"Name": str(real_title_e), "Price": str(json_price_in), "Coin": str(coin), "Url":url_e, "User_id": str(user_id)})
			bot.send_photo(parse_mode = "HTML", photo = image_html["src"], chat_id = user_id, caption = str(result))


@bot.message_handler(commands = ["list"]) 
def send_list(message):
	user_id = message.from_user.id
	user_products = db.search(User.User_id == str(user_id))
	with open("product.json", "r") as jsonFile:
		data = json.load(jsonFile)
		try:
			num_of_prud = 0
			h = 0 
			for ele in list(data["_default"]):
				if data["_default"][str(ele)]["User_id"] == user_products[int(h)]["User_id"]:
					num_of_prud = num_of_prud + 1
					h = h + 1
		except IndexError:
			h = 0
		if num_of_prud == 0:
			bot.send_message(user_id, "🔗 Non stai tracciando prodotti, inviami un link eBay per iniziare 🔗", parse_mode = "HTML")
		else: 
			try:
				product_num = 0
				j = 0
				try:
					for ele in list(data["_default"]):
						if data["_default"][str(ele)]["User_id"] == user_products[int(j)]["User_id"]:
							j = j + 1
							product_num = product_num + 1
				except IndexError:
					product_num = 1
					j = 0
				bot.send_message(user_id, "🗂️ Stai tracciando " + str(product_num) +" prodotti 🗂️", parse_mode = "HTML") 
				i = 0
				for key in data["_default"]:
					if data["_default"][str(key)]["User_id"] == user_products[int(i)]["User_id"]:
						res = requests.get(data["_default"][str(key)]["Url"])
						soup = bs4.BeautifulSoup(res.text, "lxml")
						image_html = soup.find(id = "icImg")
						price = soup.select("#prcIsum")
						garanzia = soup.find_all("div", class_="vi-swc-header")
						ebay_premium = "❌"
						if len(garanzia) >= 2:
							ebay_premium = "✅"
							real_garanzia = re.split(">|<", str(garanzia))[6].lower().capitalize()
						else:
							try:
								real_garanzia = re.split(">|<", str(garanzia))[2].lower().capitalize()
							except IndexError:
								real_garanzia = "❌"
						conditions = soup.find(id="vi-itm-cond")
						real_price = ""
						for ele in soup.select("#prcIsum"):
							real_price = (ele.text)
						json_price_in = re.split(" |,", real_price)[1] + "." + re.split(" |,", real_price)[2]
						link_click_here =  "<a href =" + "'" + str(data["_default"][str(key)]["Url"])+ "'" + ">Clicca qui per acquistarlo</a>"
						bot.send_photo(parse_mode = "HTML", photo = image_html["src"], chat_id = user_id, caption = "<b>" + str(data["_default"][str(key)]["Name"]) + "</b>" + "\n" + "\n💰 Prezzo -> " + str(json_price_in) + " " + str(data["_default"][str(key)]["Coin"]) + " " + "\n\n🧾 Garanzia -> " + str(real_garanzia) + "\n\n🚚 Servizio eBay Premium -> " + str(ebay_premium) + "\n\n📦 Condizioni del prodotto -> " + str(conditions.text) + "\n\n" + "💸 " + link_click_here + " 💸")
						i = i + 1
			except IndexError:
				i = 0


@bot.message_handler(commands = ["delete"]) 
def show_keyboard(message):
	user_id = message.from_user.id
	user_products = db.search(User.User_id == str(user_id))
	with open("product.json", "r") as jsonFile:
		data = json.load(jsonFile)
		j = 0
		product_num = 0
		try:
			for ele in list(data["_default"]):
				if data["_default"][str(ele)]["User_id"] == user_products[int(j)]["User_id"]:
					product_num = product_num + 1
					j = j + 1
		except IndexError:
			j = 0
		if product_num == 0:
			bot.send_message(user_id, "🔗 Non stai tracciando prodotti, mandami un link eBay per iniziare 🔗", parse_mode = "HTML")
		else:
			keyboard = telebot.types.InlineKeyboardMarkup()  
			i = 0
			try:
				for ele in list(data["_default"]):
					if data["_default"][str(ele)]["User_id"] == user_products[int(i)]["User_id"]:
						keyboard.add(types.InlineKeyboardButton(text = str(user_products[i]["Name"]), callback_data = str(i)))
						i = i + 1
			except IndexError:
				i = 0
			bot.send_message(user_id, "Fai tap sul prodotto che desideri eliminare ⬇️", reply_markup = keyboard)


@bot.callback_query_handler(func = lambda call: True) 
def callback_keyboard(call):
	user_id = call.message.chat.id
	message_id = call.message.message_id
	number = call.data 
	user_products = db.search(User.User_id == str(user_id))
	with open("product.json", "r") as jsonFile:
		data = json.load(jsonFile)
		index_to_delete = []
		for key in data["_default"]:
			if data["_default"][str(key)]["Name"] == user_products[int(number)]["Name"] and data["_default"][str(key)]["User_id"] == user_products[int(number)]["User_id"]:
				index_to_delete.append(str(key))
				bot.edit_message_text("🗑️ Il prodotto è stato eliminato 🗑️", user_id, message_id) 
		del data["_default"][str(index_to_delete.pop())] 
		i = 1
		for key in list(data["_default"]):
			data["_default"][str(i)] = data["_default"].pop(str(key))
			i = i + 1
	with open("product.json", "w") as jsonFile:
		data = json.dump(data, jsonFile)


@bot.message_handler(content_types = ['audio', 'video', 'document', 'photo', 'location', 'contact', 'sticker'])
def send_photo_error(message):
	bot.send_message(message.from_user.id, "🚫 Posso ricevere solo messaggi testuali 🚫")


@bot.message_handler(func = lambda message:	message.text == None or message.text != ("https://www.ebay" and ("https://www.amazon")))
def send_error(message):
	bot.send_message(message.from_user.id, "🚫 Questo non è un link eBay, per favore inserisci un link eBay valido 🚫", parse_mode = "HTML")


@bot.message_handler(func = lambda message: "https://www.amazon" in message.text and message.text != None)
def send_amazon_error(message):
	bot.send_message(message.from_user.id, " 🚫 Questo è il link di un prodotto Amazon, per favore inserisci un link eBay 🚫", parse_mode = "HTML")


global_db_num = []
global_db_price = []


def json_update():
	num = global_db_num.pop()
	price = global_db_price.pop()
	with open("product.json" , "r") as jsonFile:
		data = json.load(jsonFile)
	tmp = data["_default"][str(num)]["Price"]
	data["_default"][str(num)]["Price"] = str(price)
	with open("product.json", "w") as jsonFile:
		json.dump(data, jsonFile)


def price_check():
	with open("product.json", "r") as jsonFile:
		data = json.load(jsonFile)
		for key in data["_default"]:
			res = requests.get(data["_default"][str(key)]["Url"])
			soup = bs4.BeautifulSoup(res.text, "lxml")
			price = soup.select("#prcIsum"[4:11]) 
			real_price = ""
			json_price = data["_default"][str(key)]["Price"]
			for j in soup.select("#prcIsum"):
				real_price = (j.text)
				price_int = float(re.split(" |,", real_price)[1] + "." + re.split(" |,", real_price)[2]) 
				real_json_price = float(json_price)
			if price_int < real_json_price:
				image_html = soup.find(id = "icImg")
				link = "<a href =" + "'" + data["_default"][str(key)]["Url"] + "'" + ">" + data["_default"][str(key)]["Name"] + "</a>"
				link_click_here =  "<a href =" + "'" + data["_default"][str(key)]["Url"] + "'" + ">Clicca qui per acquistarlo</a>"
				coin = data["_default"][str(key)]["Coin"]
				diff = (real_json_price - price_int)
				global_db_num.append(int(key))
				global_db_price.append(price_int)
				json_update()
				bot.send_photo(parse_mode = "HTML", photo = image_html["src"], chat_id = data["_default"][str(key)]["User_id"], caption = "💥 Il prezzo del prodotto " + link + " è diminuito: 💥" + "\n\n📈 Prezzo precedente -> " + str(round(real_json_price , 2)) + " " + str(coin) + "\n\n📉 Prezzo attuale -> " + str(round(price_int, 2)) + " " + str(coin) + "\n\n📊 Risparmio -> " + str(round(diff, 2)) + " " + str(coin) + "\n\n💸 " + link_click_here + " 💸")
			elif price_int > real_json_price:
				image_html = soup.find(id = "icImg")
				link = "<a href =" + "'" + data["_default"][str(key)]["Url"] + "'" + ">" + data["_default"][str(key)]["Name"] + "</a>"
				link_click_here =  "<a href =" + "'" + data["_default"][str(key)]["Url"] + "'" + ">Clicca qui per acquistarlo</a>"
				coin = data["_default"][str(key)]["Coin"]
				aum_cost = (price_int - real_json_price)
				global_db_num.append(int(key))
				global_db_price.append(price_int)
				json_update()
				bot.send_photo(parse_mode = "HTML", photo = image_html["src"], chat_id = data["_default"][str(key)]["User_id"], caption = "💥 Il prezzo del prodotto: " + link + " è aumentato: 💥" + "\n\n📉 Prezzo precedente -> " + str(round(real_json_price , 2)) + " " + str(coin) + "\n\n📈 Prezzo attuale -> " + str(round(price_int, 2)) + " " + str(coin) + "\n\n📊 Perdita -> " + str(round(aum_cost, 2)) + " " + str(coin) + "\n\n💸 " + link_click_here + " 💸")
	Timer(30, price_check).start()

price_check()

@server.route("/" + bot_token, methods = ["GET", "POST"])  #Il sito viene pingato da StatusCake... Se dovesse interrompersi riprovare con Pingability.com
def get_message():
	bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
	return "!", 200


@server.route("/")
def webhook():
	bot.remove_webhook()
	bot.set_webhook(url = "https://ebayprices.herokuapp.com/" + bot_token)
	return "!", 200

if __name__ == "__main__":
	server.run(host = "0.0.0.0", port = int(os.environ.get("PORT", 5000)))
