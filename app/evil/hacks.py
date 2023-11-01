from rx.core.notification import OnNext, OnError
from asyncio import Queue
from rx.scheduler.eventloop import AsyncIOScheduler
import rx.operators as ops

# This magnificent file is a place to locate particularly hacky functions which, if present in-line in our
# otherwise impecable code, would do nothing but increase the risk of brain aneurisms in far-future aliens
# picking over the code repositories for our long-dead species.

# ridiculous hack to transform an observable into an async generator
async def observer2asyncgen(obs, loop):
    queue = Queue()
    def on_next(i):
        queue.put_nowait(i)
    disposable = obs.pipe(ops.materialize()).subscribe(
        on_next=on_next,
        scheduler=AsyncIOScheduler(loop=loop)
    )
    while True:
        i = await queue.get()
        if isinstance(i, OnNext):
            yield i.value
            queue.task_done()
        elif isinstance(i, OnError):
            disposable.dispose()
            raise(Exception(i.value))
        else:
            disposable.dispose()
            break
