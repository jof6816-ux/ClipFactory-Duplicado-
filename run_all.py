import time, finder, editor, publisher, uploader
while True:
    for agent in (finder, editor, publisher, uploader):
        try: agent.run()
        except Exception as e: print(agent.__name__, "error:", e)
    time.sleep(900)  # cada 15 min
