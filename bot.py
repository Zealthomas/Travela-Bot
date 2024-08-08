import os
import re
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
import googlemaps
import requests

# Load environment variables from .env file
load_dotenv()

# Replace with your actual bot token and API keys
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

# Initialize the Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    logger.info("Received /start command")
    keyboard = [
        [InlineKeyboardButton("Get Directions", callback_data='directions')],
        [InlineKeyboardButton("Search Places", callback_data='search')],
        [InlineKeyboardButton("Geocode Address", callback_data='geocode')],
        [InlineKeyboardButton("Calculate Distance", callback_data='distance')],
        [InlineKeyboardButton("Get Weather", callback_data='weather')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Hi! I am your Navigator bot by Travela AI. How can I assist you today?', reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    commands = {
        'directions': "Please use /directions <origin> <destination>",
        'search': "Please use /search <query>",
        'geocode': "Please use /geocode <address>",
        'distance': "Please use /distance <origin> <destination>",
        'weather': "Please use /weather <city>",
    }

    response = commands.get(query.data, 'Unknown command')
    await query.edit_message_text(text=response)

async def get_directions(update: Update, context: CallbackContext) -> None:
    logger.info("Received /directions command")
    if len(context.args) < 2:
        await update.message.reply_text('Please provide both origin and destination. Usage: /directions <origin> <destination>')
        return

    origin, destination = ' '.join(context.args[:-1]), context.args[-1]
    logger.info(f"Origin: {origin}, Destination: {destination}")

    try:
        directions_result = gmaps.directions(origin, destination)
        logger.info(f"Directions result: {directions_result}")

        if directions_result:
            steps = directions_result[0]['legs'][0]['steps']
            directions = ""
            for i, step in enumerate(steps):
                instruction = re.sub('<[^<]+?>', '', step['html_instructions'])
                directions += f"{i+1}. {instruction} ➡️\n"
                if 'distance' in step:
                    directions += f"   - {step['distance']['text']}\n"
            await update.message.reply_text(directions, parse_mode='HTML')
        else:
            await update.message.reply_text('No directions found for the given locations.')
    except googlemaps.exceptions.ApiError as e:
        logger.error(f"Error fetching directions: {e}")
        await update.message.reply_text(f'Error fetching directions: {e}')
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await update.message.reply_text(f'An unexpected error occurred: {e}')

async def search_places(update: Update, context: CallbackContext) -> None:
    logger.info("Received /search command")
    if len(context.args) < 1:
        await update.message.reply_text('Please provide a search query. Usage: /search <query>')
        return

    query = ' '.join(context.args)
    logger.info(f"Search query: {query}")

    try:
        places_result = gmaps.places(query)
        logger.info(f"Places result: {places_result}")

        if places_result['results']:
            places = "\n".join(f"{place['name']} - {place['formatted_address']}" for place in places_result['results'][:5])
            await update.message.reply_text(places)
        else:
            await update.message.reply_text('No places found. Please refine your query.')
    except googlemaps.exceptions.ApiError as e:
        logger.error(f"Error searching places: {e}")
        await update.message.reply_text(f'Error searching places: {e}')
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await update.message.reply_text(f'An unexpected error occurred: {e}')

async def geocode_address(update: Update, context: CallbackContext) -> None:
    logger.info("Received /geocode command")
    if len(context.args) < 1:
        await update.message.reply_text('Please provide an address. Usage: /geocode <address>')
        return

    address = ' '.join(context.args)
    logger.info(f"Address: {address}")

    try:
        geocode_result = gmaps.geocode(address)
        logger.info(f"Geocode result: {geocode_result}")

        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            formatted_address = geocode_result[0]['formatted_address']
            await update.message.reply_text(f"Address: {formatted_address}\nLatitude: {location['lat']}\nLongitude: {location['lng']}")
        else:
            await update.message.reply_text('No geocode result found. Please check the address.')
    except googlemaps.exceptions.ApiError as e:
        logger.error(f"Error geocoding address: {e}")
        await update.message.reply_text(f'Error geocoding address: {e}')
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await update.message.reply_text(f'An unexpected error occurred: {e}')

async def get_distance(update: Update, context: CallbackContext) -> None:
    logger.info("Received /distance command")
    if len(context.args) < 2:
        await update.message.reply_text('Please provide both origin and destination. Usage: /distance <origin> <destination>')
        return

    origin, destination = ' '.join(context.args[:-1]), context.args[-1]
    logger.info(f"Origin: {origin}, Destination: {destination}")

    try:
        distance_result = gmaps.distance_matrix(origin, destination)
        logger.info(f"Distance matrix result: {distance_result}")

        if distance_result['rows']:
            distance = distance_result['rows'][0]['elements'][0]['distance']['text']
            duration = distance_result['rows'][0]['elements'][0]['duration']['text']
            await update.message.reply_text(f"Distance: {distance}\nDuration: {duration}")
        else:
            await update.message.reply_text('No distance result found. Please check the provided addresses.')
    except googlemaps.exceptions.ApiError as e:
        logger.error(f"Error calculating distance: {e}")
        await update.message.reply_text(f'Error calculating distance: {e}')
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await update.message.reply_text(f'An unexpected error occurred: {e}')

async def get_weather(update: Update, context: CallbackContext) -> None:
    logger.info("Received /weather command")
    if len(context.args) < 1:
        await update.message.reply_text('Please provide a city name. Usage: /weather <city>')
        return

    city = ' '.join(context.args)
    logger.info(f"City: {city}")

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        response = requests.get(url)
        weather_data = response.json()
        logger.info(f"Weather data: {weather_data}")

        if weather_data.get('weather'):
            description = weather_data['weather'][0]['description']
            temperature = weather_data['main']['temp']
            await update.message.reply_text(f"Weather in {city}:\nDescription: {description}\nTemperature: {temperature}°C")
        else:
            await update.message.reply_text('No weather information found. Please check the city name.')
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await update.message.reply_text(f'An unexpected error occurred: {e}')

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/directions <origin> <destination> - Get step-by-step directions\n"
        "/search <query> - Search for places\n"
        "/geocode <address> - Get the latitude and longitude of an address\n"
        "/distance <origin> <destination> - Calculate the distance and duration\n"
        "/weather <city> - Get weather information for a city\n"
    )
    await update.message.reply_text(help_text)

async def handle_location(update: Update, context: CallbackContext) -> None:
    user_location = update.message.location
    await update.message.reply_text(f"Received location: {user_location.latitude}, {user_location.longitude}")

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('directions', get_directions))
    application.add_handler(CommandHandler('search', search_places))
    application.add_handler(CommandHandler('geocode', geocode_address))
    application.add_handler(CommandHandler('distance', get_distance))
    application.add_handler(CommandHandler('weather', get_weather))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))

    application.run_polling()

if __name__ == '__main__':
    main()