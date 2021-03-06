#!/usr/bin/env python3

import logging
import os
import time
from typing import List

import emoji
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
from telegram import ParseMode

import pgn_helper
from analysis import Analysis
from move_evaluation import MoveEvaluation

# Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
updater = Updater(token=os.getenv('telegram_token_chess'), use_context=True)
dispatcher = updater.dispatcher

# telegram markdown stuff
special_characters = '{}|_-=!~.>+#`'


def start_handler(update, context):
    message = "Hey, good to see you! I'll analyze your chess games. " \
              "To have a game analyzed, just share the PGN from lichess or chess.com with me!\n"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    logging.info("Started chat %d", update.effective_chat.id)


def help_handler(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='blub')


def escape_special_chars(result_string):
    for i in range(len(special_characters)):
        char = special_characters[i]
        result_string = result_string.replace(char, f"\\{char}")

    return result_string


def stringify_evals(move_evals: List[MoveEvaluation]):
    result_string = emoji.emojize("Here's the most interesting moves I could find :thought_balloon: \n\n")
    black_evals = [move_eval for move_eval in move_evals if move_eval.turn % 1 != 0]
    white_evals = [move_eval for move_eval in move_evals if move_eval.turn % 1 == 0]

    result_string += emoji.emojize("Important moves by White: :white_circle:\n\n")
    for move_eval in white_evals:
        result_string += move_eval.stringify() + '\n'

    result_string += emoji.emojize("Important moves by Black: :black_circle:\n\n")
    for move_eval in black_evals:
        result_string += move_eval.stringify() + '\n'

    result_string = escape_special_chars(result_string)
    return result_string


def message_handler(update, context):
    user_input = update.message.text
    pgn = pgn_helper.read_pgn_from_string(user_input)
    if pgn is not None:
        logging.info(f"Analyzing game for chat id {update.effective_chat.id}")
        analysis = Analysis(pgn, "config.json")
        analysis.run()
        current_progress = analysis.progress
        msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Analyzing your game now! Progress: {current_progress}%")
        while analysis.is_done is not True:
            if current_progress != analysis.progress:
                current_progress = analysis.progress
                context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                              message_id=msg.message_id,
                                              text=f'Analyzing your game now! Progress: {current_progress}%')
            time.sleep(1)
        context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                      message_id=msg.message_id,
                                      text=f'Analyzing your game now! Progress: 100%')
        analysis.categorize_evals()
        blunders = analysis.blunders
        response = stringify_evals(blunders)
        logging.info(response)
        update.message.reply_text(text=response,
                                  parse_mode=ParseMode.MARKDOWN_V2)
    else:
        logging.info(f"Received a message that was not a valid PGN from {update.effective_chat.id}")
        context.bot.send_message(chat_id=update.effective_chat.id, text="That doesn't look like a PGN to me.")


def error_handler(update, context):
    logging.warning("An error occurred and was handled.")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="An error occurred while analyzing your game."
                                  "Ping @violin_tobi for details or open a Github issue detailing the problem.")


def echo_markup(update, context):
    user_input = update.message.text
    text = '[bla](https://google.com)'
    update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN_V2)


dispatcher.add_handler(CommandHandler('start', start_handler))
dispatcher.add_handler(CommandHandler('help', help_handler))
# dispatcher.add_error_handler(error_handler)
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), message_handler))
# dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo_markup))


updater.start_polling()
