import os
import json
import requests
import logging
from anthropic import Anthropic
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File cache to avoid re-reading unchanged files
_file_cache = {}

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY", "")
NAMECHEAP_API_USER = os.environ.get("NAMECHEAP_API_USER", "")
NAMECHEAP_API_KEY = os.environ.get("NAMECHEAP_API_KEY", "")
NAMECHEAP_USERNAME = os.environ.get("NAMECHEAP_USERNAME", "")
NAMECHEAP_CLIENT_IP = os.environ.get("NAMECHEAP_CLIENT_IP", "")

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

RENDER_API_BASE = "https://api.render.com/v1"
NAMECHEAP_API_BASE = "https://api.namecheap.com/xml.response"

def get_client_ip():
    """Get the server's public IP address or use configured IP"""
    if NAMECHEAP_CLIENT_IP:
        return NAMECHEAP_CLIENT_IP
    
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json().get('ip', '0.0.0.0')
    except:
        logger.warning("Failed to get public IP, using configured or default")
        return '0.0.0.0'

def list_render_services():
    """List all Render services"""
    try:
        if not RENDER_API_KEY:
            logger.error("Render API key not configured")
            return {"error": "RENDER_API_KEY not configured. Please set this environment variable."}
        
        headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json"
        }
        logger.info("Fetching Render services list")
        response = requests.get(f"{RENDER_API_BASE}/services", headers=headers, timeout=10)
        response.raise_for_status()
        
        services = response.json()
        result = []
        for service in services:
            result.append({
                "id": service.get("id"),
                "name": service.get("name"),
                "type": service.get("type"),
                "suspended": service.get("suspended"),
                "createdAt": service.get("createdAt"),
                "updatedAt": service.get("updatedAt")
            })
        logger.info(f"Successfully retrieved {len(result)} Render services")
        return {
            "services": result,
            "count": len(result),
            "message": f"Found {len(result)} Render services in your account."
        }
    except requests.Timeout:
        logger.exception("Timeout listing Render services")
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Failed to list Render services: {str(e)}", exc_info=True)
        return {"error": f"Failed to list Render services: {str(e)}"}

