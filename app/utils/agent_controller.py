import os
import socket
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_socket_path() -> str:
    """Get appropriate socket path for agent communication."""
    # Read from environment variables first
    primary_socket = os.getenv('AGENT_SOCKET_PATH', '/run/devopin-agent.sock')
    fallback_socket = os.getenv('FALLBACK_SOCKET_PATH', '/tmp/devopin-agent.sock')
    
    # Check if primary socket exists and is accessible
    if os.path.exists(primary_socket):
        return primary_socket
    
    # Fallback to secondary socket
    return fallback_socket

def get_socket_timeout() -> int:
    """Get socket timeout from environment variables."""
    return int(os.getenv('AGENT_TIMEOUT', '10'))

SOCKET_PATH = get_socket_path()
SOCKET_TIMEOUT = get_socket_timeout()
class AgentController:
    """Handler untuk komunikasi dengan devopin-agent via Unix socket"""
    
    @staticmethod
    def send_command(command: str, service_name: str|None = None) -> dict:
        """Send command to agent via Unix socket"""
        try:
            # Debug logging
            import logging
            logging.basicConfig(level=logging.DEBUG)
            logger = logging.getLogger(__name__)
            
            logger.info(f"Attempting to send command: {command} to service: {service_name}")
            logger.info(f"Socket path: {SOCKET_PATH}")
            logger.info(f"Socket exists: {os.path.exists(SOCKET_PATH)}")
            
            if not os.path.exists(SOCKET_PATH):
                return {"success": False, "message": f"Agent socket not found at {SOCKET_PATH}. Is devopin-agent running?"}
            
            # Check socket permissions
            try:
                stat_info = os.stat(SOCKET_PATH)
                logger.info(f"Socket permissions: {oct(stat_info.st_mode)}")
                logger.info(f"Socket owner: {stat_info.st_uid}")
                logger.info(f"Current user: {os.getuid()}")
            except Exception as perm_e:
                logger.info(f"Cannot check socket permissions: {perm_e}")
            
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(SOCKET_TIMEOUT)  # Use timeout from environment
            
            logger.info("Connecting to socket...")
            sock.connect(SOCKET_PATH)
            
            # Prepare command
            cmd_data = {
                "command": command,
                "service": service_name
            }
            
            # Send command
            message = json.dumps(cmd_data) + "\n"
            logger.info(f"Sending message: {message.strip()}")
            sock.send(message.encode())
            
            # Receive response
            response = sock.recv(1024).decode()
            logger.info(f"Received response: {response}")
            sock.close()
            
            return json.loads(response)
            
        except socket.timeout:
            return {"success": False, "message": "Command timeout. Agent may be busy."}
        except ConnectionRefusedError:
            return {"success": False, "message": "Cannot connect to agent. Is devopin-agent service running?"}
        except PermissionError as pe:
            return {"success": False, "message": f"Permission denied accessing socket: {str(pe)}"}
        except Exception as e:
            return {"success": False, "message": f"Error communicating with agent: {str(e)}"}
    @staticmethod
    def get_current_socket_path() -> str:
        """Get current socket path being used"""
        return SOCKET_PATH
    
    @staticmethod
    def get_config_info() -> dict:
        """Get agent configuration information"""
        return {
            "socket_path": SOCKET_PATH,
            "timeout": SOCKET_TIMEOUT,
            "primary_socket": os.getenv('AGENT_SOCKET_PATH', '/run/devopin-agent.sock'),
            "fallback_socket": os.getenv('FALLBACK_SOCKET_PATH', '/tmp/devopin-agent.sock'),
            "socket_exists": os.path.exists(SOCKET_PATH)
        }
    
    @staticmethod
    def test_connection() -> dict:
        """Test connection to agent"""
        return AgentController.send_command("status")
    
    @staticmethod
    def send_stream_command(command: str, service_name: str = None, stream_id: str = None) -> dict:
        """Send streaming command to agent via Unix socket (for logs_stream and logs_stop)"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"Attempting to send stream command: {command}")
            
            if not os.path.exists(SOCKET_PATH):
                return {"success": False, "message": f"Agent socket not found at {SOCKET_PATH}. Is devopin-agent running?"}
            
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(SOCKET_TIMEOUT)
            
            logger.info("Connecting to socket for streaming...")
            sock.connect(SOCKET_PATH)
            
            # Prepare command
            cmd_data = {
                "command": command,
                "service": service_name,
                "stream_id": stream_id
            }
            
            # Send command
            message = json.dumps(cmd_data) + "\n"
            logger.info(f"Sending stream message: {message.strip()}")
            sock.send(message.encode())
            
            # For logs_stream, return socket for streaming
            if command == "logs_stream":
                return {"success": True, "socket": sock, "streaming": True}
            
            # For logs_stop, get response and close
            response = sock.recv(1024).decode()
            logger.info(f"Received response: {response}")
            sock.close()
            
            return json.loads(response)
            
        except socket.timeout:
            return {"success": False, "message": "Command timeout. Agent may be busy."}
        except ConnectionRefusedError:
            return {"success": False, "message": "Cannot connect to agent. Is devopin-agent service running?"}
        except PermissionError as pe:
            return {"success": False, "message": f"Permission denied accessing socket: {str(pe)}"}
        except Exception as e:
            return {"success": False, "message": f"Error communicating with agent: {str(e)}"}
    
    @staticmethod
    def start_log_stream(service_name: str) -> dict:
        """Start log streaming for a service"""
        return AgentController.send_stream_command("logs_stream", service_name=service_name)
    
    @staticmethod
    def stop_log_stream(stream_id: str = None) -> dict:
        """Stop log streaming"""
        return AgentController.send_stream_command("logs_stop", stream_id=stream_id)
