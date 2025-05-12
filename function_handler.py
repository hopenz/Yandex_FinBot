import json
from aiogram import types
from main import bot, dp

async def handler(event, context):
    if event.get("httpMethod") == "GET":
        return {"statusCode": 200, "body": "Bot is running"}
    if event.get("body"):
        update = types.Update(**json.loads(event["body"]))
        await dp.feed_update(bot, update, context=context)
        return {"statusCode": 200, "body": "OK"}
    return {"statusCode": 400, "body": "No body"}