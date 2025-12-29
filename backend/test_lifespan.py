import asyncio
import sys
sys.path.insert(0, '.')

from app.main import app

async def test():
    print("Testing lifespan...")
    async with app.router.lifespan_context(app):
        print("Lifespan started successfully!")
        await asyncio.sleep(2)
    print("Lifespan ended")

if __name__ == "__main__":
    asyncio.run(test())
