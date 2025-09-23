from .client import Client, LoginFailedException

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

    def subhandler(self, response: requests.Response, return_headers: bool=False):
        if response.status_code >= 400 :
            json_decoded_data = response.json()
            print(json_decoded_data)
            java_error_code = json_decoded_data['exception'] if 'exception' in json_decoded_data else "Unknown error"
            detail_error_code = None
            if 'detail' in json_decoded_data:
                detail_error_code = json_decoded_data['detail']
            elif 'exception' in json_decoded_data:
                detail_error_code = json_decoded_data['exception']
            else:
                detail_error_code = "Unknown error"
            
            if java_error_code == "com.arcadedb.server.security.ServerSecurityException":
                raise LoginFailedException(java_error_code, detail_error_code)
            else:
                raise Exception(java_error_code, detail_error_code)
        
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
        return self.subhandler(response, return_headers=return_headers)

    def get(self, endpoint: str, return_headers: bool=False, extra_headers: dict = {}) -> requests.Response:
        endpoint = self._get_endpoint(endpoint)
        logging.info(f"submitting get request to {endpoint}")
        response = requests.get(
            endpoint,
            auth=(self.username, self.password),
            headers=extra_headers,
        )
        return self.subhandler(response, return_headers=return_headers)

