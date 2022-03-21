import asyncio
from asyncio.proactor_events import _ProactorBaseWritePipeTransport
import dataclasses
import datetime
from email.headerregistry import Address
import logging
import math
import multiprocessing
import os
import random
import signal
import time
import traceback
import typing
import pickle
import os
import sys
from unicodedata import numeric
import discord
import jsonpickle
import openai

DISCORD_TOKEN = "OTUzMjA4MTkyOTU4MDkxMzM1.YjBOTg.UgfIhHhiRbLIt1-SEX6n0LtmNvw"  # Get one here: https://discord.com/developers/applications/
OPENAI_API_KEY = "sk-hhmt0YZxBvLUyBolMj93330e0WVy5upUdsQKA2cE"  # https://beta.openai.com/account/api-keys
OPENAI_ORGANIZATION = "org-9zM1S4qv2Ja3oN1mNay53Lu4"
SETTINGS = {'temperature': 0.0,
                  'top_p': 1,
                  'max_tokens': 1952,
                  'presence_penalty': 0.45,
                  'frequency_penalty': 0.65,
                  'best_of': 1,
                  'engine': "text-davinci-002"
                  }
PREFIX = '.'
CLEANUP = 60
VERIFY_CHANNEL = 885760989608431636  # Yannic Kilcher "_verification"
VERIFIED_ROLE = 821375158295592961  # Yannic Kilcher "verified"
ALLOWED_CHANNEL = 953210271600635914  # Yannic Kilcher "gpt3"
MESSAGE_CHANNEL = 953210271600635914  # Yannic Kilcher "bot-chat"
ALLOWED_GUILD = 950816238882418728  # Yannic Kilcher
SHITPOSTING_CHANNEL = 736963923521175612
PRUNING_DAYS = 60
ADMIN_USER = [952850561340948541, 690665848876171274 ]  # ClashLuke, Endomorphosis 
ROLES = {'reinforcement-learning': 760062682693894144, 'computer-vision': 762042823666171955, 'natural-language-processing': 762042825260007446, 'meetup': 782362139087208478, 'verified': 821375158295592961, 'homebrew-nlp': 911661603190079528, 'world-modelz': 914229949873913877 }

APPROVAL_EMOJI: typing.Union[str, discord.Emoji] = "yes"
DISAPPROVAL_EMOJI: typing.Union[str, discord.Emoji] = "noo"
LOG_LEVEL = logging.DEBUG

openai.api_key = OPENAI_API_KEY
openai.organization = OPENAI_ORGANIZATION

FALLBACKS = []
CHANNEL: typing.Optional[discord.TextChannel] = None


class ExitFunctionException(Exception):
    pass


@dataclasses.dataclass
class Context:
    client: discord.Client
    message: discord.Message
    sources: dict
    settings: dict

    fired_messages: typing.List[asyncio.Task]


def fire(ctx: Context, *coroutine: typing.Union[typing.Coroutine, typing.Iterable[typing.Coroutine]]) -> None:
    if len(coroutine) == 0:
        coroutine = coroutine[0]
    if isinstance(coroutine, typing.Coroutine):
        coroutine = [coroutine]
    ctx.fired_messages.extend([asyncio.create_task(coro) for coro in coroutine])


def debug(message: typing.Any):
    if LOG_LEVEL <= logging.DEBUG:
        print(message)


async def discord_check(ctx: Context, check: bool, response: str):
    if check:
        channel: discord.TextChannel = ctx.message.channel
        fire(ctx, channel.send(response, reference=ctx.message))
        raise ExitFunctionException


def local_check(check: bool, message: str):
    if check:
        debug(message)
        raise ExitFunctionException


def call_gpt(prompt, settings):
    value = openai.Completion.create(prompt=prompt,  engine="text-davinci-002",  temperature=0.0,  max_tokens=1952,   top_p=1, frequency_penalty=0,  presence_penalty=0    )["choices"][0]["text"]
    return (value)
    
async def basic_check(ctx: Context, permission, dm=False):
    channel: discord.TextChannel = ctx.message.channel
    await discord_check(ctx, not dm and not hasattr(channel, "guild"), "This command can't be used in DM.")
    await discord_check(ctx, dm and hasattr(channel, "guild"), "This command only be used in DM.")
    if not dm:
        guild: discord.Guild = channel.guild
        await discord_check(ctx, not channel.id == MESSAGE_CHANNEL or not guild.id == ALLOWED_GUILD,
                            "Insufficient permission. This bot can only be used in its dedicated channel on the "
                            "\"JusticeDAO\" discord server.")
    if permission:
        author: discord.User = ctx.message.author
        await discord_check(ctx, author.id not in ADMIN_USER,
                            "Insufficient permission. Only the owners of this bot are allowed to run this command. "
                            "Try .add instead")