def get_render_service(service_id):
    """Get details of a specific Render service"""
    try:
        if not RENDER_API_KEY:
            logger.error("Render API key not configured")
            return {"error": "RENDER_API_KEY not configured. Please set this environment variable."}
        
        headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json"
        }
        logger.info(f"Fetching details for Render service: {service_id}")
        response = requests.get(f"{RENDER_API_BASE}/services/{service_id}", headers=headers, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Successfully retrieved details for service {service_id}")
        return {"service": response.json()}
    except requests.Timeout:
        logger.exception(f"Timeout getting Render service: {service_id}")
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Failed to get Render service {service_id}: {str(e)}", exc_info=True)
        return {"error": f"Failed to get Render service: {str(e)}"}

def restart_render_service(service_id):
    """Restart a Render service"""
    try:
        if not RENDER_API_KEY:
            logger.error("Render API key not configured")
            return {"error": "RENDER_API_KEY not configured. Please set this environment variable."}
        
        headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json"
        }
        logger.info(f"Restarting Render service: {service_id}")
        response = requests.post(
            f"{RENDER_API_BASE}/services/{service_id}/restart",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        logger.info(f"Successfully restarted service {service_id}")
        return {"success": True, "message": f"Service {service_id} restarted successfully"}
    except requests.Timeout:
        logger.exception(f"Timeout restarting Render service: {service_id}")
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Failed to restart Render service {service_id}: {str(e)}", exc_info=True)
        return {"error": f"Failed to restart Render service: {str(e)}"}

def suspend_render_service(service_id):
    """Suspend a Render service"""
    try:
        if not RENDER_API_KEY:
            logger.error("Render API key not configured")
            return {"error": "RENDER_API_KEY not configured. Please set this environment variable."}
        
        headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        logger.info(f"Suspending Render service: {service_id}")
        response = requests.post(
            f"{RENDER_API_BASE}/services/{service_id}/suspend",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        logger.info(f"Successfully suspended service {service_id}")
        return {"success": True, "message": f"Service {service_id} suspended successfully"}
    except requests.Timeout:
        logger.exception(f"Timeout suspending Render service: {service_id}")
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Failed to suspend Render service {service_id}: {str(e)}", exc_info=True)
        return {"error": f"Failed to suspend Render service: {str(e)}"}

def resume_render_service(service_id):
    """Resume a suspended Render service"""
    try:
        if not RENDER_API_KEY:
            logger.error("Render API key not configured")
            return {"error": "RENDER_API_KEY not configured. Please set this environment variable."}
        
        headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json"
        }
        logger.info(f"Resuming Render service: {service_id}")
        response = requests.post(
            f"{RENDER_API_BASE}/services/{service_id}/resume",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        logger.info(f"Successfully resumed service {service_id}")
        return {"success": True, "message": f"Service {service_id} resumed successfully"}
    except requests.Timeout:
        logger.exception(f"Timeout resuming Render service: {service_id}")
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Failed to resume Render service {service_id}: {str(e)}", exc_info=True)
        return {"error": f"Failed to resume Render service: {str(e)}"}

def check_namecheap_domain(domain_name):
    """Check if a domain is available on Namecheap"""
    try:
        if not NAMECHEAP_API_KEY or not NAMECHEAP_API_USER:
            logger.error("Namecheap API credentials not configured")
            return {"error": "NAMECHEAP_API_KEY or NAMECHEAP_API_USER not configured. Please set these environment variables."}
        
        client_ip = get_client_ip()
        if client_ip == '0.0.0.0':
            return {"error": "Unable to determine client IP. Please set NAMECHEAP_CLIENT_IP environment variable with your whitelisted IP."}
        
        params = {
            "ApiUser": NAMECHEAP_API_USER,
            "ApiKey": NAMECHEAP_API_KEY,
            "UserName": NAMECHEAP_USERNAME or NAMECHEAP_API_USER,
            "Command": "namecheap.domains.check",
            "ClientIp": client_ip,
            "DomainList": domain_name
        }
        
        logger.info(f"Checking domain availability for: {domain_name}")
        response = requests.get(NAMECHEAP_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        
        is_available = "Available=\"true\"" in response.text
        logger.info(f"Domain {domain_name} availability: {is_available}")
        
        return {
            "available": is_available,
            "domain": domain_name,
            "message": f"Domain {domain_name} is {'available' if is_available else 'not available'} for registration."
        }
    except requests.Timeout:
        logger.exception(f"Timeout checking domain: {domain_name}")
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Failed to check domain {domain_name}: {str(e)}", exc_info=True)
        return {"error": f"Failed to check domain: {str(e)}"}

def list_namecheap_domains():
    """List all domains in Namecheap account"""
    try:
        if not NAMECHEAP_API_KEY or not NAMECHEAP_API_USER:
            logger.error("Namecheap API credentials not configured")
            return {"error": "NAMECHEAP_API_KEY or NAMECHEAP_API_USER not configured. Please set these environment variables."}
        
        client_ip = get_client_ip()
        if client_ip == '0.0.0.0':
            return {"error": "Unable to determine client IP. Please set NAMECHEAP_CLIENT_IP environment variable with your whitelisted IP."}
        
        params = {
            "ApiUser": NAMECHEAP_API_USER,
            "ApiKey": NAMECHEAP_API_KEY,
            "UserName": NAMECHEAP_USERNAME or NAMECHEAP_API_USER,
            "Command": "namecheap.domains.getList",
            "ClientIp": client_ip,
            "PageSize": "100"
        }
        
        logger.info("Listing Namecheap domains")
        response = requests.get(NAMECHEAP_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        
        logger.info("Successfully retrieved Namecheap domains")
        return {
            "domains_xml": response.text,
            "success": True,
            "message": "Retrieved domain list. Please review the XML response for detailed information."
        }
    except requests.Timeout:
        logger.exception("Timeout listing domains")
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Failed to list domains: {str(e)}", exc_info=True)
        return {"error": f"Failed to list domains: {str(e)}"}

def get_namecheap_domain_info(domain_name):
    """Get detailed information about a domain"""
    try:
        if not NAMECHEAP_API_KEY or not NAMECHEAP_API_USER:
            logger.error("Namecheap API credentials not configured")
            return {"error": "NAMECHEAP_API_KEY or NAMECHEAP_API_USER not configured. Please set these environment variables."}
        
        client_ip = get_client_ip()
        if client_ip == '0.0.0.0':
            return {"error": "Unable to determine client IP. Please set NAMECHEAP_CLIENT_IP environment variable with your whitelisted IP."}
        
        params = {
            "ApiUser": NAMECHEAP_API_USER,
            "ApiKey": NAMECHEAP_API_KEY,
            "UserName": NAMECHEAP_USERNAME or NAMECHEAP_API_USER,
            "Command": "namecheap.domains.getInfo",
            "ClientIp": client_ip,
            "DomainName": domain_name
        }
        
        logger.info(f"Getting domain info for: {domain_name}")
        response = requests.get(NAMECHEAP_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Successfully retrieved info for {domain_name}")
        return {
            "domain_info_xml": response.text,
            "success": True,
            "message": f"Retrieved information for {domain_name}. Please review the XML response for detailed information."
        }
    except requests.Timeout:
        logger.exception(f"Timeout getting domain info: {domain_name}")
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Failed to get domain info for {domain_name}: {str(e)}", exc_info=True)
        return {"error": f"Failed to get domain info: {str(e)}"}

def read_env_variables(keys=None):
    """
    Read environment variables. If keys is provided (list of strings), return only those keys.
    If keys is None, return all environment variables (sensitive ones are hidden).
    """
    try:
        logger.info(f"Reading environment variables: {keys}")
        
        # Get all environment variables
        all_env = dict(os.environ)
        
        # If specific keys requested
        if keys:
            result = {}
            for key in keys:
                result[key] = all_env.get(key, "NOT_SET")
            logger.info(f"Successfully read {len(result)} environment variables")
            return {
                "variables": result,
                "success": True
            }
        
        # Return all non-sensitive variables
        sensitive_patterns = ['PASSWORD', 'SECRET', 'TOKEN', 'PRIVATE', 'CREDENTIAL', 'KEY']
        safe_env = {}
        sensitive_env = []
        
        for key, value in all_env.items():
            is_sensitive = any(pattern in key.upper() for pattern in sensitive_patterns)
            if is_sensitive:
                sensitive_env.append(key)
                safe_env[key] = "***HIDDEN***"
            else:
                safe_env[key] = value
        
        logger.info(f"Successfully read all environment variables ({len(sensitive_env)} hidden)")
        return {
            "variables": safe_env,
            "sensitive_keys_hidden": sensitive_env,
            "success": True,
            "note": "Sensitive keys are hidden. Request specific keys by name to see their values."
        }
        
    except Exception as e:
        logger.error(f"Error reading environment variables: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}

FUNCTION_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_render_services",
            "description": "List all Render services in the account",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_render_service",
            "description": "Get detailed information about a specific Render service",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The ID of the Render service"
                    }
                },
                "required": ["service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_render_service",
            "description": "Restart a Render service",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The ID of the Render service to restart"
                    }
                },
                "required": ["service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suspend_render_service",
            "description": "Suspend a Render service to stop it from running",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The ID of the Render service to suspend"
                    }
                },
                "required": ["service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resume_render_service",
            "description": "Resume a suspended Render service",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The ID of the Render service to resume"
                    }
                },
                "required": ["service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_namecheap_domain",
            "description": "Check if a domain name is available for registration on Namecheap",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain_name": {
                        "type": "string",
                        "description": "The domain name to check (e.g., example.com)"
                    }
                },
                "required": ["domain_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_namecheap_domains",
            "description": "List all domains registered in the Namecheap account",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_namecheap_domain_info",
            "description": "Get detailed information about a specific domain in Namecheap",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain_name": {
                        "type": "string",
                        "description": "The domain name to get info for (e.g., example.com)"
                    }
                },
                "required": ["domain_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_dashboard_file",
            "description": "Read the contents of a dashboard file (HTML, CSS, JS). Use this to see the current content before making edits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file to read. Options: static/dashboard.html, static/admin-dashboard.html, static/sales.html, static/claim-domain.html, static/packages.html, static/register-complete.html, static/backoffice.html, static/css/style.css, static/admin-panel.html"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_dashboard_file",
            "description": "Edit a dashboard file by replacing specific content. Always read the file first to get the exact content to replace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file to edit. Options: static/dashboard.html, static/admin-dashboard.html, static/sales.html, static/claim-domain.html, static/packages.html, static/register-complete.html, static/backoffice.html, static/css/style.css, static/admin-panel.html"
                    },
                    "old_content": {
                        "type": "string",
                        "description": "The exact content to replace (must match exactly, including whitespace)"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "The new content to insert"
                    }
                },
                "required": ["filename", "old_content", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_html_page",
            "description": "Create a new HTML page in the static folder. Use this to build new pages for the backoffice or dashboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename with path (must start with 'static/' and end with '.html'). Example: static/analytics.html"
                    },
                    "content": {
                        "type": "string",
                        "description": "The complete HTML content for the page"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_python_file",
            "description": "Read a Python backend file (app.py or models.py) in chunks. For faster responses, read specific sections instead of entire files. Default reads first 200 lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file to read. Options: app.py, models.py"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Line number to start reading from (1-indexed). Default: 1"
                    },
                    "num_lines": {
                        "type": "integer",
                        "description": "Number of lines to read. Default: 200. Use -1 to read entire file (slower)."
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_python_file",
            "description": "Edit a Python backend file (app.py or models.py) to add routes, modify logic, or update models. Always read the file first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file to edit. Options: app.py, models.py"
                    },
                    "old_content": {
                        "type": "string",
                        "description": "The exact content to replace (must match exactly, including whitespace and indentation)"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "The new content to insert"
                    }
                },
                "required": ["filename", "old_content", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_env_variables",
            "description": "Read environment variables. Request specific keys or get all (sensitive ones hidden). Perfect for checking API keys, configuration, and secrets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific environment variable names to read (e.g., ['OPENAI_API_KEY', 'RENDER_API_KEY']). If not provided, returns all variables with sensitive ones hidden."
                    }
                },
                "required": []
            }
        }
    }
]

