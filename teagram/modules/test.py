from .. import loader

@loader.module("wtf", warning="oh no, don't load it")
class WTFMod(loader.Module):
    
    @loader.command()
    async def testwtf(self, message):
        await message.edit("oh no it's session stealer")