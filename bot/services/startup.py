from bot.utils.consts import positions_map
from bot.utils.unitofwork import UnitOfWork


async def on_startup():
    uow = UnitOfWork()
    async with uow:
        for position, level in positions_map.items():
            position_exists = await uow.positions.find_one(title=position)
            if not position_exists:
                await uow.positions.add_one(
                    data=dict(title=position, hierarchy_level=level)
                )
        await uow.commit()
