from bot.utils.consts import positions_map
from bot.utils.unitofwork import UnitOfWork


async def on_startup():
    uow = UnitOfWork()
    async with uow:
        for level in range(1, 5):
            level_exists = await uow.hierarchy_level_repo.find_one(level=level)
            if not level_exists:
                await uow.hierarchy_level_repo.add_one(
                    data=dict(
                        level=level,
                        prompt="test prompt",
                        analytics_prompt="test analytics prompt",
                    )
                )
                await uow.commit()
        for position, level in positions_map.items():
            position_exists = await uow.positions.find_one(title=position)
            if not position_exists:
                position_model = await uow.hierarchy_level_repo.find_one(level=level)
                await uow.positions.add_one(
                    data=dict(
                        title=position,
                        hierarchy_level_id=position_model.id,
                    )
                )
        await uow.commit()