def read_dashboard_file(filename):
    """Read a dashboard file (HTML, CSS, JS)"""
    allowed_files = [
        'static/dashboard.html',
        'static/admin-dashboard.html',
        'static/sales.html',
        'static/claim-domain.html',
        'static/packages.html',
        'static/register-complete.html',
        'static/backoffice.html',
        'static/css/style.css',
        'static/admin-panel.html'
    ]
    
    if filename not in allowed_files:
        return {"error": f"Access denied. Only dashboard files can be read. Allowed files: {', '.join(allowed_files)}"}
    
    try:
        logger.info(f"Reading file: {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully read file: {filename}")
        return {
            "filename": filename,
            "content": content,
            "success": True
        }
    except FileNotFoundError:
        logger.error(f"File not found: {filename}", exc_info=True)
        return {"error": f"File not found: {filename}"}
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {str(e)}", exc_info=True)
        return {"error": f"Failed to read file: {str(e)}"}

def edit_dashboard_file(filename, old_content, new_content):
    """Edit a dashboard file by replacing old_content with new_content"""
    allowed_files = [
        'static/dashboard.html',
        'static/admin-dashboard.html',
        'static/sales.html',
        'static/claim-domain.html',
        'static/packages.html',
        'static/register-complete.html',
        'static/backoffice.html',
        'static/css/style.css',
        'static/admin-panel.html'
    ]
    
    if filename not in allowed_files:
        return {"error": f"Access denied. Only dashboard files can be edited. Allowed files: {', '.join(allowed_files)}"}
    
    try:
        logger.info(f"Editing file: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        if old_content not in current_content:
            return {"error": "Old content not found in file. Please read the file first to get the exact content."}
        
        updated_content = current_content.replace(old_content, new_content, 1)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"Successfully edited file: {filename}")
        return {
            "filename": filename,
            "success": True,
            "message": f"Successfully updated {filename}"
        }
    except FileNotFoundError:
        logger.error(f"File not found: {filename}", exc_info=True)
        return {"error": f"File not found: {filename}"}
    except Exception as e:
        logger.error(f"Failed to edit file {filename}: {str(e)}", exc_info=True)
        return {"error": f"Failed to edit file: {str(e)}"}

