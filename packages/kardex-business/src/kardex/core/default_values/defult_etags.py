from kardex.tools import EtagTool


async def set_default_etags():
    await EtagTool().update_branches_etags()
