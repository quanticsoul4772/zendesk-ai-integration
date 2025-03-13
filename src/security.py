import os
import hmac
import hashlib
import ipaddress
from functools import wraps
from flask import request, jsonify, abort

import logging
logger = logging.getLogger(__name__)

# Load environment variables
WEBHOOK_SECRET_KEY = os.getenv("WEBHOOK_SECRET_KEY", "")
ALLOWED_IPS_RAW = os.getenv("ALLOWED_IPS", "").split(",")

# Parse allowed IPs and networks
ALLOWED_IPS = []
ALLOWED_NETWORKS = []
for ip_entry in ALLOWED_IPS_RAW:
    if ip_entry:
        try:
            if "/" in ip_entry:
                # This is a network in CIDR notation
                ALLOWED_NETWORKS.append(ipaddress.ip_network(ip_entry.strip()))
            else:
                # This is a single IP
                ALLOWED_IPS.append(ipaddress.ip_address(ip_entry.strip()))
        except ValueError as e:
            logger.error(f"Invalid IP or network: {ip_entry} - {e}")

def is_ip_allowed(client_ip):
    """Check if an IP is allowed based on the whitelist."""
    try:
        ip = ipaddress.ip_address(client_ip)
        
        # Check if IP is directly in whitelist
        if ip in ALLOWED_IPS:
            return True
            
        # Check if IP is in any of the allowed networks
        for network in ALLOWED_NETWORKS:
            if ip in network:
                return True
                
        return False
    except ValueError:
        # If we can't parse the IP, reject it
        return False

def verify_webhook_signature(payload, signature, secret_key=None):
    """
    Verify the HMAC signature of a webhook payload.
    
    Args:
        payload (bytes): The raw request payload
        signature (str): The signature provided in the request header
        secret_key (str, optional): The secret key to use. Defaults to env variable.
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature:
        return False
        
    key = secret_key or WEBHOOK_SECRET_KEY
    if not key:
        logger.warning("No webhook secret key configured!")
        return False
    
    calculated_signature = hmac.new(
        key=key.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(calculated_signature, signature)

def ip_whitelist(f):
    """Decorator to restrict access to whitelisted IPs."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        
        # Skip check if no IPs are defined (avoids lockout during development)
        if not ALLOWED_IPS and not ALLOWED_NETWORKS:
            return f(*args, **kwargs)
            
        if not is_ip_allowed(client_ip):
            logger.warning(f"Unauthorized access attempt from IP: {client_ip}")
            return jsonify({"error": "Access denied"}), 403
            
        return f(*args, **kwargs)
    return decorated_function

def webhook_auth(f):
    """Decorator to verify webhook signatures."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        payload = request.get_data()
        signature = request.headers.get('X-Zendesk-Webhook-Signature')
        
        # Skip check if no secret key is defined (development mode)
        if not WEBHOOK_SECRET_KEY:
            return f(*args, **kwargs)
        
        if not verify_webhook_signature(payload, signature):
            logger.warning(f"Invalid webhook signature: {signature}")
            return jsonify({"error": "Invalid signature"}), 401
            
        return f(*args, **kwargs)
    return decorated_function
