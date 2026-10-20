from .domain import SUMMARY_MODEL, SummaryFailure


class HermesModel:
    def __init__(self, ctx):
        self.ctx = ctx

    async def complete(self, messages, *, max_tokens):
        try:
            result = await self.ctx.llm.acomplete(messages=messages, max_tokens=max_tokens,
                temperature=0.1, timeout=180, purpose="margen.summary")
        except TimeoutError:
            raise
        except Exception as exc:
            raise SummaryFailure('summary_provider') from exc
        if result.provider != 'openrouter' or result.model != SUMMARY_MODEL:
            raise SummaryFailure('summary_model_mismatch')
        if not result.text.strip():
            raise SummaryFailure('summary_empty')
        return result.text
