import asyncio
import sys

async def test_ffprobe():
    video_path = r'storage\uploads\俄罗斯的军力真的是世界第二吗？俄罗斯算是青春版苏联吗？ 为什么发展了30年，俄罗斯依旧没有强大起来？#欧洲 #俄罗斯 #经济发展 #综合国力 #知识分享.mp4'

    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]

    print(f"Running command: {' '.join(cmd)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        print(f"Return code: {process.returncode}")
        print(f"Stdout: {stdout.decode('utf-8', errors='ignore')}")
        print(f"Stderr: {stderr.decode('utf-8', errors='ignore')}")

        if process.returncode == 0:
            duration_str = stdout.decode('utf-8').strip()
            print(f"Duration: {duration_str}")
        else:
            print("Command failed!")

    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ffprobe())