def create_html_page(filename, content):
    """Create a new HTML page in the static folder"""
    if not filename.startswith('static/') or not filename.endswith('.html'):
        return {"error": "HTML pages must be in static/ folder and end with .html"}
    
    try:
        logger.info(f"Creating new HTML page: {filename}")
        
        if os.path.exists(filename):
            return {"error": f"File {filename} already exists. Use edit_dashboard_file to modify it."}
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully created HTML page: {filename}")
        return {
            "filename": filename,
            "success": True,
            "message": f"Successfully created {filename}"
        }
    except Exception as e:
        logger.error(f"Failed to create HTML page {filename}: {str(e)}", exc_info=True)
        return {"error": f"Failed to create HTML page: {str(e)}"}

def read_python_file(filename, start_line=1, num_lines=200):
    """Read a Python file (app.py or models.py) in chunks with caching
    
    Args:
        filename: The file to read (app.py or models.py)
        start_line: Line number to start reading from (1-indexed, default: 1)
        num_lines: Number of lines to read (default: 200, use -1 for entire file)
    """
    allowed_files = ['app.py', 'models.py']
    
    if filename not in allowed_files:
        return {"error": f"Access denied. Only these files can be read: {', '.join(allowed_files)}"}
    
    try:
        # Get file info
        current_mtime = os.path.getmtime(filename)
        
        # For full file reads, use cache
        if num_lines == -1:
            cache_key = f"{filename}_full"
            
            if cache_key in _file_cache:
                cached_mtime, cached_content = _file_cache[cache_key]
                if cached_mtime == current_mtime:
                    logger.info(f"Using cached full content for: {filename}")
                    return {
                        "filename": filename,
                        "content": cached_content,
                        "total_lines": len(cached_content.splitlines()),
                        "success": True,
                        "cached": True
                    }
            
            # Read full file
            logger.info(f"Reading full Python file: {filename}")
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cache it
            _file_cache[cache_key] = (current_mtime, content)
            
            return {
                "filename": filename,
                "content": content,
                "total_lines": len(content.splitlines()),
                "success": True,
                "cached": False
            }
        
        # For chunked reads
        logger.info(f"Reading {filename} lines {start_line} to {start_line + num_lines - 1}")
        with open(filename, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        total_lines = len(all_lines)
        
        # Adjust for 1-indexed start_line
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, start_idx + num_lines)
        
        chunk_lines = all_lines[start_idx:end_idx]
        content = ''.join(chunk_lines)
        
        logger.info(f"Successfully read {len(chunk_lines)} lines from {filename}")
        return {
            "filename": filename,
            "content": content,
            "start_line": start_line,
            "end_line": start_idx + len(chunk_lines),
            "lines_returned": len(chunk_lines),
            "total_lines": total_lines,
            "success": True,
            "cached": False,
            "note": f"Showing lines {start_line}-{start_idx + len(chunk_lines)} of {total_lines}. Use start_line and num_lines to read other sections."
        }
    except FileNotFoundError:
        logger.error(f"File not found: {filename}", exc_info=True)
        return {"error": f"File not found: {filename}"}
    except Exception as e:
        logger.error(f"Failed to read Python file {filename}: {str(e)}", exc_info=True)
        return {"error": f"Failed to read file: {str(e)}"}

