import telebot
from telebot import types
import yfinance as yf
import os
from flask import Flask
from threading import Thread

# Render Keep Alive
app = Flask('')
@app.route('/')
def home(): return "Forex AI Bot is Live!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

TOKEN = '7311692566:AAGFv2P5ioA_s_45talCetYbJQynbTAlrvc'
ADMIN_ID = '449613656'
bot = telebot.TeleBot(TOKEN)

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_detailed_analysis(symbol):
    try:
        symbol_map = {
            '🇪🇺 EUR/USD': 'EURUSD=X', '🇬🇧 GBP/USD': 'GBPUSD=X',
            '🇯🇵 USD/JPY': 'USDJPY=X', '🟡 GOLD (XAU/USD)': 'GC=F',
            '₿ Bitcoin (BTC)': 'BTC-USD'
        }
        search_symbol = symbol_map.get(symbol, symbol)
        
        # መረጃ ማምጣት
        df = yf.download(search_symbol, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 30:
            return "❌ በቂ የገበያ መረጃ ማግኘት አልተቻለም።"

        # በራሳችን RSI እና EMA ማስላት (ከስህተት ነፃ የሆነ መንገድ)
        close_prices = df['Close']
        df['RSI'] = calculate_rsi(close_prices)
        df['EMA_20'] = close_prices.ewm(span=20, adjust=False).mean()
        
        # ባዶ ያልሆኑትን የመጨረሻ እሴቶች መውሰድ
        valid_df = df.dropna(subset=['RSI', 'EMA_20'])
        last_row = valid_df.iloc[-1]
        prev_row = valid_df.iloc[-2]
        
        l_price, l_rsi = float(last_row['Close']), float(last_row['RSI'])
        l_ema, p_price = float(last_row['EMA_20']), float(prev_row['Close'])

        analysis = f"🎯 **የ {symbol} AI ትንታኔ**\n"
        analysis += "----------------------------------\n"
        analysis += f"💰 **ዋጋ:** `{l_price:.5f}`\n"
        analysis += f"📈 **RSI:** `{l_rsi:.2f}`\n"
        analysis += f"📊 **EMA (20):** `{l_ema:.5f}`\n\n"

        if l_rsi < 30: signal = "🟢 **BUY (Oversold)**\nገበያው በጣም ስለተሸጠ ዋጋው ሊጨምር ይችላል።"
        elif l_rsi > 70: signal = "🔴 **SELL (Overbought)**\nገበያው በጣም ስለተገዛ ዋጋው ሊቀንስ ይችላል።"
        elif l_price > l_ema and p_price <= l_ema: signal = "🔵 **STRONG BUY**\nዋጋው ከ EMA በላይ ወጥቷል።"
        else: signal = "🟡 **NEUTRAL**\nገበያው ግልጽ አቅጣጫ አልያዘም።"

        return analysis + f"💡 **ምክር:**\n{signal}"
    except Exception as e:
        return f"⚠️ ስህተት: ትንታኔውን መስራት አልተቻለም።"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🇪🇺 EUR/USD', '🇬🇧 GBP/USD', '🇯🇵 USD/JPY', '🟡 GOLD (XAU/USD)', '₿ Bitcoin (BTC)', '🔄 ሌላ ምልክት ለመጻፍ')
    bot.send_message(message.chat.id, "እንኳን ወደ Forex AI ቦት መጡ! 👋\nጥንድ ይምረጡ፡", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if message.text == '🔄 ሌላ ምልክት ለመጻፍ':
        bot.send_message(message.chat.id, "ምልክቱን ይጻፉ (ለምሳሌ፦ `AUDUSD=X`)፡")
        return
    bot.send_message(message.chat.id, f"🔍 የ {message.text} ገበያን በመተንተን ላይ ነኝ...")
    result = get_detailed_analysis(message.text)
    bot.send_message(message.chat.id, result, parse_mode='Markdown')
    bot.send_message(ADMIN_ID, f"🔔 @{message.from_user.username} {message.text} ጠይቋል።")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
