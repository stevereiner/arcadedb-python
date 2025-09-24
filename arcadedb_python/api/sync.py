from .client import Client
from ..exceptions import LoginFailedException, parse_error_response

import json
import logging
import requests
import re


def _filter_payload_for_log(payload: dict, max_chars: int = 500) -> dict:
    """Filter payload for logging by truncating embedding data to avoid cluttering logs.
    
    Args:
        payload: The payload dictionary to filter
        max_chars: Maximum characters to show for the entire payload
        
    Returns:
        Filtered payload dictionary with embedding data truncated
    """
    if not isinstance(payload, dict):
        return payload
    
    # Create a copy to avoid modifying the original
    filtered_payload = payload.copy()
    
    # Filter the 'command' field if it contains embedding arrays
    if 'command' in filtered_payload and isinstance(filtered_payload['command'], str):
        command = filtered_payload['command']
        
        # Pattern to match embedding arrays like [0.123, -0.456, 0.789, ...]
        embedding_pattern = r'\[[-0-9.,\s]+\]'
        
        def replace_embedding(match):
            full_embedding = match.group(0)
            if len(full_embedding) > 50:  # If embedding is long, truncate it
                # Extract first few values to show dimension info
                values = re.findall(r'[-0-9.]+', full_embedding[:100])
                total_values = len(re.findall(r'[-0-9.]+', full_embedding))
                if len(values) >= 2:
                    return f"[{values[0]}, {values[1]}, ...] (dim:{total_values})"
                else:
                    return f"[...] (dim:{total_values})"
            return full_embedding
        
        # Replace embedding arrays with truncated versions
        filtered_command = re.sub(embedding_pattern, replace_embedding, command)
        
        # Limit total command length
        if len(filtered_command) > max_chars:
            filtered_command = filtered_command[:max_chars] + "..."
        
        filtered_payload['command'] = filtered_command
    
    return filtered_payload


class SyncClient(Client):
    def __init__(self, host: str, port: str, protocol: str = "http", **kwargs):
        super().__init__(host, port, protocol, **kwargs)

    def subhandler(self, response: requests.Response, return_headers: bool=False, query: str = None):
        if response.status_code >= 400:
            try:
                json_decoded_data = response.json()
            except json.JSONDecodeError:
                # If response is not JSON, create a basic error structure
                json_decoded_data = {
                    'error': f'HTTP {response.status_code} Error',
                    'detail': response.text or 'No additional details',
                    'exception': 'HTTPException'
                }
            
            logging.error(f"ArcadeDB Error Response: {json_decoded_data}")
            
            # Use the new exception parsing system
            exception = parse_error_response(json_decoded_data, query=query)
            raise exception
        
        response.raise_for_status()
        logging.debug(f"response: {response.text}")
        if return_headers is False:
            if len(response.text) > 0:
                try:
                    return response.json()["result"]
                except:
                    return response.text
            else:
                return
        else:
            return  response.headers

    def post(self, endpoint: str, payload: dict, return_headers: bool=False, extra_headers: dict = {}) -> requests.Response:
        endpoint = self._get_endpoint(endpoint)
        filtered_payload = _filter_payload_for_log(payload)
        logging.info(f"posting to {endpoint} with payload {filtered_payload}")
        response = requests.post(
            endpoint,
            data=json.dumps(payload),
            headers={**self.headers,**extra_headers},
            auth=(self.username, self.password),
        )
        # Extract query from payload for better error reporting
        query = payload.get('command') if isinstance(payload, dict) else None
        return self.subhandler(response, return_headers=return_headers, query=query)

    def get(self, endpoint: str, return_headers: bool=False, extra_headers: dict = {}) -> requests.Response:
        endpoint = self._get_endpoint(endpoint)
        logging.info(f"submitting get request to {endpoint}")
        response = requests.get(
            endpoint,
            auth=(self.username, self.password),
            headers=extra_headers,
        )
        return self.subhandler(response, return_headers=return_headers)