def edit_python_file(filename, old_content, new_content):
    """Edit a Python file (app.py or models.py) by replacing content"""
    allowed_files = ['app.py', 'models.py']
    
    if filename not in allowed_files:
        return {"error": f"Access denied. Only these files can be edited: {', '.join(allowed_files)}"}
    
    try:
        logger.info(f"Editing Python file: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        if old_content not in current_content:
            return {"error": "Old content not found in file. Please read the file first to get the exact content."}
        
        updated_content = current_content.replace(old_content, new_content, 1)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"Successfully edited Python file: {filename}")
        return {
            "filename": filename,
            "success": True,
            "message": f"Successfully updated {filename}. Remember to restart the Flask server for changes to take effect!"
        }
    except Exception as e:
        logger.error(f"Failed to edit Python file {filename}: {str(e)}", exc_info=True)
        return {"error": f"Failed to edit file: {str(e)}"}

AVAILABLE_FUNCTIONS = {
    "list_render_services": list_render_services,
    "get_render_service": get_render_service,
    "restart_render_service": restart_render_service,
    "suspend_render_service": suspend_render_service,
    "resume_render_service": resume_render_service,
    "check_namecheap_domain": check_namecheap_domain,
    "list_namecheap_domains": list_namecheap_domains,
    "get_namecheap_domain_info": get_namecheap_domain_info,
    "read_dashboard_file": read_dashboard_file,
    "edit_dashboard_file": edit_dashboard_file,
    "create_html_page": create_html_page,
    "read_python_file": read_python_file,
    "edit_python_file": edit_python_file,
    "read_env_variables": read_env_variables
}

