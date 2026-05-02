import asyncio
from composer import compose_message

async def main():
    cat = {'slug': 'dentists', 'voice': {'tone': 'professional'}}
    merch = {'identity': {'name': 'Dr. Smith'}}
    trig = {'kind': 'perf_spike', 'payload': {'delta_pct': 45, 'metric': 'profile views', 'reason': 'weekend surge'}}
    
    print('Calling compose_message...')
    result = await compose_message(cat, merch, trig)
    print('Result:', result)

asyncio.run(main())
