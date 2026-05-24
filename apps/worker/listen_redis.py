import asyncio
import redis.asyncio as aioredis
from uuid import uuid4

async def main():
    redis_client = aioredis.from_url("rediss://default:**@top-tomcat-133300.upstash.io:6379//", decode_responses=True)
    async with redis_client.pubsub() as pubsub:
        await pubsub.psubscribe("scan:*")
        print("Subscribed to scan:* channels. Waiting for events...")
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg:
                print(msg)

asyncio.run(main())
