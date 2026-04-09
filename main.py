import asyncio
from app.run import run_polling


async def main() -> None:
    await run_polling()


if __name__ == "__main__":
    asyncio.run(main())
