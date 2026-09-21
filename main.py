import discord
from discord.ext import commands
import os, threading, time
from flask import Flask
from collections import defaultdict

app = Flask(__name__)
TOKEN = os.getenv("TOKEN")
STRIPE_LINK = os.getenv("STRIPE_LINK", "https://buy.stripe.com/test_123")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

stats = {"raids": 0, "msgs": 0, "nukes": 0, "webhooks": 0}
join_cache, msg_global = [], []
spam_cache = defaultdict(list)
is_defending = False

# WEB DIRECTA, SIN ARCHIVOS
HTML = """
<!DOCTYPE html>
<html><head><title>Liminal Shield</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{background:#0a0a0b;color:white;font-family:Arial;text-align:center;padding:20px}
.card{background:#16161a;padding:20px;margin:15px auto;max-width:500px;border-radius:15px;border:1px solid #333}
h1{color:#9147ff}.num{font-size:32px;font-weight:bold}
.btn{background:#9147ff;color:white;padding:15px 30px;border-radius:10px;text-decoration:none;display:inline-block}
</style>
</head>
<body>
<h1>🛡️ LIMINAL SHIELD</h1>
<p>Bot ONLINE 24/7</p>
<div class="card"><h2>RAIDS BLOQUEADAS</h2><div class="num">{raids}</div></div>
<div class="card"><h2>MENSAJES ANALIZADOS</h2><div class="num">{msgs}</div></div>
<div class="card"><h2>NUKES BLOQUEADOS</h2><div class="num">{nukes}</div></div>
<div class="card"><h2>WEBHOOKS BORRADOS</h2><div class="num">{webhooks}</div></div>
<div class="card"><a href="{stripe}" class="btn">COMPRAR PRO - 4.99€</a><br><br>Comando:!liminal</div>
</body></html>
"""

@app.route('/')
def home():
    return HTML.format(raids=stats["raids"], msgs=stats["msgs"], nukes=stats["nukes"], webhooks=stats["webhooks"], stripe=STRIPE_LINK)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def blindar(guild, razon, atacante=None):
    global is_defending
    if is_defending: return
    is_defending = True
    if "RAID" in razon: stats["raids"] += 1
    if "NUKE" in razon: stats["nukes"] += 1
    try:
        await guild.edit(verification_level=discord.VerificationLevel.highest)
        for ch in guild.text_channels:
            try:
                await ch.edit(slowmode_delay=15)
                await ch.set_permissions(guild.default_role, send_messages=False)
            except: pass
        canal = guild.system_channel or guild.text_channels[0]
        if atacante:
            try: await guild.ban(atacante, reason=razon)
            except: pass
        await canal.send(f"🛡️ BLOQUEADO: {razon}.!unlock para restaurar")
    except: pass

@bot.event
async def on_ready(): print(f"ONLINE {bot.user}")

@bot.event
async def on_member_join(m):
    join_cache.append(time.time())
    while join_cache and time.time() - join_cache[0] > 10: join_cache.pop(0)
    if len(join_cache) >= 5: await blindar(m.guild, f"RAID {len(join_cache)} joins")

@bot.event
async def on_message(msg):
    if msg.author.bot:
        await bot.process_commands(msg)
        return
    stats["msgs"] += 1
    now = time.time()
    msg_global.append(now)
    while msg_global and now - msg_global[0] > 5: msg_global.pop(0)
    if len(msg_global) >= 25:
        await blindar(msg.guild, f"FLOOD {len(msg_global)} msgs"); msg_global.clear(); return
    spam_cache[msg.author.id].append(now)
    spam_cache[msg.author.id] = [t for t in spam_cache[msg.author.id] if now - t < 4]
    if len(spam_cache[msg.author.id]) >= 6:
        try: await msg.author.timeout(duration=3600, reason="spam")
        except: pass
        return
    await bot.process_commands(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    global is_defending; is_defending = True
    await ctx.guild.edit(verification_level=discord.VerificationLevel.highest)
    for ch in ctx.guild.text_channels:
        try: await ch.edit(slowmode_delay=15); await ch.set_permissions(ctx.guild.default_role, send_messages=False)
        except: pass
    await ctx.send("🔒 Bloqueado")

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    global is_defending; is_defending = False; join_cache.clear(); msg_global.clear()
    await ctx.guild.edit(verification_level=discord.VerificationLevel.low)
    for ch in ctx.guild.text_channels:
        try: await ch.edit(slowmode_delay=0); await ch.set_permissions(ctx.guild.default_role, overwrite=None)
        except: pass
    await ctx.send("🔓 Restaurado")

@bot.command()
async def liminal(ctx):
    embed = discord.Embed(title="🛡️ LIMINAL SHIELD PRO", color=0x9147ff, description=f"[Ver Web]({os.getenv('RENDER_EXTERNAL_URL','')}) | [Comprar PRO]({STRIPE_LINK})")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
