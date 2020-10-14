import discord
import asyncio
import cs50

from cs50 import SQL
from discord.ext import commands

# SETUP
client = commands.Bot(command_prefix = '.') # bot
db = SQL("sqlite:///Bank.db")

account_message = "You don't have an account. To create an account type '.account' in the chat."

def add_account(member):
    name = member.name
    id = member.id

    # Check if member already has an account
    rows = db.execute("SELECT * FROM accounts WHERE id = :id", id=id)

    if len(rows) == 0:
        db.execute("INSERT INTO accounts (id, name, cash) VALUES (:id, :name, :cash)",
         id=id, name=name, cash=200)

@client.event
async def on_ready():
    print('bot is gay')

# Censor words
@client.event
async def on_message(message):
    # Gets words user is allowed to use
    permissions = db.execute("SELECT * FROM permissions WHERE user_id = :user_id", user_id=message.author.id)
    allowed = [ i["word"] for i in permissions ]
    # Gets all the words that the user is not allowed to use
    owners = db.execute("SELECT * FROM owners")
    not_allowed = [ i["word"] for i in owners if i["word"] not in allowed ]

    # Censor
    res = [word for word in not_allowed if(word in message.content)]
    if bool(res) and message.author.id != client.user.id: # The 2nd expression assures the bot doesn't censor itself
        await message.delete()

    await client.process_commands(message)

@client.event
async def on_member_join(member):
    add_account(member)

@client.command()
async def account(ctx):
    add_account(ctx.author)

@client.command()
async def cash(ctx, member : discord.Member=None):
    # if member field is null just get the sender's info
    if not member:
        member = ctx.author

    id = member.id
    rows = db.execute("SELECT * FROM accounts WHERE id = :id", id=id)

    # Checks if member has an account
    if not len(rows) == 0:
        await ctx.send(rows[0]["name"] + " has $" + str(rows[0]["cash"]))
    else:
        await ctx.send(member.name + " does not have an account.")

@client.command()
async def words(ctx, member : discord.Member=None):
    # if member field is null just get the sender's info
    if not member:
        member = ctx.author

    id = member.id
    rows = db.execute("SELECT * FROM owners WHERE owner_id = :id", id=id)

    lines = []

    lines.append(member.name + " owns:")
    for row in rows:
        lines.append(row["word"])

    await ctx.send("\n".join(lines))

@client.command(aliases=['give$'])
async def give_money(ctx, receiver : discord.Member=None, amount=None):
    giver = ctx.author

    # if member field is null just get the sender's info
    if not receiver:
        await ctx.send("Must provide receiver.")
    else:
        giver_account = db.execute("SELECT * FROM accounts WHERE id = :id", id=giver.id)
        receiver_account = db.execute("SELECT * FROM accounts WHERE id = :id", id=receiver.id)

        # Checks if member has an account
        if len(giver_account) == 0:
            ctx.send(giver.name + " does not have an account.")
        elif len(giver_account) == 0:
            ctx.send(receiver.name + " does not have an account.")
        elif not int(amount):
            await ctx.send("Must provide transaction amount.")
        elif int(amount) > giver_account[0]["cash"]:
            await ctx.send("You don't have enough money to make this transaction.")
        else:
            giver_cash = giver_account[0]["cash"]-int(amount)
            receiver_cash = receiver_account[0]["cash"]+int(amount)
            db.execute("UPDATE accounts SET cash = :cash WHERE id = :id", cash=giver_cash, id=giver.id)
            db.execute("UPDATE accounts SET cash = :cash WHERE id = :id", cash=receiver_cash, id=receiver.id)

@client.command(aliases=['giveW'])
async def give_word(ctx, receiver : discord.Member=None, *, word=None):
    giver = ctx.author

    # if member field is null just get the sender's info
    if not receiver:
        await ctx.send("Must provide receiver.")
    else:
        # Checks if giver owns word
        rows = db.execute("SELECT * FROM owners WHERE word = :word AND owner_id = :id", word=word, id=ctx.author.id)
        if len(rows) == 0:
            await ctx.send("You don't own this word.")
        else:
            # Change owner of word
            db.execute("UPDATE owners SET owner_id = :id WHERE word = :word", id=receiver.id, word=word)
            db.execute("UPDATE permissions SET user_id = :id WHERE word = :word", id=receiver.id, word=word)