def process_admin_command(user_message, conversation_history=None):
    """Process an admin command using AI with function calling"""
    if not anthropic_client:
        return {
            "response": "Claude API is not configured. Please set the ANTHROPIC_API_KEY environment variable to enable AI admin features.",
            "conversation_history": conversation_history or []
        }
    
    if conversation_history is None:
        conversation_history = []
    
    messages = [
        {
            "role": "system",
            "content": """You are Coey, a full-stack AI developer with self-healing capabilities.

CAPABILITIES:
• Render: list, restart, suspend, resume services
• Namecheap: check domains, list domains, get info
• Files: read/edit HTML, CSS, Python (app.py, models.py)
• Create: new HTML pages, Flask routes, database models
• Env: read environment variables (API keys, secrets, config)
• Debug & Self-Heal: automatically detect and fix issues

SELF-HEALING MODE:
When errors occur or performance issues are detected:
1. Read the affected file to diagnose the problem
2. Identify root cause (syntax errors, imports, logic bugs, performance issues like repeated file reads)
3. Fix the issue following best practices (add caching, status updates, optimize prompts)
4. Verify the fix by reading the file back
5. Explain what was broken and how you fixed it

PERFORMANCE FIXES:
If slowness detected, check admin_ai_bot.py for:
- Missing file caching in read functions (add mtime-based cache)
- Missing status updates during function execution (add yield status messages)
- Unnecessary file reads in prompts (optimize system prompt to discourage this)

AUTO-FIX PATTERNS:
• Streaming issues: Check stream=True in OpenAI calls
• Performance/slowness: Add file caching, status updates, avoid unnecessary file reads
• Import errors: Add missing imports
• Syntax errors: Fix Python/JS syntax
• Type errors: Add proper type handling
• LSP errors: Fix type mismatches and undefined references
• Function errors: Check parameters and return values
• API issues: Validate requests and responses
• Large file reads: Implement caching with mtime checks to avoid re-reading unchanged files

PROACTIVE MONITORING:
• Check logs for errors before and after changes
• Validate code follows existing patterns
• Test critical paths (streaming, function calls, API integrations)
• Monitor performance and optimize when needed

WORKFLOW:
1. Only read files when necessary (don't read app.py/models.py for simple questions)
2. When reading Python files, use chunks (200 lines) for speed - default parameters are optimized
3. Make precise edits
4. Verify changes only if editing
5. Test if critical
6. Explain clearly

PERFORMANCE BEST PRACTICES:
• Use chunked reading: Read 200-line sections instead of full files for instant responses
• Only use num_lines=-1 when you absolutely need the entire file
• For simple questions about the app, use your knowledge - don't read files
• Reading specific sections is 5-10x faster than reading everything

For backend changes, remind user to restart Flask server. Be proactive, self-reliant, and fix issues before they impact users."""
        }
    ] + conversation_history + [{"role": "user", "content": user_message}]
    
    try:
        logger.info(f"Processing admin command: {user_message}")
        system_message = messages[0]["content"]
        user_messages = messages[1:]
        
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system_message,
            messages=user_messages,
            tools=FUNCTION_DEFINITIONS
        )
        
        tool_calls = [block for block in response.content if block.type == "tool_use"]
        
        if tool_calls:
            user_messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            tool_results = []
            for tool_call in tool_calls:
                function_name = tool_call.name
                function_args = tool_call.input
                
                logger.info(f"Executing function: {function_name} with args: {function_args}")
                
                if function_name in AVAILABLE_FUNCTIONS:
                    function_response = AVAILABLE_FUNCTIONS[function_name](**function_args)
                    logger.info(f"Function {function_name} response: {function_response}")
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps(function_response)
                    })
                else:
                    logger.warning(f"Unknown function called: {function_name}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps({"error": f"Unknown function: {function_name}"})
                    })
            
            user_messages.append({
                "role": "user",
                "content": tool_results
            })
            
            final_response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_message,
                messages=user_messages
            )
            
            logger.info("Successfully processed command with tool calls")
            text_content = " ".join([block.text for block in final_response.content if block.type == "text"])
            return {
                "response": text_content,
                "conversation_history": user_messages
            }
        else:
            logger.info("Processed command without tool calls")
            text_content = " ".join([block.text for block in response.content if block.type == "text"])
            return {
                "response": text_content,
                "conversation_history": user_messages
            }
            
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}", exc_info=True)
        return {
            "response": f"I encountered an error while processing your command: {str(e)}. Please check the configuration and try again.",
            "conversation_history": conversation_history
        }

