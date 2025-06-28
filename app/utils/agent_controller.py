import os
import socket
import json
# Socket configuration for agent communication
def get_socket_path() -> str:
    """Get appropriate socket path for agent communication."""
    # Production: systemd managed socket
    prod_socket = "/run/devopin-agent.sock"
    if os.path.exists(prod_socket):
        return prod_socket
    
    # Development/fallback: use /tmp
    return "/tmp/devopin-agent.sock"

SOCKET_PATH = get_socket_path()
class AgentController:
    """Handler untuk komunikasi dengan devopin-agent via Unix socket"""
    
    @staticmethod
    def send_command(command: str, service_name: str|None = None) -> dict:
        """Send command to agent via Unix socket"""
        try:
            if not os.path.exists(SOCKET_PATH):
                return {"success": False, "message": "Agent socket not found. Is devopin-agent running?"}
            
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 second timeout
            
            sock.connect(SOCKET_PATH)
            
            # Prepare command
            cmd_data = {
                "command": command,
                "service": service_name
            }
            
            # Send command
            message = json.dumps(cmd_data) + "\n"
            sock.send(message.encode())
            
            # Receive response
            response = sock.recv(1024).decode()
            sock.close()
            
            return json.loads(response)
            
        except socket.timeout:
            return {"success": False, "message": "Command timeout. Agent may be busy."}
        except ConnectionRefusedError:
            return {"success": False, "message": "Cannot connect to agent. Is devopin-agent service running?"}
        except Exception as e:
            return {"success": False, "message": f"Error communicating with agent: {str(e)}"}
    @staticmethod
    def get_current_socket_path() -> str:
        """Get current socket path being used"""
        return get_socket_path()
    
    @staticmethod
    def test_connection() -> dict:
        """Test connection to agent"""
        return AgentController.send_command("status")
