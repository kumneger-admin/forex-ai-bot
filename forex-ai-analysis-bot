import telebot
import yfinance as yf
import pandas_ta as ta
import os
from flask import Flask
from threading import Thread

# Render ለሚጠይቀው Port ምላሽ ለመስጠት (Keep Alive)
app = Flask('')
@app.route('/')
def home():
    return "Forex AI Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# የአንተ መረጃ
TOKEN = '7311692566:AAGFv2P5ioA_s_45talCetYbJQynbTAlrvc'
ADMIN_ID = '449613656'
bot = telebot.TeleBot(TOKEN)

def get_detailed_analysis(symbol):
    try:
        data = yf.download(symbol, period="2d", interval="15m")
        if data.empty or len(data) < 20:
            return "❌ ስህተት፡ ምልክቱን አላገኘሁትም። ለምሳሌ፡ EURUSD=X ብለው ይሞክሩ።"

        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['EMA_20'] = ta.ema(data['Close'], length=20)
        
        last_price = data['Close'].iloc[-1]
        last_rsi = data['RSI'].iloc[-1]
        last_ema = data['EMA_20'].iloc[-1]
        prev_price = data['Close'].iloc[-2]

        analysis = f"🎯 **የ {symbol} AI ትንታኔ**\n"
        analysis += "----------------------------------\n"
        analysis += f"💰 **ዋጋ:** `{last_price:.5f}`\n"
        analysis += f"📈 **RSI:** `{last_rsi:.2f}`\n"
        analysis += f"📊 **EMA:** `{last_ema:.5f}`\n\n"

        if last_rsi < 30:
            signal = "🟢 **BUY (Oversold)**\nገበያው በጣም ስለተሸጠ ዋጋው ሊጨምር ይችላል።"
        elif last_rsi > 70:
            signal = "🔴 **SELL (Overbought)**\nገበያው በጣም ስለተገዛ ዋጋው ሊቀንስ ይችላል።"
        elif last_price > last_ema and prev_price <= last_ema:
            signal = "🔵 **STRONG BUY**\nዋጋው ከ EMA በላይ ስለወጣ ወደ ላይ የመሄድ እድል አለው።"
        else:
            signal = "🟡 **NEUTRAL**\nገበያው የተለየ አቅጣጫ አልያዘም።"

        analysis += f"💡 **ምክር:**\n{signal}"
        return analysis
    except Exception as e:
        return f"⚠️ ስህተት: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "እንኳን ወደ Forex AI ቦት መጡ! ትንታኔ ለማግኘት እንደ `EURUSD=X` ያሉ ምልክቶችን ይላኩ።")

@bot.message_handler(func=lambda m: True)
def handle_analysis(message):
    symbol = message.text.upper()
    bot.send_message(message.chat.id, f"🔍 የ {symbol} ገበያን በመተንተን ላይ ነኝ...")
    result = get_detailed_analysis(symbol)
    bot.send_message(message.chat.id, result, parse_mode='Markdown')
    bot.send_message(ADMIN_ID, f"🔔 @{message.from_user.username} {symbol} ጠይቋል።")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
