from .domain import SUMMARY_MODEL


class HermesModel:
    def __init__(self, ctx):
        self.ctx = ctx

    async def complete(self, messages, *, max_tokens):
        result = await self.ctx.llm.acomplete(messages=messages, max_tokens=max_tokens,
            temperature=0.1, timeout=180, purpose="margen.summary")
        if result.provider != 'openrouter' or result.model != SUMMARY_MODEL:
            raise RuntimeError("El perfil debe usar OpenRouter con el modelo de resumen aprobado.")
        if not result.text.strip():
            raise RuntimeError("El proveedor no devolvió texto.")
        return result.text