async def print_pdf(ctx: Context, pdf_url: str):
    channel: discord.TextChannel = ctx.message.channel
    fire(ctx, channel.send(pdf_url, file=discord.File(pdf_url)))

async def startover(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    author: discord.User = ctx.message.author
    fire(ctx, channel.send("Alright, let's start over."))
    if os.path.exists(f"{author.id}.pkl"):
        with open(f"{author.id}.pkl", "rb") as f:
            complaint_data = pickle.load(f)
    complaint_data = {}
    outfile = open(f"{author.id}.pkl", "wb")
    with open(f"{author.id}.pkl", "wb") as f:
        pickle.dump(complaint_data, f)

def is_a_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

async def complaint(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    author: discord.User = ctx.message.author

    #fire(ctx, channel.send("This command is temporarily gone, but will be back in the future! Use .add instead.", reference=ctx.message))
    #await basic_check(ctx, True)
    await basic_check(ctx, False, True)
    #await channel.send(call_gpt(ctx.message.content[len('.complaint '):], settings))
    message = ctx.message.content[len('.complaint '):]
    if os.path.exists(f"{author.id}.pkl"):
        with open(f"{author.id}.pkl", "rb") as f:
            complaint_data = pickle.load(f)
    else :
        complaint_data = {}
    if "message_history" not in complaint_data:
        complaint_data["message_history"] = []

    if "stage" not in complaint_data:   
        complaint_data["stage"] = 0
    
    if "last_modified" not in complaint_data:
        complaint_data["last_modified"] = datetime.datetime.now()


    if complaint_data["last_modified"] < datetime.datetime.now() - datetime.timedelta(hours=1):
        complaint_data["stage"] = 0
        complaint_data["last_modified"] = datetime.datetime.now()
    if complaint_data["stage"] == 0:
        fire(ctx, channel.send("We have not talked in a long time\n\n"))    
        if "complaint" not in complaint_data:
            #generate_complaint = call_gpt('Generate  a detailed legal lawsuit from this complaint: \n """' + message + ' \n """  ', SETTINGS)
            generated_questions = call_gpt('Generate a list of questions that an attorney would ask their client about this legal lawsuit. \n """' + message + ' \n """  ', SETTINGS)
            questions = generated_questions.split("?")
            complaint_data["complaint"] = message
            for i in range(0, len(questions)):
                questions[i] = questions[i].replace("\n", "").replace("-", "")
                if is_a_number(questions[i].split(".")[0]):
                    questions[i] = questions[i].split(".")[1].lstrip().replace("\n", "").replace("-", "")
                if isempty(questions[i]) == True:
                    questions.pop(i)
            
            complaint_data["questions"] = questions
            complaint_data["last_question"] = questions[0] 
            fire(ctx, channel.send(questions[0] + "? use the .answer command.", reference=ctx.message))
            complaint_data["stage"] = 1
            with open(f"{author.id}.pkl", "wb") as f:
                pickle.dump(complaint_data, f)
    else:
        fire(ctx, channel.send("Here is your complaint, try .startover to start over"))
        fire(ctx, channel.send(complaint_data["complaint"]))
        if complaint_data["questions"] is not None:
            fire(ctx, channel.send(complaint_data["questions"][0] + "?, use the .answer command.", reference=ctx.message))
    complaint_data["last_modified"] = datetime.datetime.now()
    complaint_data["stage"] = 1

    with open(f"{author.id}.pkl", "wb") as f:
        pickle.dump(complaint_data, f)

def isempty(s):
    return not s or not s.strip()
    
async def answer(ctx: Context):
    author: discord.User = ctx.message.author
    channel: discord.TextChannel = ctx.message.channel
    if os.path.exists(f"{author.id}.pkl"):
        with open(f"{author.id}.pkl", "rb") as f:
            complaint_data = pickle.load(f)

    if "last_question" not in complaint_data or complaint_data["stage"] < 1:
        complaint_data["last_question"] = ""
        fire(ctx, channel.send("You have not started a complaint yet. Use .complaint to start one.", reference=ctx.message))
        return

    answer = ctx.message.content[len('.answer '):]
    if "answered_questions" not in complaint_data:
        complaint_data["answered_questions"] = {}   
    if answer != "":
        complaint_data["answered_questions"][complaint_data["last_question"]] = answer
        if len(complaint_data["questions"]) > 1:
            complaint_data["questions"].pop(0)

    if "questions" not in complaint_data :
        complaint_data["questions"] = []
    if len(complaint_data["questions"]) == 0:
        summarize_text = str('Generate a very long detailed summary about the Plaintiff\'s legal complaint from this conversation: \n """')
        
        for question in complaint_data["answered_questions"]:
            summarize_text = summarize_text + "Lawyer: " + question  + "? \n"
            summarize_text = summarize_text + "Plaintiff: "  +  complaint_data["answered_questions"][question] + "\n"
        summarize_text = summarize_text + '"""'
        generate_complaint = call_gpt(summarize_text, SETTINGS)
        summarize_text2 = str('combine these two very long detailed summaries about the Defendant\'s legal complaint """')
        summarize_text2 = summarize_text2 + complaint_data["complaint"]+ "\n"
        summarize_text2 = summarize_text2 + generate_complaint + "\n" + '""" ' 
        new_complaint = call_gpt(summarize_text2, SETTINGS)
        complaint_data["complaint"] = new_complaint
        generated_questions = call_gpt('Generate a list of questions that an attorney would ask their client about this legal lawsuit. \n """' + complaint_data["complaint"] + ' \n """  ', SETTINGS)
        generated_questions_list = generated_questions.split("?")

        for i in range(len(generated_questions_list)):
            generated_questions_list[i] = generated_questions_list[i].replace("\n", "").replace("-", "")
            generated_questions_list[i] = generated_questions_list[i].lstrip()
            if is_a_number(generated_questions_list[i].split(".")[0]):
                generated_questions_list[i] = generated_questions_list[i].split(".")[1].lstrip().replace("\n", "").replace("-", "")
            if generated_questions_list[i] not in complaint_data["answered_questions"].keys() and isempty(generated_questions_list[i]) == False:
                complaint_data["questions"].append(generated_questions_list[i])

    if len(complaint_data["questions"]) == 0 or len(complaint_data["answered_questions"]) > 75:
        fire(ctx, channel.send("You have answered all the questions, congratulations! Use .startover to start over.", reference=ctx.message))
        
        complaint_data["stage"] = 2

    else:    
        fire(ctx, channel.send(complaint_data["questions"][0] + "? use the .answer command. to answer", reference=ctx.message))
        complaint_data["last_question"] = complaint_data["questions"][0]
        complaint_data["questions"].pop(0)
        complaint_data["last_modified"] = datetime.datetime.now()
    

    pickle.dump(complaint_data, open(f"{author.id}.pkl", "wb"))
    return

def object_to_string(obj):
    import json
    return json.dumps(obj)

async def printdata(ctx: Context):
    import json
    author: discord.User = ctx.message.author
    channel: discord.TextChannel = ctx.message.channel
    if os.path.exists(f"{author.id}.pkl"):
        with open(f"{author.id}.pkl", "rb") as f:
            complaint_data = pickle.load(f)
    else:
        complaint_data = {}
    complaint_data["last_modified"] = None
    with open(f"{author.id}.json", "w") as f:
        json.dump(complaint_data, f)
        fire(ctx, channel.send("here is your log file", reference=ctx.message))
        fire(ctx, channel.send(file=discord.File(f"{author.id}.json")))

    return

async def prune(ctx: Context):
    channel: discord.TextChannel = ctx.client.get_channel(SHITPOSTING_CHANNEL)
    async for msg in channel.history(limit=None,
                                     before=datetime.datetime.now() - datetime.timedelta(days=PRUNING_DAYS)):
        try:
            fire(ctx, msg.delete())
        except discord.errors.NotFound:
            break


async def complete(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    author: discord.User = ctx.message.author
    message = ctx.message.content[len('.complete '):]
    if os.path.exists(f"{author.id}.pkl"):
        with open(f"{author.id}.pkl", "rb") as f:
            complaint_data = pickle.load(f)
    if complaint_data["stage"] < 2:
        fire(ctx, channel.send("You have not completed your complaint yet. Use .answer to answer questions.", reference=ctx.message))
        return

    summarize_text = '""" \n Plaintiff:' +  complaint_data["complaint"] + "\n"
    for question in complaint_data["answered_questions"]: 
            summarize_text = summarize_text + "Lawyer: " + question  + "? \n"
            summarize_text = summarize_text + "Client: "  +  complaint_data["answered_questions"][question] + "\n"
    summarize_text = summarize_text + '""" \n'
    complaint_data["extracted_data"] = {}
    form_questions = [
        "What is the name of the defendant",
        "What is the name of the plaintiff",
        "What is the plaintiff's address",
        "What is the defendant's address",
        "What is the plaintiff's phone number",
        "What is the defendant's phone number",
        "What is the plaintiff's email address",
        "What is the defendant's email address",
        "What is the plaintiff's state",
        "What is the defendant's state",
        "What is the plaintiff's city",
        "What is the defendant's city",
        "What is the plaintiff's zip code",
        "What is the defendant's zip code",
    ].sort()

    for item in form_questions:
        if item not in complaint_data["answered_questions"].keys():
            complaint_data["questions"].append(item)
        
    if len(complaint_data["questions"]) > 0:
        complaint_data["stage"] = 1
        fire(ctx, channel.send(complaint_data["questions"][0].replace("?", "").replace("\n", "") + "? answer with .answer", reference=ctx.message))
        complaint_data["last_question"] = complaint_data["questions"][0].replace("?", "").replace("\n", "")
        with open(f"{author.id}.pkl", "wb") as f:
            pickle.dump(complaint_data, f)
        return()
    
    prompt  = "Does the complaint involve a federeal question of law? \n"
    complaint_data["extracted_data"][prompt] = call_gpt(prompt + summarize_text, SETTINGS)
    if "yes" in complaint_data["extracted_data"][prompt].lower():
        prompt  = "Generate the Numbered List the specific federal statutes, federal treaties, and/or provisions of the United States Constitution that are at issue in this case."
        complaint_data["extracted_data"][prompt] = call_gpt(prompt + summarize_text, SETTINGS)
    
    prompt  = "Does the complaint involve citizens of different states? \n"    
    complaint_data["extracted_data"][prompt] = call_gpt(prompt + summarize_text, SETTINGS)
    prompt  = "does the complaint involve an amount above $75,000? \n"
    complaint_data["extracted_data"][prompt] = call_gpt(prompt + summarize_text, SETTINGS)
    prompt  = "Write a short and plain statement of the legal claim. Do not make legal arguments. State as briefly as possible the facts showing that each plaintiff is entitled to the damages or other relief sought. State how each defendant was involved and what each defendant did that caused the plaintiff harm or violated the plaintiff's rights, including the dates and places of that involvement or conduct."
    complaint_data["extracted_data"][prompt] = call_gpt(prompt + summarize_text, SETTINGS)
    prompt  = "State briefly and precisely what damages or other relief the plaintiff asks the court to order. Do not make legal arguments. Include any basis for claiming that the wrongs alleged are continuing at the present time. Include the amounts of any actual damages claimed for the acts alleged and the basis for these amounts. Include any punitive or exemplary damages claimed, the amounts, and the reasons the plaintiff claims they are entitled to actual or punitive money damages."
    complaint_data["extracted_data"][prompt] = call_gpt(prompt + summarize_text, SETTINGS)

    if len(complaint_data["questions"]) > 0:
        complaint_data["stage"] = 1
        fire(ctx, channel.send( complaint_data["questions"][0].replace("\n","").replace("?","") + "? Use .answer ", reference=ctx.message))
        
    else:
        complaint_data["stage"] = 3
        fire(ctx, channel.send("Your complaint is complete, use .format to clean up the data", reference=ctx.message))
        pass

    with open(f"{author.id}.pkl", "wb") as f:
        pickle.dump(complaint_data, f)
    
    return

async def format(ctx: Context):
    import json
    channel: discord.TextChannel = ctx.message.channel
    author: discord.User = ctx.message.author
    message = ctx.message.content[len('.format '):]
    if os.path.exists(f"{author.id}.pkl"):
        with open(f"{author.id}.pkl", "rb") as f:
            complaint_data = pickle.load(f)
    complaint_data["results"] = {}
    for item in complaint_data["extracted_data"]:
        question = item
        answer = complaint_data["extracted_data"][item]
        if "what is the" in question.lower():        
            if "is" in answer.lower():
                answer = answer.split("is")[1].strip().replace(":", "")
                complaint_data["results"][item.replace("What is the", "").replace("?", "").replace("\n", "").lstrip().strip()] = answer.lstrip().capitalize()
        
        if "state" in item.lower():
            if "from" in answer.lower():
                complaint_data["results"][item.replace("What is the", "").replace("?", "").replace("\n","").lstrip().strip()] = answer.lower().replace("from","").lstrip().capitalize()

        if "Does the complaint involve a federeal question of law?" in item:
            if "yes" in complaint_data["extracted_data"][item].lower():
                complaint_data["results"]["federal_question"] = True
            elif "no" in complaint_data["extracted_data"][item].lower():
                complaint_data["results"]["federal_question"] = False                 

        if "State briefly and precisely what damages" in item:
            complaint_data["results"]["relief"] = answer.replace("\n", " ")

        if "Write a short and plain statement of the legal claim" in item:
            complaint_data["results"]["claim"] = answer.replace("\n", " ")

        if "does the complaint involve an amount above $75,000?" in item:
            if "yes" in answer.lower():
                complaint_data["results"]["controversy_amount"] = True
            elif "no" in answer.lower():
                complaint_data["results"]["controversy_amount"] = False

    if "plaintiff's zip code" in complaint_data["results"].keys() and "plaintiff's address" in complaint_data["results"].keys():
        if complaint_data["results"]["plaintiff's zip code"] not in complaint_data["results"]["plaintiff's address"] and len(complaint_data["results"]["plaintiff's address"]) > 0:
            complaint_data["results"]["plaintiff's address"] = complaint_data["results"]["plaintiff's address"] + " " + complaint_data["results"]["plaintiff's zip code"]

    if "defendant's zip code" in complaint_data["results"].keys() and "defendant's address" in complaint_data["results"].keys():
        if complaint_data["results"]["defendants's zip code"] not in complaint_data["results"]["defendants's address"] and len(complaint_data["results"]["defendants's address"]) > 0:
            complaint_data["results"]["defendants's address"] = complaint_data["results"]["defendants's address"] + " " + complaint_data["results"]["defendants's zip code"]

    if "defendant's state" in complaint_data["results"].keys() and "plaintiff's state" in complaint_data["results"].keys():
        if complaint_data["results"]["defendant's state"].lower() == complaint_data["results"]["plaintiff's state"].lower():
            complaint_data["results"]["Diversity"] = False
        else:
            complaint_data["results"]["Diversity"] = True


    with open(f"{author.id}.pkl", "wb") as f:
        pickle.dump(complaint_data, f)
    fire(ctx, channel.send(json.dumps(f"{complaint_data['results']}"), reference=ctx.message))
    return



async def pdf(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    author: discord.User = ctx.message.author
    message = ctx.message.content[len('.complete '):]
    if os.path.exists(f"{author.id}.pkl"):
        with open(f"{author.id}.pkl", "rb") as f:
            complaint_data = pickle.load(f)
    if complaint_data["stage"] < 3:
        fire(ctx, channel.send("You have not completed enough details to generate your complaint, please use .complete" , reference=ctx.message))
        return
    
async def verify(ctx: Context):
    if ctx.message.channel.id == VERIFY_CHANNEL:
        fire(ctx,
             ctx.message.author.add_roles(discord.utils.get(ctx.message.guild.roles, id=VERIFIED_ROLE)),
             ctx.message.delete(delay=1))


async def add(ctx: Context):
    await basic_check(ctx, False, True)

    query = ctx.message.content[len('.add '):]
    author_id = ctx.message.author.id
    reply = await CHANNEL.send(f"<@{author_id}> added ```\n{query}``` to the queue. You can vote on it by clicking the "
                               f":{APPROVAL_EMOJI.name}: or :{DISAPPROVAL_EMOJI.name}: reactions.\n\nTo add a query "
                               f"yourself, send me a message like `.add YOUR PROMPT HERE` via DM!")
    fire(ctx, reply.add_reaction(APPROVAL_EMOJI), reply.add_reaction(DISAPPROVAL_EMOJI))

    ctx.sources[reply.id] = (query, author_id)


async def delete(ctx: Context):
    await basic_check(ctx, False, True)
    channel: discord.TextChannel = ctx.message.channel
    query = ctx.message.content[len('.delete '):]
    author_id = ctx.message.author.id
    deleted = False
    for reply_id, (qry, qry_author_id) in ctx.sources.items():
        if author_id == qry_author_id and qry == query:
            del ctx.sources[reply_id]
            fire(ctx, channel.send(f"Removed query.", reference=ctx.message),
                 (await CHANNEL.fetch_message(reply_id)).delete())
            deleted = True
            break
    if not deleted:
        fire(ctx, channel.send(f"Didn't find query.", reference=ctx.message))


async def role(ctx: Context):
    await basic_check(ctx, False)
    query = ctx.message.content[len('.role '):]
    channel: discord.TextChannel = ctx.message.channel

    if query in ROLES:
        author: discord.Member = ctx.message.author
        guild: discord.Guild = ctx.message.guild
        queried_role: discord.Role = guild.get_role(ROLES[query])
        for role in author.roles:
            role: discord.Role = role
            if role == queried_role:
                fire(ctx, author.remove_roles(role), channel.send(f"Removed role", reference=ctx.message))
                return
        fire(ctx, author.add_roles(queried_role), channel.send(f"Added role", reference=ctx.message))
    else:
        fire(ctx, channel.send(f"Couldn't find role", reference=ctx.message))


async def add_fallback(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    await basic_check(ctx, True)

    query = ctx.message.content[len('.add_fallback '):]
    FALLBACKS.append(query)

    fire(ctx, channel.send(f"Added query to the fallback list. There are now {len(FALLBACKS)} queries in said list.",
                           reference=ctx.message))


async def await_ctx(ctx: Context):
    for msg in ctx.fired_messages:
        await msg
    ctx.fired_messages.clear()


async def restart(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    await basic_check(ctx, True)

    fire(ctx, channel.send(f"Restarting", reference=ctx.message), dump_queue(ctx))
    await await_ctx(ctx)

    os.system("python3 bot.py")
    os.kill(os.getppid(), signal.SIGTERM)


async def settings(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    fire(ctx,
         channel.send(''.join(["gpt3:\n\t", '\n\t'.join(sorted([f"{k}={v}" for k, v in ctx.settings['gpt3'].items()])),
                               '\n'
                               'bot:\n\t', '\n\t'.join(sorted([f"{k}={v}" for k, v in ctx.settings['bot'].items()]))]),
                      reference=ctx.message))


async def dump_queue(ctx: Context):
    await basic_check(ctx, True)
    with open("queue_dump.json", 'w') as f:
        f.write(jsonpickle.dumps(dict(ctx.sources), indent=4))
    channel: discord.TextChannel = ctx.message.channel
    fire(ctx, channel.send("Dumped queue.", reference=ctx.message))


async def dump_settings(ctx: Context):
    await basic_check(ctx, True)
    with open("setting_dump.json", 'w') as f:
        f.write(jsonpickle.dumps({key: dict(val) for key, val in ctx.settings.items()}, indent=4))
    channel: discord.TextChannel = ctx.message.channel
    fire(ctx, channel.send("Dumped settings.", reference=ctx.message))


async def dump_fallbacks(ctx: Context):
    await basic_check(ctx, True)
    with open("fallbacks.json", 'w') as f:
        f.write(jsonpickle.dumps(FALLBACKS, indent=4))
    channel: discord.TextChannel = ctx.message.channel
    fire(ctx, channel.send("Dumped fallbacks.", reference=ctx.message))


async def load_fallbacks(ctx: Context):
    await basic_check(ctx, True)
    with open("fallbacks.json", 'w') as f:
        fallbacks = jsonpickle.loads(f.read())
    FALLBACKS.clear()
    FALLBACKS.extend(fallbacks)
    channel: discord.TextChannel = ctx.message.channel
    fire(ctx, channel.send("Loaded fallbacks.", reference=ctx.message))


async def load_settings(ctx: Context):
    with open("setting_dump.json", 'r') as f:
        tmp = jsonpickle.loads(f.read())
    for top_key, top_val in tmp.items():
        for key, val in top_val.items():
            ctx.settings[top_key][key] = val
    await basic_check(ctx, True)
    channel: discord.TextChannel = ctx.message.channel
    fire(ctx, channel.send("Loaded settings.", reference=ctx.message))


async def load_queue(ctx: Context):
    with open("queue_dump.json", 'r') as f:
        tmp = jsonpickle.loads(f.read())
    for key, val in tmp.items():
        ctx.sources[key] = val
    await basic_check(ctx, True)
    channel: discord.TextChannel = ctx.message.channel
    fire(ctx, channel.send("Loaded queue.", reference=ctx.message))


async def eval_queue(ctx: Context):
    proposals = {}
    for answer_id, (prompt, user_id) in ctx.sources.items():
        message: discord.Message = await CHANNEL.fetch_message(answer_id)
        proposals[answer_id] = [0, user_id, prompt]
        for r in message.reactions:
            r: discord.Reaction = r
            e: discord.Emoji = r.emoji
            if e.name == DISAPPROVAL_EMOJI.name:
                proposals[answer_id][0] -= r.count
            elif e.name == APPROVAL_EMOJI.name:
                proposals[answer_id][0] += r.count
    return proposals


async def queue(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    proposals = await eval_queue(ctx)
    proposals = sorted([(count, prompt) for _, (count, _, prompt) in proposals.items()], reverse=True)
    if len(proposals) == 0:
        fire(ctx, channel.send("Queue is empty", reference=ctx.message))
        return
    fire(ctx, channel.send('\n\n\n'.join([f'PROMPT: ```\n{prompt[:40]}```Score: {count}'
                                          for count, prompt in proposals[:10]])
                           + f'..and {len(proposals) - 10} more' * (len(proposals) > 10), reference=ctx.message))


async def start(ctx: Context):
    channel: discord.TextChannel = ctx.client.get_channel(ALLOWED_CHANNEL)
    ctx.settings['bot']['started'] = 1

    while True:
        min_ln = math.log(ctx.settings['bot']['min_response_time'])
        max_ln = math.log(ctx.settings['bot']['max_response_time'])
        delay = math.e ** (random.random() * (max_ln - min_ln) + min_ln)
        print(f"Next delay: {int(delay / 60):3d} minutes")
        start_time = time.time()

        proposals = await eval_queue(ctx)
        if proposals:
            _, (count, _, _) = max(proposals.items(), key=lambda x: x[1][0])
            best, message_id, author = random.choice([(prompt, message_id, author_id)
                                                      for message_id, (score, author_id, prompt)
                                                      in proposals.items()
                                                      if score == count])
            if count < ctx.settings['bot']['min_score'] and ctx.settings['bot']['use_fallback']:
                prompt = random.choice(FALLBACKS)
                response = call_gpt(prompt, ctx.settings)
                prompt: discord.Message = await channel.send(f"PROMPT:\n```\n{prompt}```")
                fire(ctx, channel.send(f"RESPONSE:\n```\n{response}```", reference=prompt))
            elif count < ctx.settings['bot']['min_score'] and ctx.settings['bot']['show_no_score']:
                fire(ctx, channel.send("Nothing has any score, skipping this one."))
            else:
                response = call_gpt(best, ctx.settings)
                fire(ctx, channel.send(f"<@{author}>\nRESPONSE:```\n{response}```",
                                       reference=await channel.fetch_message(message_id)))
                del ctx.sources[message_id]
        elif ctx.settings['bot']['use_fallback']:
            prompt = random.choice(FALLBACKS)
            response = call_gpt(prompt, ctx.settings)
            prompt: discord.Message = await channel.send(f"PROMPT:\n```\n{prompt}```")
            fire(ctx, channel.send(f"RESPONSE:\n```\n{response}```", reference=prompt))
        elif ctx.settings['bot']['show_empty']:
            fire(ctx, channel.send("No prompts in queue, skipping this one."))

        await await_ctx(ctx)
        time.sleep(delay + start_time - time.time())  # Ensure delay stays the same


async def change_setting(ctx: Context):
    channel: discord.TextChannel = ctx.message.channel
    author: discord.User = ctx.message.author
    arguments = ctx.message.content.split(' ')[1:]
    await discord_check(ctx, len(arguments) != 3,
                        "Invalid number of arguments. Should be `group_name parameter_name value`")
    await discord_check(ctx, author.id not in ADMIN_USER,
                        "Invalid number of arguments. Should be `group_name parameter_name value`")
    group_name, parameter_name, value = arguments
    previous_value = ctx.settings[group_name][parameter_name]
    ctx.settings[group_name][parameter_name] = type(previous_value)(value)
    fire(ctx, channel.send(f"Changed {parameter_name} from {previous_value} to {value}", reference=ctx.message))


COMMANDS = {'change_setting': change_setting, 'settings': settings, 'add': add, 'complete': complete,
        'queue': queue, 'dump_queue': dump_queue, 'load_queue': load_queue,
            'dump_settings': dump_settings, 'load_settings': load_settings,
            'dump_fallbacks': dump_fallbacks, 'load_fallbacks': load_fallbacks, 'add_fallback': add_fallback,
            'delete': delete, 'role': role, 'format': format,
            'restart': restart, 'verify': verify, 'complaint': complaint, 'answer': answer, 'startover': startover, 'printdata': printdata
            }


async def bot_help(ctx: Context):
    fire(ctx, ctx.message.channel.send(f'Available Commands: `{"` `".join(sorted(list(COMMANDS.keys())))}`',
                                       reference=ctx.message))


COMMANDS['help'] = bot_help


async def process_spam(ctx: Context):
    content = ctx.message.content
    if not (('http://' in content or 'https://' in content) and ('disc' in content or 'disoc' in content) and
            ('gift' in content or 'gft' in content)):
        return
    author: discord.User = ctx.message.author
    server: discord.Guild = ctx.message.guild
    await ctx.message.delete()
    await server.kick(author, reason=f'Spam: {ctx.message.content}')


async def process_message(ctx: Context):
    fn_name = ctx.message.content[1:]

    if ' ' in fn_name:
        fn_name = fn_name[:fn_name.find(' ')]
    fire(ctx, process_spam(ctx))

    try:
        local_check(fn_name not in COMMANDS, "Unknown command")
        local_check(not ctx.message.content.startswith('.'), "Not a command")
    except ExitFunctionException:
        return

    try:
        await COMMANDS[fn_name](ctx)
    except ExitFunctionException:
        pass
    except Exception as exc:
        if LOG_LEVEL <= logging.ERROR:
            traceback.print_exc()


def init_fn(sources: dict, settings: dict, fn: typing.Union[start, prune]):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = discord.Client()

    @client.event
    async def on_message(message: discord.Message):
        return

    @client.event
    async def on_ready():
        global APPROVAL_EMOJI, DISAPPROVAL_EMOJI, CHANNEL
        if isinstance(APPROVAL_EMOJI, str):
            for emoji in client.emojis:
                emoji: discord.Emoji = emoji
                if emoji.name == APPROVAL_EMOJI:
                    APPROVAL_EMOJI = emoji
                if emoji.name == DISAPPROVAL_EMOJI:
                    DISAPPROVAL_EMOJI = emoji
            CHANNEL = client.get_channel(ALLOWED_CHANNEL)
        debug(f"{fn.__name__} logged in as {client.user.name}")
        await fn(Context(client, None, sources, settings, []))

    loop.create_task(client.start(DISCORD_TOKEN))
    loop.run_forever()
    loop.close()


def init(sources: dict, settings: dict):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = discord.Client()

    @client.event
    async def on_message(message: discord.Message):
        ctx: Context = Context(client, message, sources, settings, [])
        fire(ctx, process_message(ctx))
        await await_ctx(ctx)

    @client.event
    async def on_ready():
        global APPROVAL_EMOJI, DISAPPROVAL_EMOJI, CHANNEL
        if isinstance(APPROVAL_EMOJI, str):
            for emoji in client.emojis:
                emoji: discord.Emoji = emoji
                if emoji.name == APPROVAL_EMOJI:
                    APPROVAL_EMOJI = emoji
                if emoji.name == DISAPPROVAL_EMOJI:
                    DISAPPROVAL_EMOJI = emoji
            CHANNEL = client.get_channel(ALLOWED_CHANNEL)
        debug(f"Core logged in as {client.user.name}")

    loop.create_task(client.start(DISCORD_TOKEN))
    loop.run_forever()
    loop.close()


def backup(sources):
    while True:
        with open("queue_dump.json", 'w') as f:
            f.write(jsonpickle.dumps(dict(sources), indent=4))
        time.sleep(600)


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    _sources = manager.dict({})
    _gpt3 = manager.dict({})
    _bot = manager.dict({})
    _settings = manager.dict({})
    _gpt3.update({'temperature': 0.0,
                  'top_p': 1,
                  'max_tokens': 256,
                  'presence_penalty': 0.45,
                  'frequency_penalty': 0.65,
                  'best_of': 1,
                  'engine': "davinci"
                  })
    _bot.update({'min_response_time': 60,
                 'max_response_time': 60,
                 "started": 0,
                 'min_score': 0,
                 'show_no_score': 0,
                 'show_empty': 0,
                 'use_fallback': 0,
                 'max_synchronisation_delay_ms': 2000,
                 })
    _settings.update({'gpt3': _gpt3,
                      'bot': _bot
                      })

    procs = [multiprocessing.Process(target=init, args=(_sources, _settings), daemon=True),
             multiprocessing.Process(target=init_fn, args=(_sources, _settings, start), daemon=True),
             multiprocessing.Process(target=init_fn, args=(_sources, _settings, prune), daemon=True)]
    for t in procs:
        t.start()
    backup(_sources)
