import telebot
from telebot import types
from config import TOKEN
from logic import QuizManager

bot = telebot.TeleBot(TOKEN)

quiz_manager = QuizManager()

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    
    user_data = quiz_manager.check_user(user_id)
    
    if user_data:
        from config import ANIMALS
        animal = ANIMALS.get(user_data['totem'])
        
        if animal:
            welcome_back = (
                f"Рады видеть тебя снова, опекун! 👋\n\n"
                f"Твой тотем по-прежнему — *{animal['name']}*! 🐾\n"
                "Он скучал и ждет тебя в Московском зоопарке."
            )
            try:
                with open(animal['image'], 'rb') as photo:
                    bot.send_photo(user_id, photo, caption=welcome_back, parse_mode="Markdown")
            except:
                bot.send_message(user_id, welcome_back, parse_mode="Markdown")
        
        show_result(user_id)

    quiz_manager.start_quiz(user_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать тест 🐾", callback_data="start_quiz"))
    
    img_path = '/content/images/start_logo.png' 
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Добро пожаловать в программу опеки Московского зоопарка. "
        "Пройди тест, чтобы найти своего тотемного зверя! 🦁\n\n"
        "🛡 *Конфиденциальность:* мы не собираем ваши персональные данные. "
        "Нам нужны только ответы на вопросы, чтобы подобрать вам друга."
    )
    
    try:
        with open(img_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

    
def send_question(user_id):
    question = quiz_manager.get_question(user_id)
    markup = types.InlineKeyboardMarkup()
    
    for text, animal_key in question["options"]:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"answer_{animal_key}"))

    question_photo = "/content/images/question.png"
    
    try:
        with open(question_photo, 'rb') as photo:
            bot.send_photo(
                user_id, 
                photo, 
            caption=f"❓ *Вопрос №{quiz_manager.user_states[user_id]['current_question']}:*\n\n{question['text']}",
            reply_markup=markup,
            parse_mode="Markdown"


            )
    except Exception as e:
        bot.send_message(user_id, f"Ошибка фото: {e}\n\n{question['text']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.message.chat.id
    
    if call.data == "start_quiz":
        quiz_manager.start_quiz(user_id)
        send_question(user_id)

    elif call.data == "contact_keeper":
        bot.send_message(user_id, "📞 По вопросам опеки пишите нам: help@moscowzoo.ru\nИли в наш официальный чат: @MoscowZooOfficial")
    
    elif call.data.startswith("answer_"):
        animal_key = call.data.replace("answer_", "")
        quiz_manager.update_score(user_id, animal_key)
        
        if quiz_manager.is_last_question(user_id):
            show_result(user_id)
        else:
            send_question(user_id)
    elif call.data == "get_cert":
        user_id = call.message.chat.id
        user_name = call.from_user.first_name
        user_data = quiz_manager.check_user(user_id)
        
        if user_data:
            animal_name = user_data['totem']
            
            cert_path = quiz_manager.create_certificate(user_name, animal_name)
            with open(cert_path, 'rb') as cert:
                bot.send_document(user_id, cert, caption=f"Твой официальный сертификат опекуна, {user_name}! ✨")
        else:
            bot.send_message(user_id, "Сначала пройди тест, чтобы я знал, кого вписать в сертификат! 😉")
    
    bot.answer_callback_query(call.id)


def save_feedback(message):
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(message.chat.id, "Спасибо за ваш отзыв! Вы помогаете нам стать лучше. ✨")

def send_question(user_id):
    question = quiz_manager.get_question(user_id)
    markup = types.InlineKeyboardMarkup()
    
    for text, animal_key in question["options"]:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"answer_{animal_key}"))
    
    img_path = question["image"] 
    
    with open(img_path, 'rb') as photo:
        bot.send_photo(
            user_id, 
            photo, 
            caption=f"❓ *Вопрос №{quiz_manager.user_states[user_id]['current_question']}:*\n\n{question['text']}", 
            reply_markup=markup,
            parse_mode="Markdown"
        )



def show_result(user_id):
    from config import ANIMALS
    from telebot import types
    
    result_key = quiz_manager.get_result(user_id)
    
    animal = ANIMALS.get(result_key)
    if not animal:
        for k, v in ANIMALS.items():
            if v['name'] == result_key:
                animal = v
                result_key = k
                break

    user_info = bot.get_chat(user_id)
    user_name = user_info.first_name if user_info.first_name else "Друг"
    quiz_manager.save_result(user_id, user_name, result_key)

    text = (
        f"🏁 *Тест завершен!*\n\n"
        f"Твое тотемное животное — *{animal['name']}*! 🐾\n\n"
        f"{animal['desc']}\n\n"
        f"💳 Хочешь стать опекуном? Жми кнопку ниже!"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Стать опекуном ❤️", url="https://moscowzoo.ru"))
    markup.add(types.InlineKeyboardButton("Оставить отзыв ✍️", callback_data="leave_feedback"))
    share_msg = f"Я прошел тест и мой тотем — {animal['name']}! 🐾 Узнай, кто ты: t.me/TheZooGuardianrobot"
    markup.add(types.InlineKeyboardButton("Поделиться результатом 📢", switch_inline_query=share_msg))
    
    markup.add(types.InlineKeyboardButton("Связаться с сотрудником 📞", callback_data="contact_keeper"))
    markup.add(types.InlineKeyboardButton("Получить именной сертификат 📜", callback_data="get_cert"))
    markup.add(types.InlineKeyboardButton("Пройти еще раз 🔄", callback_data="start_quiz"))
    
    try:
        with open(animal['image'], 'rb') as photo:
            bot.send_photo(user_id, photo, caption=text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

ADMIN_ID = 12345678

@bot.message_handler(commands=["admin"])
def admin_stats(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Доступ закрыт.")
        return

    import json
    try:
        with open('/content/guardians.json', 'r') as f:
            data = json.load(f)
        
        report = f"📊 *СТАТИСТИКА БОТА*\n\n"
        report += f"👤 Всего опекунов: {len(data)}\n"
        bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    except:
        bot.send_message(ADMIN_ID, "База пока пуста.")

@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if message.chat.id != ADMIN_ID: return
    text_to_send = message.text.replace("/broadcast ", "")
    
    if not text_to_send or text_to_send == "/broadcast":
        bot.send_message(ADMIN_ID, "⚠️ Напиши: /broadcast Привет, опекуны!")
        return

    import json
    with open('/content/guardians.json', 'r') as f:
        data = json.load(f)

    count = 0
    for user_id in data.keys():
        try:
            bot.send_message(user_id, f"🔔 *Сообщение от Зоопарка:*\n\n{text_to_send}", parse_mode="Markdown")
            count += 1
        except:
            pass
    
    bot.send_message(ADMIN_ID, f"✅ Рассылка завершена! Отправлено: {count} пользователям.")

@bot.inline_handler(lambda query: True)
def query_text(inline_query):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            text="Узнать свой тотем 🐾", 
            url="https://t.me"
        ))

        r = types.InlineQueryResultArticle(
            id='1',
            title="🐾 Нажми сюда, чтобы отправить результат!",
            description="Твой тотем: " + inline_query.query.split("—")[-1],
            input_message_content=types.InputTextMessageContent(
                inline_query.query, 
                parse_mode="Markdown"
            ),
            reply_markup=markup
        )
        
        bot.answer_inline_query(inline_query.id, [r], cache_time=1)
    except Exception as e:
        print(f"DEBUG Inline Error: {e}")



if __name__ == "__main__":
    bot.polling(none_stop=True)
