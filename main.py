import discord
from discord.ext import commands
import os, threading
from flask import Flask, redirect, render_template_string
import stripe

app = Flask('')
TOKEN = os.getenv("TOKEN")
stripe.api_key = os.getenv("STRIPE_SECRET")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

PRODUCTS = {
    "color": {"name": "Rol de Color", "price": 199, "desc": "Tu color personalizado", "emoji": "🎨"},
    "emoji": {"name": "Emoji Personalizado", "price": 99, "desc": "Tu emoji en el server", "emoji": "😎"},
    "sticker": {"name": "Sticker Personalizado", "price": 149, "desc": "Tu sticker", "emoji": "🔥"},
    "vip": {"name": "Acceso VIP", "price": 499, "desc": "Canales VIP", "emoji": "👑"},
    "sala": {"name": "Sala Privada", "price": 299, "desc": "Tu sala de voz", "emoji": "🎧"},
    "boost": {"name": "Recompensa Boost", "price": 399, "desc": "Recompensa por boost", "emoji": "🚀"}
}

HTML_STORE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tienda Discord - Oficial</title>
<style>
body{background:#0f0f10;color:white;font-family:Arial;text-align:center;padding:20px}
h1{color:#5865f2}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:15px;max-width:900px;margin:auto}
.card{background:#1e1f22;padding:20px;border-radius:12px;border:1px solid #333}
.card h3{margin:10px 0}
.price{color:#23a559;font-weight:bold;font-size:18px}
.btn{background:#5865f2;color:white;padding:10px 15px;border-radius:8px;text-decoration:none;display:block;margin-top:10px;font-weight:bold}
.btn:hover{background:#4752c4}
</style>
</head>
<body>
<h1>🛒 TIENDA DEL SERVER</h1>
<p>Objetos comunes para tu servidor de Discord - Pago seguro con Stripe</p>
<div class="grid">
{% for id, p in products.items() %}
<div class="card">
<div style="font-size:40px">{{p.emoji}}</div>
<h3>{{p.name}}</h3>
<p style="color:#aaa">{{p.desc}}</p>
<div class="price">{{p.price/100}}€</div>
<a class="btn" href="/buy/{{id}}">Comprar</a>
</div>
{% endfor %}
</div>
<p style="margin-top:30px;color:#666">Bot activo en Discord con!tienda</p>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_STORE, products=PRODUCTS)

@app.route('/buy/<prod>')
def buy(prod):
    if prod not in PRODUCTS: return "Producto no existe", 404
    p = PRODUCTS[prod]
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price_data': {'currency': 'eur','product_data': {'name': p['name']},'unit_amount': p['price']},'quantity': 1}],
        mode='payment',
        success_url='https://discord.com',
        cancel_url='/',
    )
    return redirect(session.url)

@app.route('/webhook', methods=['POST'])
def webhook(): return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

@bot.event
async def on_ready():
    print(f"✅ BOT + WEB ACTIVOS como {bot.user}")

@bot.command()
async def tienda(ctx):
    embed = discord.Embed(title="🛒 TIENDA", description="También en la web!", color=0x5865f2)
    for k, v in PRODUCTS.items():
        embed.add_field(name=f"{v['emoji']} {v['name']} - {v['price']/100}€", value=f"`!comprar {k}`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def comprar(ctx, producto: str):
    producto = producto.lower()
    if producto not in PRODUCTS:
        await ctx.send(f"Usa `!tienda` - Disponibles: {', '.join(PRODUCTS.keys())}")
        return
    p = PRODUCTS[producto]
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price_data': {'currency': 'eur','product_data': {'name': p['name']},'unit_amount': p['price']},'quantity': 1}],
        mode='payment', success_url='https://discord.com', cancel_url='https://discord.com',
    )
    await ctx.send(f"{ctx.author.mention} Tu link para **{p['name']}**: {session.url}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
