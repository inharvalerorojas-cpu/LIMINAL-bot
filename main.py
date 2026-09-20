import discord
from discord.ext import commands
import os, threading
from flask import Flask

app = Flask('')
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@app.route('/')
def home(): return "LIMINAL by INMARC Studios - ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

@bot.event
async def on_ready():
    print(f"✅ LIMINAL conectado como {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="INMARC Store | !tienda"))

@bot.command()
async def tienda(ctx):
    embed = discord.Embed(title="INMARC STUDIOS // LIMINAL STORE", description="Tienda oficial próximamente con Stripe", color=0x7c3aed)
    embed.add_field(name="LIMINAL ACCESS - 4,99€", value="Acceso privado INMARC", inline=False)
    embed.add_field(name="VIP REALM - 9,99€", value="Rol VIP + color", inline=False)
    embed.add_field(name="FOUNDER'S KEY - 19,99€", value="Founder limitado", inline=False)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