@client.command()
async def rank(ctx, n=None):
    output = []
    # Gets user account and rank
    user_account = db.execute("SELECT * FROM ( SELECT id, name, cash, RANK () OVER ( ORDER BY cash DESC) rank FROM accounts) t WHERE id = :id;", id=ctx.author.id)
    if len(user_account) == 0:
        output.append(account_message)
    else:
        output.append("Your rank is " + str(user_account[0]["rank"]) + "\n")

    # Gets top n people
    if not n:
        n = 3
    if not int(n):
        n = 3
    output.append("The top " + str(n) + " people are:")
    leaderboard = db.execute("SELECT * FROM ( SELECT id, name, cash, RANK () OVER ( ORDER BY cash DESC) rank FROM accounts) t WHERE rank <= :rank;", rank=int(n))
    for account in leaderboard:
        output.append("\t" + str(account["rank"]) + ". " + account["name"] + " $" + str(account["cash"]) )

    await ctx.send("\n".join(output))

@client.command()
async def allow(ctx, member : discord.Member, *, word=None):
    # Checks if user has ownership
    rows = db.execute("SELECT * FROM owners WHERE word = :word AND owner_id = :id", word=word, id=ctx.author.id)
    if len(rows) == 0:
        await ctx.send("You don't own this word.")
    else:
        # Checks if member already has permission
        rows = db.execute("SELECT * FROM permissions WHERE word = :word AND user_id = :id", word=word, id=member.id)
        if len(rows) != 0:
            await ctx.send(member.name + " already has permission.")
        else:
            db.execute("INSERT INTO permissions (word, user_id) VALUES (:word, :user_id)",
            word=word, user_id=member.id)

@client.command()
async def deny(ctx, member : discord.Member, *, word=None):
    # Checks if user has ownership
    rows = db.execute("SELECT * FROM owners WHERE word = :word AND owner_id = :id", word=word, id=ctx.author.id)
    if len(rows) == 0:
        await ctx.send("You don't own this word.")
    elif member.id == ctx.author.id:
        await ctx.send("Can't deny yourself permission!")
    else:
        # Checks if member already has permission
        db.execute("DELETE FROM permissions WHERE word=:word AND user_id=:id;", word=word, id=member.id)

@client.command()
async def purchase(ctx, *, word=None):
    cost = 50
    if not word:
        await ctx.send("Must provide word")
    else:
        buyer_account = db.execute("SELECT * FROM accounts WHERE id = :id", id=ctx.author.id)
        if len(buyer_account) == 0:
            await ctx.send(account_message)
        elif buyer_account[0]["cash"] < cost:
            await ctx.send("You don't have enough money to make the purchase.")
        elif word[0] == ".":
            await ctx.send("Can't buy a command")
        elif len(word) < 3:
            await ctx.send("Word too short")
        else:
            rows = db.execute("SELECT * FROM owners WHERE word = :word", word=word)
            if len(rows) != 0:
                await ctx.send("Someone has already made this purchase")
            else:
                buyer_cash = buyer_account[0]["cash"] - cost
                db.execute("UPDATE accounts SET cash = :cash WHERE id = :id", cash=buyer_cash, id=ctx.author.id)

                # Update owners
                db.execute("INSERT INTO owners (word, owner_id) VALUES (:word, :owner_id)",
                word=word, owner_id=ctx.author.id)
                # Update permissions
                db.execute("INSERT INTO permissions (word, user_id) VALUES (:word, :user_id)",
                word=word, user_id=ctx.author.id)


client.run('NzUyMzQxMzQ5NzAwODYxOTcz.X1WOew.M8fJ7OXqmiyD6Fk_BtVNX2wCGa4')
