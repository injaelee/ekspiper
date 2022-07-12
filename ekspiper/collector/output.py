

class FluentCollector(Collector):
    def __init__(self,
        fluent_sender: FluentSender,
    ):
        self.fluent_sender = fluent_sender

    async def process(self,
        entry: Dict[str, Any]
    ):
        logger.info("[ForwardBookOffersAsyncProcessor] Start iteration")

        for offer in entry.get("result", {}).get("offers", []):
            self.fluent_sender.emit("bookoffer", offer)

        logger.info("[ForwardBookOffersAsyncProcessor] Done iteration")
        
