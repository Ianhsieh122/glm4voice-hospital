import asyncio
import websockets
import json
import time

async def test_stutter(run_index):
    uri = "ws://localhost:8000/ws/conversation"
    intervals = []
    print(f"--- Run {run_index} ---")
    
    # Retry loop for connection
    max_retries = 10
    retry_delay = 5
    websocket = None
    
    for attempt in range(max_retries):
        try:
            websocket = await websockets.connect(uri)
            break
        except Exception as e:
            print(f"Connection attempt {attempt+1}/{max_retries} failed. Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            
    if not websocket:
        print("Could not connect to the server.")
        return intervals

    try:
        try:
            msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            if isinstance(msg, str):
                print(f"Initial msg: {msg[:100]}")
            except Exception as e:
                print("No initial message.")

            payload = {"type": "transcript", "text": "你好，請問有看診嗎？"}
            await websocket.send(json.dumps(payload))
            print("Sent payload. Waiting for audio chunks...")
            
            last_time = None
            
            while True:
                try:
                    # 15s timeout for first audio, then 3s for subsequent chunks
                    timeout = 15.0 if last_time is None else 3.0
                    message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    current_time = time.time()
                    
                    if isinstance(message, bytes):
                        # Calculate interval only between consecutive audio chunks
                        if last_time is not None:
                            interval = (current_time - last_time) * 1000
                            intervals.append(interval)
                        last_time = current_time
                    else:
                        print(f"Received text msg: {message[:100]}")
                        
                except asyncio.TimeoutError:
                    print("Timeout reached, assuming audio stream finished.")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed.")
                    break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()
        
    return intervals

async def main():
    all_intervals = []
    for i in range(1, 4):
        intervals = await test_stutter(i)
        all_intervals.append(intervals)
        await asyncio.sleep(2) # small pause between runs
        
    print("\n--- Summary ---")
    stutter_found = False
    for i, intervals in enumerate(all_intervals, 1):
        if not intervals:
            print(f"Run {i}: No interval data.")
            continue
        avg = sum(intervals) / len(intervals)
        max_interval = max(intervals)
        stutters = sum(1 for x in intervals if x > 50)
        if stutters > 0:
            stutter_found = True
        print(f"Run {i}: Total chunks = {len(intervals)+1}, Avg Interval = {avg:.2f} ms, Max Interval = {max_interval:.2f} ms, Stutters (>50ms) = {stutters}")

    if stutter_found:
        print("\nConclusion: Stuttering detected (intervals > 50ms).")
    else:
        print("\nConclusion: No stuttering detected. Intervals are consistent.")

if __name__ == "__main__":
    asyncio.run(main())
