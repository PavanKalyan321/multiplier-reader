# WebSocket test server - simulates API trading signals for testing
import asyncio
import websockets
import json
from datetime import datetime
from typing import List, Dict, Any
import argparse


class WebSocketTestServer:
    """Test WebSocket server that sends trading signals"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize test server

        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.clients = set()
        self.signal_queue = asyncio.Queue()
        self.running = False

    def _log(self, message: str):
        """Log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] TEST_SERVER: {message}")

    async def register_client(self, websocket):
        """Register a new client"""
        self.clients.add(websocket)
        self._log(f"Client connected. Total clients: {len(self.clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)
            self._log(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast_signal(self, signal: Dict[str, Any]):
        """Broadcast signal to all connected clients"""
        if not self.clients:
            self._log("No clients connected, signal not sent")
            return

        message = json.dumps(signal)
        self._log(f"Broadcasting signal: {signal}")

        dead_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                dead_clients.add(client)

        # Remove dead clients
        for client in dead_clients:
            self.clients.discard(client)

    async def send_test_signals(
        self,
        num_signals: int = 5,
        interval: float = 10.0,
        base_multiplier: float = 1.5
    ):
        """Send test signals at intervals

        Args:
            num_signals: Number of signals to send
            interval: Interval between signals in seconds
            base_multiplier: Base expected multiplier
        """
        self._log(f"Starting to send {num_signals} test signals (interval: {interval}s)")

        for i in range(num_signals):
            signal = {
                'timestamp': datetime.now().isoformat(),
                'expectedRange': f'1.0-{base_multiplier + 1.0:.1f}',
                'expectedMultiplier': str(base_multiplier + (i * 0.1)),  # Increment multiplier
                'bet': True,
                'roundId': f'signal_{i+1}_{int(datetime.now().timestamp())}'
            }

            await self.broadcast_signal(signal)
            self._log(f"Sent signal {i+1}/{num_signals}")

            if i < num_signals - 1:
                await asyncio.sleep(interval)

        self._log("All test signals sent")

    async def start_server(self):
        """Start the WebSocket server"""
        self.running = True

        async def handle_client(websocket, path):
            await self.register_client(websocket)

        try:
            async with websockets.serve(handle_client, self.host, self.port):
                self._log(f"WebSocket server started on ws://{self.host}:{self.port}")
                await asyncio.Event().wait()  # Run forever
        except Exception as e:
            self._log(f"Server error: {e}")
        finally:
            self.running = False

    async def interactive_mode(self):
        """Run server in interactive mode"""
        self._log("Starting in interactive mode...")
        self._log("Commands:")
        self._log("  send <num> - Send N test signals")
        self._log("  clients - Show connected clients")
        self._log("  quit - Exit")

        loop = asyncio.get_event_loop()

        while self.running:
            try:
                # Read user input without blocking
                command = await loop.run_in_executor(None, input, "\n> ")

                if command.startswith("send"):
                    try:
                        num = int(command.split()[1]) if len(command.split()) > 1 else 1
                        await self.send_test_signals(num)
                    except (ValueError, IndexError):
                        self._log("Usage: send <number>")

                elif command == "clients":
                    self._log(f"Connected clients: {len(self.clients)}")

                elif command == "quit":
                    self._log("Shutting down...")
                    self.running = False
                    break

                else:
                    self._log(f"Unknown command: {command}")

            except Exception as e:
                self._log(f"Error: {e}")


async def run_server_with_test_signals(
    num_signals: int = 5,
    interval: float = 10.0,
    host: str = "localhost",
    port: int = 8765
):
    """Run server and send test signals

    Args:
        num_signals: Number of signals to send
        interval: Interval between signals
        host: Server host
        port: Server port
    """
    server = WebSocketTestServer(host, port)

    # Create server task
    server_task = asyncio.create_task(server.start_server())

    # Give server time to start
    await asyncio.sleep(1)

    try:
        # Send test signals
        await server.send_test_signals(num_signals, interval)

        # Wait a bit before shutdown
        await asyncio.sleep(5)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


async def run_server_interactive(host: str = "localhost", port: int = 8765):
    """Run server in interactive mode

    Args:
        host: Server host
        port: Server port
    """
    server = WebSocketTestServer(host, port)

    # Create server task
    server_task = asyncio.create_task(server.start_server())

    # Give server time to start
    await asyncio.sleep(1)

    try:
        # Run interactive mode
        await server.interactive_mode()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='WebSocket Test Server for Trading Signals')
    parser.add_argument('--mode', choices=['test', 'interactive'], default='interactive',
                      help='Server mode (default: interactive)')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8765, help='Server port (default: 8765)')
    parser.add_argument('--signals', type=int, default=5, help='Number of test signals (default: 5)')
    parser.add_argument('--interval', type=float, default=10.0, help='Signal interval in seconds (default: 10)')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("WebSocket Test Server for Trading Signals".center(60))
    print(f"{'='*60}\n")

    try:
        if args.mode == 'test':
            print(f"Starting in TEST mode: sending {args.signals} signals every {args.interval}s\n")
            asyncio.run(run_server_with_test_signals(
                num_signals=args.signals,
                interval=args.interval,
                host=args.host,
                port=args.port
            ))
        else:
            print(f"Starting in INTERACTIVE mode on ws://{args.host}:{args.port}\n")
            asyncio.run(run_server_interactive(args.host, args.port))

    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Error: {e}")

    print("\nServer stopped")


if __name__ == "__main__":
    main()
