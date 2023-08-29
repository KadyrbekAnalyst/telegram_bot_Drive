from telebot import types
import telebot
import psycopg2
from datetime import datetime

# Replace with your bot token
BOT_TOKEN = "6114080585:AAFN15QFrHwPbz0P99FQatYrXXmFQgG1CvM"

# Create a bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Database connection parameters
db_params = {
    "host": "localhost",  # Replace with your Docker container's IP or hostname
    "port": 5432,         # The port you mapped in Docker Compose
    "dbname": "postgres",
    "user": "postgres",
    "password": "mysecretpassword"
}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    attend_button = types.InlineKeyboardButton(text='Attend', callback_data='attend')
    skip_button = types.InlineKeyboardButton(text='Skip', callback_data='skip')
    check_attendance_button = types.InlineKeyboardButton(text='Check Attendance', callback_data='check_attendance')
    markup.add(attend_button, skip_button, check_attendance_button)

    bot.send_message(message.chat.id, "Please select an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'attend')
def callback_query(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name  # You can also use last_name or username
    try:
        connection = psycopg2.connect(**db_params)
        with connection.cursor() as cursor:
            current_date = datetime.now().date()
            cursor.execute("SELECT attended_today FROM attendance WHERE telegram_id = %s AND request_date::date = %s", (user_id, current_date))
            attendance_record = cursor.fetchone()
            if attendance_record and attendance_record[0]:
                bot.answer_callback_query(callback_query_id=call.id, text="You've already attended today.")
            else:
                cursor.execute("SELECT attended_today FROM attendance WHERE telegram_id = %s AND request_date::date = %s", (user_id, current_date))
                exist_today = cursor.fetchone()
                if exist_today and exist_today[0] is False:
                    cursor.execute("UPDATE attendance SET attended_today = TRUE WHERE telegram_id = %s AND request_date::date = %s", (user_id, current_date))
                    connection.commit()
                    bot.answer_callback_query(callback_query_id=call.id, text="Attendance marked!")
                else:
                # Mark attendance in the database
                    cursor.execute("INSERT INTO attendance (attended_today, telegram_id,request_date , name)"
                        "VALUES (%s, %s, %s, %s)",
                        (True,user_id,current_date,user_name)
                                   )
                    connection.commit()
                    bot.answer_callback_query(callback_query_id=call.id, text="Attendance marked!")


    except psycopg2.Error as e:
        print("Database error:", e)
    finally:
        if connection:
            connection.close()
            
@bot.callback_query_handler(func=lambda call: call.data == 'skip')
def callback_query(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name  # You can also use last_name or username
    try:
        connection = psycopg2.connect(**db_params)
        with connection.cursor() as cursor:
            current_date = datetime.now().date()
            cursor.execute("SELECT attended_today FROM attendance WHERE telegram_id = %s AND request_date::date = %s", (user_id, current_date))
            attendance_record = cursor.fetchone()
            if attendance_record and attendance_record[0]:
                cursor.execute("UPDATE attendance SET attended_today = FALSE WHERE telegram_id = %s AND request_date::date = %s", (user_id, current_date))
                connection.commit()
                bot.answer_callback_query(callback_query_id=call.id, text="Skip marked!")
            else:
                cursor.execute("SELECT telegram_id FROM attendance WHERE telegram_id = %s AND request_date::date = %s", (user_id, current_date))
                exist_today = cursor.fetchone()
                if exist_today:
                    bot.answer_callback_query(callback_query_id=call.id, text="You've already skip today.")
                else:
                    cursor.execute("INSERT INTO attendance (attended_today, telegram_id,request_date , name)"
                        "VALUES (%s, %s, %s, %s)",
                        (False,user_id,current_date,user_name)
                                   )
                    connection.commit()
                    bot.answer_callback_query(callback_query_id=call.id, text="Skip marked!")


    except psycopg2.Error as e:
        print("Database error:", e)
    finally:
        if connection:
            connection.close()
            
@bot.callback_query_handler(func=lambda call: call.data == 'check_attendance')
def callback_query_check_all_attendance(call):
    user_id = call.from_user.id
    
    # Check if the user is authorized to access this information
    if user_id == 607527832 or user_id == 228986095 :  # Replace with the actual admin user ID
        try:
            connection = psycopg2.connect(**db_params)
            with connection.cursor() as cursor:
                current_date = datetime.now().date()
                cursor.execute("SELECT name, attended_today FROM attendance WHERE request_date::date = %s", (current_date,))
                attendance_records = cursor.fetchall()

                if attendance_records:
                    attendance_text = "Attendance for today:\n"
                    for record in attendance_records:
                        name = record[0]
                        attended_today = record[1]
                        status = "Attended" if attended_today else "Did not attend"
                        attendance_text += f"{name}: {status}\n"
                else:
                    attendance_text = "No attendance records for today."

                bot.send_message(call.message.chat.id, attendance_text)

        except psycopg2.Error as e:
            print("Database error:", e)
        finally:
            if connection:
                connection.close()
    else:
        bot.send_message(call.message.chat.id, "You are not authorized to check attendance.")






# Start the bot
bot.polling()

# Test is success
# conn = psycopg2.connect(**db_params)
# cursor = conn.cursor()
# query = '''Select * from attendance '''
# cursor.execute(query)
# results = cursor.fetchall()
# print(results)