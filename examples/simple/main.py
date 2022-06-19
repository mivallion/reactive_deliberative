import asyncio

from reactive_deliberative import Fact, Production, V
from reactive_deliberative import ReactiveDeliberative

i = 0


async def counter_predicate():
    global i
    i += 1
    await asyncio.sleep(0)
    return i == 10000000


async def counter_reactive():
    global i
    i = 0
    print('c')
    await asyncio.sleep(0)


@Production(V('fact') << Fact(light_color="red"), timeout=10)
async def make_green(net, fact):
    print('making green')
    fact['light_color'] = 'green'
    net.update_fact(fact)
    await asyncio.sleep(0)


@Production(V('fact') << Fact(light_color="green"), timeout=10)
async def make_red(net, fact):
    print('making red')
    fact['light_color'] = 'red'
    net.update_fact(fact)
    await asyncio.sleep(0)


@Production(V('fact') << Fact(light_color="green"), priority=2, timeout=10)
def make_red_high_priority(net, fact):
    print('making red high priority')
    fact['light_color'] = 'red'
    net.update_fact(fact)


if __name__ == '__main__':
    rd = ReactiveDeliberative()
    rd.add_fact("green", "light_color")
    rd.add_production(make_red)
    rd.add_production(make_green)
    rd.add_production(make_red_high_priority)
    rd.add_reactive_action(counter_predicate, counter_reactive, force=False)
    rd.run()
