from typing import Final
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from data_management import calculate_distance, generate_google_maps_link, get_resorts, get_restaurants

# TODO: Insert the TOKEN and the USERNAME
TOKEN: Final = ''
USERNAME: Final = ''


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, how can I help you?')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_message = (
        f"The bot has 4 commands:\n"
        f"\t1) start - Starts the bot\n"
        f"\t2) help - Returns the list of commands\n"
        f"\t3) booking - Book an event\n"
        f"\t4) tourismagent - Search the closes beach resort or restaurant"
    )
    await update.message.reply_text(reply_message)


# Define conversation states
NAME, SURNAME, EMAIL, PHONE = range(4)


# Command handler: Start the conversation
async def booking_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Insert your *name*:", parse_mode="Markdown")
    return NAME


# State 1: Capture name
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Insert your *surname*:", parse_mode="Markdown")
    return SURNAME


# State 2: Capture surname
async def get_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['surname'] = update.message.text
    await update.message.reply_text("Insert your *email address*:", parse_mode="Markdown")
    return EMAIL


# State 3: Capture email address
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text
    await update.message.reply_text("Insert your *phone number*:", parse_mode="Markdown")
    return PHONE


# State 4: Capture phone number and display summary
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['phone'] = update.message.text

    # Summarize the collected data
    summary = (
        f"Your info:\n\n"
        f"👤 *Name*: {context.user_data['name']}\n"
        f"👤 *Surname*: {context.user_data['surname']}\n"
        f"📧 *Email*: {context.user_data['email']}\n"
        f"📞 *Phone*: {context.user_data['phone']}\n\n"
        f"Thanks for booking!"
    )

    await update.message.reply_text(summary, parse_mode="Markdown")
    return ConversationHandler.END


# Cancel handler: End the conversation
async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Event booking has been canceled. Have a great day!")
    return ConversationHandler.END


# Conversation states
LOCATION, CHOICE = range(2)


# Start command handler
async def tourismagent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Welcome to the Tourism Agent Bot!\nPlease share your location to find nearby places.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Send Location", request_location=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return LOCATION


# Location handler
async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_location = update.message.location
    context.user_data['latitude'] = user_location.latitude
    context.user_data['longitude'] = user_location.longitude

    await update.message.reply_text(
        "What are you looking for? Please choose:",
        reply_markup=ReplyKeyboardMarkup(
            [["Beach Resort"], ["Restaurant"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return CHOICE


# Choice handler
async def receive_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text.lower()
    user_lat = context.user_data['latitude']
    user_lon = context.user_data['longitude']

    filtered_places = None
    if user_choice == "beach resort":
        filtered_places = get_resorts()
    else:
        filtered_places = get_restaurants()

    nearest_place = min(
        filtered_places.itertuples(),
        key=lambda place: calculate_distance(
            user_lat, user_lon, place.latitudine, place.longitudine
        )
    )

    # Generate Google Maps link
    maps_link = generate_google_maps_link(nearest_place.latitudine, nearest_place.longitudine)

    # Respond with the nearest place
    await update.message.reply_text(
        f"The nearest {user_choice} is:\n\n"
        f"*{nearest_place.denominazione}*\n"
        f"📍 [View on Google Maps]({maps_link})",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# Cancel handler
async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation canceled. Have a nice day!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))

    # ConversationHandler to manage the sequence of questions
    booking_handler = ConversationHandler(
        entry_points=[CommandHandler("booking", booking_command)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_surname)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel_booking)],
    )

    # Add handlers to the application
    app.add_handler(booking_handler)

    # Define conversation handler
    agent_handler = ConversationHandler(
        entry_points=[CommandHandler("tourismagent", tourismagent)],
        states={
            LOCATION: [MessageHandler(filters.LOCATION, receive_location)],
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_choice)],
        },
        fallbacks=[CommandHandler("cancel", cancel_search)],
    )

    # Add the handler to the application
    app.add_handler(agent_handler)

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
