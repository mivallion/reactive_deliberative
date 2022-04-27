import asyncio
from typing import Callable, Coroutine, Awaitable

from py_rete import Fact, Production, V, ReteNetwork


class ReactiveDeliberative:
    def __init__(self, loop_delay=0):
        self.fact = Fact()
        self.network = ReteNetwork()
        self.network.add_fact(self.fact)
        self.loop_delay = loop_delay
        self.network_lock = asyncio.Lock()
        self.loop = asyncio.get_event_loop()
        self.task = self.loop.create_task(self._network_loop())
        self.reactive_tasks = []

    def run(self):
        self.loop.run_forever()

    def _get_fact_last_int_idx(self):
        return max([key for key in self.fact.keys() if isinstance(key, int)])

    async def _network_loop(self):
        while 1:
            async with self.network_lock:
                await self.network.run()
                await asyncio.sleep(0)

    def add_fact(self, value, parameter=None):
        if parameter is None:
            idx = self._get_fact_last_int_idx()
            self.fact[idx] = value
        else:
            self.fact[parameter] = value

        self.network.update_fact(self.fact)

    def remove_fact(self, parameter):
        del self.fact[parameter]

        self.network.update_fact(self.fact)

    def add_production(self, production):
        self.network.add_production(production)

    async def __reactive_action(self, predicate, callback, force):
        while True:
            if await predicate():
                if force:
                    self.task.cancel()
                await callback()
                if force:
                    self.task = self.loop.create_task(self._network_loop())

    def add_reactive_action(self, predicate, callback, force=True):
        task = asyncio.get_event_loop().create_task(self.__reactive_action(predicate, callback, force))
        self.reactive_tasks.append(task)
