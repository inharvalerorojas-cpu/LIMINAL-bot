import discord
from discord.ext import commands
import os, threading, time
from flask import Flask
from collections import defaultdict

app = Flask('')
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- MEMORIA ---
join_cache = []
msg_global = []
spam_cache = defaultdict(list)
is_defending = False
WHITELIST = []

@app.route('/')
def home(): return "INMARC SHIELD TOTAL - LIVE"
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def blindar_servidor(guild, razon, atacante=None):
    global is_defending
    if is_defending: return
    is_defending = True
    print(f"🚨 ATAQUE: {razon}")
    try:
        await guild.edit(verification_level=discord.VerificationLevel.highest)
        for ch in guild.text_channels:
            try:
                await ch.edit(slowmode_delay=15)
                await ch.set_permissions(guild.default_role, send_messages=False)
            except: pass
        canal = guild.system_channel or guild.text_channels[0]
        if atacante:
            try: await guild.ban(atacante, reason=f"Shield: {razon}")
            except: pass
            await canal.send(f"🛡️ **ATAQUE BLOQUEADO: {razon}**\nAtacante: {atacante} baneado. Usa `!unlock`")
        else:
            await canal.send(f"🛡️ **ATAQUE BLOQUEADO: {razon}**\nLockdown activado. Usa `!unlock`")
    except Exception as e:
        print(f"Error blindaje: {e}")

@bot.event
async def on_ready():
    print(f"✅ SHIELD TOTAL ACTIVO como {bot.user}")

@bot.event
async def on_member_join(member):
    now = time.time()
    join_cache.append(now)
    while join_cache and now - join_cache[0] > 10:
        join_cache.pop(0)
    if len(join_cache) >= 5:
        await blindar_servidor(member.guild, f"RAID - {len(join_cache)} joins/10s")

@bot.event
async def on_message(message):
    if message.author.bot or message.author.id in WHITELIST:
        return
    now = time.time()
    msg_global.append(now)
    while msg_global and now - msg_global[0] > 5:
        msg_global.pop(0)
    if len(msg_global) >= 25:
        await blindar_servidor(message.guild, f"FLOOD/DDOS - {len(msg_global)} msgs/5s")
        msg_global.clear()
        return

    spam_cache[message.author.id].append(now)
    spam_cache[message.author.id] = [t for t in spam_cache[message.author.id] if now - t < 4]
    if len(spam_cache[message.author.id]) >= 6:
        try:
            await message.author.timeout(duration=3600, reason="Anti-Spam")
            await message.channel.send(f"🤖 {message.author.mention} muteado 1h por spam.", delete_after=5)
        except: pass
        return

    if ("@everyone" in message.content or "@here" in message.content) and not message.author.guild_permissions.moderate_members:
        try:
            await message.delete()
            await message.author.timeout(duration=3600, reason="Anti @everyone")
        except: pass
        return

    scam_words = ["free nitro", "nitro gratis", "discord.gift", "steam gift"]
    if any(w in message.content.lower() for w in scam_words):
        try:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention} link scam borrado.", delete_after=10)
        except: pass
        return

    await bot.process_commands(message)

@bot.event
async def on_guild_channel_delete(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.user.id not in WHITELIST and not entry.user.bot:
                await blindar_servidor(channel.guild, f"NUKE - Canal {channel.name} borrado", entry.user)
    except: pass

@bot.event
async def on_guild_role_delete(role):
    try:
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.user.id not in WHITELIST and not entry.user.bot:
                await blindar_servidor(role.guild, f"NUKE - Rol {role.name} borrado", entry.user)
    except: pass

@bot.event
async def on_webhooks_update(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
            if entry.user.id not in WHITELIST and not entry.user.guild_permissions.administrator:
                webhooks = await channel.webhooks()
                for wh in webhooks:
                    if wh.user and wh.user.id == entry.user.id:
                        await wh.delete(reason="Anti-Webhook Spam")
    except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    global is_defending
    is_defending = True
    await ctx.send("🔒 Bloqueando servidor...")
    try:
        await ctx.guild.edit(verification_level=discord.VerificationLevel.highest)
        for ch in ctx.guild.text_channels:
            try:
                await ch.edit(slowmode_delay=15)
                await ch.set_permissions(ctx.guild.default_role, send_messages=False)
            except Exception as e:
                print(f"No pude bloquear {ch.name}: {e}")
        await ctx.send(f"🛡️ Servidor en lockdown. Usa `!unlock`")
    except Exception as e:
        await ctx.send(f"❌ Error: No tengo permisos. Asegúrate que mi rol está arriba del todo. {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    global is_defending, join_cache, msg_global
    is_defending = False
    join_cache = []
    msg_global = []
    try:
        await ctx.guild.edit(verification_level=discord.VerificationLevel.low)
        for ch in ctx.guild.text_channels:
            try:
                await ch.edit(slowmode_delay=0)
                await ch.set_permissions(ctx.guild.default_role, overwrite=None)
            except: pass
        await ctx.send("🔓 Servidor restaurado.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
