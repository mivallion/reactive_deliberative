import asyncio
from time import sleep

from py_rete import Fact, Production, V, ReteNetwork

f1 = Fact(light_color="red")


@Production(V('fact') << Fact(light_color="red"))
async def make_green(net, fact):
    print('making green')
    fact['light_color'] = 'green'
    net.update_fact(fact)


@Production(V('fact') << Fact(light_color="green"))
async def make_red(net, fact):
    print('making red')
    fact['light_color'] = 'red'
    net.update_fact(fact)


net_lock = asyncio.Lock()

light_net = ReteNetwork()
light_net.add_fact(f1)
light_net.add_production(make_green)
light_net.add_production(make_red)


async def net_loop():
    async with net_lock:
        while 1:
            await light_net.run(1)
            await asyncio.sleep(1)


def create_net_loop():
    event_loop = asyncio.get_event_loop()
    return [event_loop.create_task(net_loop())]


async def main():
    for i in range(100):
        futures = create_net_loop()
        await asyncio.sleep(1)
        for f in futures:
            f.cancel()


asyncio.run(main())
