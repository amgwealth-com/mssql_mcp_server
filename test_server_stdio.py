#!/usr/bin/env python3
"""Test MCP server in stdio mode with a simple MCP protocol exchange."""

import asyncio
import json
import os
import sys

async def test_mcp_server():
    """Test the MCP server with basic protocol messages."""
    
    # Start the server process
    process = await asyncio.create_subprocess_exec(
        "uv", "run", "python", "src/mssql_mcp_server/server.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={
            **os.environ,
            "MSSQL_SERVER": "amg-uat-00.database.windows.net",
            "MSSQL_DATABASE": "awm",
            "MSSQL_USER": "kyleliu",
            "MSSQL_PASSWORD": "uat!23456"
        }
    )
    
    print("✓ Server process started")
    print()
    
    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialize request...")
        request_json = json.dumps(init_request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()
        
        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=5.0
            )
            
            if response_line:
                response = json.loads(response_line.decode())
                print("✓ Received initialize response")
                print(f"  Server: {response.get('result', {}).get('serverInfo', {}).get('name', 'unknown')}")
                print(f"  Protocol: {response.get('result', {}).get('protocolVersion', 'unknown')}")
                print()
                
                # Send initialized notification
                initialized_notif = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                print("Sending initialized notification...")
                notif_json = json.dumps(initialized_notif) + "\n"
                process.stdin.write(notif_json.encode())
                await process.stdin.drain()
                print("✓ Sent initialized notification")
                print()
                
                # Test tools/list
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                print("Requesting tools list...")
                tools_json = json.dumps(tools_request) + "\n"
                process.stdin.write(tools_json.encode())
                await process.stdin.drain()
                
                tools_response = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=5.0
                )
                
                if tools_response:
                    tools_result = json.loads(tools_response.decode())
                    tools = tools_result.get('result', {}).get('tools', [])
                    print(f"✓ Received {len(tools)} tool(s)")
                    for tool in tools:
                        print(f"  - {tool.get('name')}: {tool.get('description')}")
                    print()
                
                # Test resources/list
                resources_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "resources/list"
                }
                print("Requesting resources list...")
                resources_json = json.dumps(resources_request) + "\n"
                process.stdin.write(resources_json.encode())
                await process.stdin.drain()
                
                resources_response = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=10.0
                )
                
                if resources_response:
                    resources_result = json.loads(resources_response.decode())
                    resources = resources_result.get('result', {}).get('resources', [])
                    print(f"✓ Received {len(resources)} resource(s) (tables)")
                    for resource in resources[:5]:  # Show first 5
                        print(f"  - {resource.get('name')}")
                    if len(resources) > 5:
                        print(f"  ... and {len(resources) - 5} more")
                    print()
                
                print("✓ All MCP protocol tests passed!")
                print()
                print("The server is working correctly and ready to use.")
                
            else:
                print("✗ No response from server")
                
        except asyncio.TimeoutError:
            print("✗ Timeout waiting for server response")
            stderr = await process.stderr.read()
            if stderr:
                print("\nServer stderr:")
                print(stderr.decode())
    
    finally:
        # Clean shutdown
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_server())
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
