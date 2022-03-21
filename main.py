import asyncio

from py_rete import Fact, Production, V
from reactive_deliberative.reactive_deliberative import ReactiveDeliberative


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


async def main():
    rd = ReactiveDeliberative()
    rd.add_fact("green", "light_color")
    rd.add_production(make_red)
    rd.add_production(make_green)
    await rd.task


asyncio.run(main())
