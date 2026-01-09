import telebot
from telebot import types
import yfinance as yf
import pandas_ta as ta
import os
from flask import Flask
from threading import Thread

# Render Keep Alive (ለ Cron-job እንዲመች)
app = Flask('')
@app.route('/')
def home(): return "Forex AI Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# የአንተ መረጃ
TOKEN = '7311692566:AAGFv2P5ioA_s_45talCetYbJQynbTAlrvc'
ADMIN_ID = '449613656'
bot = telebot.TeleBot(TOKEN)

# --- ዋና ማውጫ (Buttons) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('🇪🇺 EUR/USD')
    btn2 = types.KeyboardButton('🇬🇧 GBP/USD')
    btn3 = types.KeyboardButton('🇯🇵 USD/JPY')
    btn4 = types.KeyboardButton('🟡 GOLD (XAU/USD)')
    btn5 = types.KeyboardButton('₿ Bitcoin (BTC)')
    btn6 = types.KeyboardButton('🔄 ሌላ ምልክት ለመጻፍ')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

def get_detailed_analysis(symbol):
    try:
        # ምልክቶችን ለ Yahoo Finance እንዲመቹ ማስተካከል
        symbol_map = {
            '🇪🇺 EUR/USD': 'EURUSD=X',
            '🇬🇧 GBP/USD': 'GBPUSD=X',
            '🇯🇵 USD/JPY': 'USDJPY=X',
            '🟡 GOLD (XAU/USD)': 'GC=F',
            '₿ Bitcoin (BTC)': 'BTC-USD'
        }
        
        search_symbol = symbol_map.get(symbol, symbol)
        
        # መረጃውን ማምጣት
        data = yf.download(search_symbol, period="2d", interval="15m", progress=False)
        
        if data.empty or len(data) < 20:
            return "❌ ስህተት፡ መረጃ ማግኘት አልተቻለም። እባክዎ ምልክቱን በትክክል ያስገቡ።"

        # Indicators ማስላት
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['EMA_20'] = ta.ema(data['Close'], length=20)
        
        # ቁጥሮቹን ወደ float በመቀየር ስህተቶችን ማስቀረት
        last_price = float(data['Close'].iloc[-1])
        last_rsi = float(data['RSI'].iloc[-1])
        last_ema = float(data['EMA_20'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2])

        analysis = f"🎯 **የ {symbol} AI ትንታኔ**\n"
        analysis += "----------------------------------\n"
        analysis += f"💰 **ዋጋ:** `{last_price:.5f}`\n"
        analysis += f"📈 **RSI:** `{last_rsi:.2f}`\n"
        analysis += f"📊 **EMA (20):** `{last_ema:.5f}`\n\n"

        if last_rsi < 35:
            signal = "🟢 **BUY (Oversold)**\nገበያው በጣም ስለተሸጠ ዋጋው ሊጨምር ይችላል።"
        elif last_rsi > 65:
            signal = "🔴 **SELL (Overbought)**\nገበያው በጣም ስለተገዛ ዋጋው ሊቀንስ ይችላል።"
        elif last_price > last_ema and prev_price <= last_ema:
            signal = "🔵 **STRONG BUY**\nዋጋው ከ EMA በላይ ስለወጣ ወደ ላይ የመሄድ እድል አለው።"
        else:
            signal = "🟡 **NEUTRAL**\nገበያው የተለየ አቅጣጫ አልያዘም። በትዕግስት ይጠብቁ።"

        analysis += f"💡 **የ AI ምክር:**\n{signal}"
        return analysis
    except Exception as e:
        return f"⚠️ ስህተት: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = "እንኳን ወደ ቁምነገር Forex AI ቦት በሰላም መጡ! 👋\n\nትንታኔ የሚፈልጉትን ጥንድ ከታች ካሉት አማራጮች ይምረጡ።"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '🔄 ሌላ ምልክት ለመጻፍ')
def ask_custom(message):
    bot.send_message(message.chat.id, "እባክዎ የሚፈልጉትን ምልክት ይጻፉ (ለምሳሌ፦ `AUDUSD=X`)፡", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    symbol = message.text
    bot.send_message(message.chat.id, f"🔍 የ {symbol} ገበያን በመተንተን ላይ ነኝ... እባክዎ ይጠብቁ።")
    
    result = get_detailed_analysis(symbol)
    
    # ውጤቱን ከ Button ጋር መላክ
    bot.send_message(message.chat.id, result, parse_mode='Markdown', reply_markup=main_menu())
    
    # ለአድሚን (ለአንተ) መረጃ መላክ
    bot.send_message(ADMIN_ID, f"🔔 @{message.from_user.username} የ {symbol} ትንታኔ ጠይቋል።")

if __name__ == "__main__":
    # Flaskን በሌላ Thread ማስነሳት
    Thread(target=run_flask).start()
    bot.infinity_polling()        