def process_admin_command_streaming(user_message, conversation_history=None):
    """Process an admin command with streaming responses"""
    if not anthropic_client:
        yield json.dumps({
            "type": "error",
            "content": "Claude API is not configured. Please set the ANTHROPIC_API_KEY environment variable to enable AI admin features."
        }) + "\n"
        return
    
    if conversation_history is None:
        conversation_history = []
    
    messages = [
        {
            "role": "system",
            "content": """You are Coey, a full-stack AI developer with self-healing capabilities.

CAPABILITIES:
• Render: list, restart, suspend, resume services
• Namecheap: check domains, list domains, get info
• Files: read/edit HTML, CSS, Python (app.py, models.py)
• Create: new HTML pages, Flask routes, database models
• Env: read environment variables (API keys, secrets, config)
• Debug & Self-Heal: automatically detect and fix issues

SELF-HEALING MODE:
When errors occur or performance issues are detected:
1. Read the affected file to diagnose the problem
2. Identify root cause (syntax errors, imports, logic bugs, performance issues like repeated file reads)
3. Fix the issue following best practices (add caching, status updates, optimize prompts)
4. Verify the fix by reading the file back
5. Explain what was broken and how you fixed it

PERFORMANCE FIXES:
If slowness detected, check admin_ai_bot.py for:
- Missing file caching in read functions (add mtime-based cache)
- Missing status updates during function execution (add yield status messages)
- Unnecessary file reads in prompts (optimize system prompt to discourage this)

AUTO-FIX PATTERNS:
• Streaming issues: Check stream=True in OpenAI calls
• Performance/slowness: Add file caching, status updates, avoid unnecessary file reads
• Import errors: Add missing imports
• Syntax errors: Fix Python/JS syntax
• Type errors: Add proper type handling
• LSP errors: Fix type mismatches and undefined references
• Function errors: Check parameters and return values
• API issues: Validate requests and responses
• Large file reads: Implement caching with mtime checks to avoid re-reading unchanged files

PROACTIVE MONITORING:
• Check logs for errors before and after changes
• Validate code follows existing patterns
• Test critical paths (streaming, function calls, API integrations)
• Monitor performance and optimize when needed

WORKFLOW:
1. Only read files when necessary (don't read app.py/models.py for simple questions)
2. When reading Python files, use chunks (200 lines) for speed - default parameters are optimized
3. Make precise edits
4. Verify changes only if editing
5. Test if critical
6. Explain clearly

PERFORMANCE BEST PRACTICES:
• Use chunked reading: Read 200-line sections instead of full files for instant responses
• Only use num_lines=-1 when you absolutely need the entire file
• For simple questions about the app, use your knowledge - don't read files
• Reading specific sections is 5-10x faster than reading everything

For backend changes, remind user to restart Flask server. Be proactive, self-reliant, and fix issues before they impact users."""
        }
    ] + conversation_history + [{"role": "user", "content": user_message}]
    
    try:
        logger.info(f"Processing admin command (streaming): {user_message}")
        
        # Start streaming immediately
        yield json.dumps({"type": "status", "content": "Thinking..."}) + "\n"
        
        system_message = messages[0]["content"]
        user_messages = messages[1:]
        
        # Use Claude's API (non-streaming for now - streaming can be added later)
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system_message,
            messages=user_messages,
            tools=FUNCTION_DEFINITIONS
        )
        
        # Check for tool calls in Claude's response
        tool_calls = [block for block in response.content if block.type == "tool_use"]
        text_blocks = [block for block in response.content if block.type == "text"]
        
        # Yield any initial text content
        for text_block in text_blocks:
            if text_block.text:
                yield json.dumps({"type": "content", "content": text_block.text}) + "\n"
        
        # If we have tool calls, execute them
        if tool_calls:
            yield json.dumps({"type": "status", "content": "Executing actions..."}) + "\n"
            
            user_messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            tool_results = []
            
            # Execute each function with status updates
            for tc in tool_calls:
                function_name = tc.name
                function_args = tc.input
                
                # Show what we're doing
                action_msg = f"Running {function_name}..."
                if function_name == "read_python_file":
                    action_msg = f"Reading {function_args.get('filename', 'file')}..."
                elif function_name == "read_dashboard_file":
                    action_msg = f"Reading {function_args.get('filename', 'file')}..."
                elif function_name == "edit_python_file":
                    action_msg = f"Editing {function_args.get('filename', 'file')}..."
                elif function_name == "edit_dashboard_file":
                    action_msg = f"Updating {function_args.get('filename', 'file')}..."
                
                yield json.dumps({"type": "status", "content": action_msg}) + "\n"
                
                logger.info(f"Executing function: {function_name} with args: {function_args}")
                
                if function_name in AVAILABLE_FUNCTIONS:
                    function_response = AVAILABLE_FUNCTIONS[function_name](**function_args)
                    logger.info(f"Function {function_name} response: {function_response}")
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": json.dumps(function_response)
                    })
            
            # Add tool results to messages
            user_messages.append({
                "role": "user",
                "content": tool_results
            })
            
            # Get final response from Claude
            final_response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_message,
                messages=user_messages
            )
            
            # Extract and yield text content
            text_content = " ".join([block.text for block in final_response.content if block.type == "text"])
            if text_content:
                yield json.dumps({"type": "content", "content": text_content}) + "\n"
            
            yield json.dumps({"type": "done", "conversation_history": user_messages}) + "\n"
        else:
            # No tool calls - return the initial response
            yield json.dumps({"type": "done", "conversation_history": user_messages}) + "\n"
            
    except Exception as e:
        logger.error(f"Error processing streaming command: {str(e)}", exc_info=True)
        yield json.dumps({"type": "error", "error": f"I encountered an error: {str(e)}"}) + "\n"
