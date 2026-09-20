# ... (mantén todo lo anterior y añade esto arriba con Flask)
from flask import request

# ... dentro de Flask app

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig = request.headers.get('Stripe-Signature')
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except:
        return "Error", 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = int(session['metadata']['user_id'])
        role_name = session['metadata']['role']
        # Aquí asignamos el rol
        guild = discord.utils.get(bot.guilds) # coge el primer server
        async def assign():
            await bot.wait_until_ready()
            member = guild.get_member(user_id)
            role = discord.utils.get(guild.roles, name=role_name)
            if member and role:
                await member.add_roles(role)
        bot.loop.create_task(assign())
    return "OK", 200
