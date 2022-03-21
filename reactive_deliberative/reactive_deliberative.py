import asyncio

from py_rete import Fact, Production, V, ReteNetwork

class ReactiveDeliberative:
    def __init__(self, loop_delay=1):
        self.fact = Fact()
        self.network = ReteNetwork()
        self.network.add_fact(self.fact)
        self.loop_delay = loop_delay
        self.network_lock = asyncio.Lock()

        self.task = asyncio.get_event_loop().create_task(self._network_loop())

    def _get_fact_last_int_idx(self):
        return max([key for key in self.fact.keys() if isinstance(key, int)])

    async def _network_loop(self):
        async with self.network_lock:
            while 1:
                await self.network.run(1)
                await asyncio.sleep(self.loop_delay)

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
