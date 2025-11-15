import os
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional

class NamecheapClient:
    def __init__(self):
        self.api_user = os.getenv('NAMECHEAP_API_USER', '')
        self.api_key = os.getenv('NAMECHEAP_API_KEY', '')
        self.username = os.getenv('NAMECHEAP_USERNAME', self.api_user)
        self.client_ip = os.getenv('NAMECHEAP_CLIENT_IP', '')
        
        # Use sandbox by default for testing
        self.sandbox = os.getenv('NAMECHEAP_SANDBOX', 'true').lower() == 'true'
        self.base_url = 'https://api.sandbox.namecheap.com/xml.response' if self.sandbox else 'https://api.namecheap.com/xml.response'
        
        # Mock mode for testing without credentials
        self.mock_mode = os.getenv('NAMECHEAP_MOCK_MODE', 'true').lower() == 'true'
        
        if not self.mock_mode and (not self.api_key or not self.api_user or not self.client_ip):
            print("[Namecheap] WARNING: API credentials not configured. Running in MOCK MODE.")
            self.mock_mode = True
    
    def _make_request(self, command: str, extra_params: Dict = None) -> Optional[ET.Element]:
        """Make API request to Namecheap"""
        params = {
            'ApiUser': self.api_user,
            'ApiKey': self.api_key,
            'UserName': self.username,
            'ClientIp': self.client_ip,
            'Command': command
        }
        
        if extra_params:
            params.update(extra_params)
        
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"[Namecheap] HTTP Error: {response.status_code}")
                return None
            
            root = ET.fromstring(response.text)
            return root
            
        except Exception as e:
            print(f"[Namecheap] Request error: {str(e)}")
            return None
    
    def check_domain_availability(self, domain_name: str) -> Dict:
        """Check if a domain is available for registration"""
        if self.mock_mode:
            print(f"[Namecheap] MOCK MODE - Showing {domain_name} as available")
            return {
                'success': True,
                'available': True,
                'domain': domain_name,
                'price': '9.99',
                'mock': True
            }
        
        try:
            print(f"[Namecheap] Checking domain: {domain_name}")
            
            root = self._make_request('namecheap.domains.check', {
                'DomainList': domain_name
            })
            
            if root is None:
                return {
                    'success': False,
                    'error': 'Failed to connect to Namecheap API'
                }
            
            # Parse XML response
            # Structure: <ApiResponse><CommandResponse><DomainCheckResult Domain="..." Available="true/false" /></CommandResponse></ApiResponse>
            status = root.get('Status')
            
            if status != 'OK':
                errors = root.findall('.//Error')
                error_msg = errors[0].text if errors else 'Unknown error'
                print(f"[Namecheap] API Error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Find domain check result
            domain_result = root.find('.//DomainCheckResult')
            
            if domain_result is None:
                return {
                    'success': False,
                    'error': 'Invalid API response format'
                }
            
            is_available = domain_result.get('Available', 'false').lower() == 'true'
            premium = domain_result.get('IsPremiumName', 'false').lower() == 'true'
            
            print(f"[Namecheap] Domain {domain_name}: {'Available' if is_available else 'Not Available'}")
            
            return {
                'success': True,
                'available': is_available,
                'domain': domain_name,
                'premium': premium,
                'mock': False
            }
            
        except Exception as e:
            print(f"[Namecheap] Unexpected error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def register_domain(self, domain_name: str, user_email: str, user_full_name: str, years: int = 1) -> Dict:
        """Register a domain (requires contact information)"""
        if self.mock_mode:
            print(f"[Namecheap] MOCK MODE - Simulating successful registration")
            return {
                'success': True,
                'domain': domain_name,
                'message': 'Domain registration simulated (MOCK MODE)',
                'mock': True
            }
        
        try:
            # Split full name into first and last
            name_parts = user_full_name.split(' ', 1)
            first_name = name_parts[0] if name_parts else 'User'
            last_name = name_parts[1] if len(name_parts) > 1 else 'Account'
            
            print(f"[Namecheap] Registering domain: {domain_name}")
            
            # Note: This requires complete contact information
            # For production, you'll need to collect full address, phone, etc.
            params = {
                'DomainName': domain_name,
                'Years': str(years),
                # Registrant Contact
                'RegistrantFirstName': first_name,
                'RegistrantLastName': last_name,
                'RegistrantAddress1': '123 Main St',  # TODO: Collect from user
                'RegistrantCity': 'Los Angeles',
                'RegistrantStateProvince': 'CA',
                'RegistrantPostalCode': '90001',
                'RegistrantCountry': 'US',
                'RegistrantPhone': '+1.3105551234',  # TODO: Collect from user
                'RegistrantEmailAddress': user_email,
                # Tech/Admin/Billing contacts (can be same as registrant)
                'TechFirstName': first_name,
                'TechLastName': last_name,
                'TechAddress1': '123 Main St',
                'TechCity': 'Los Angeles',
                'TechStateProvince': 'CA',
                'TechPostalCode': '90001',
                'TechCountry': 'US',
                'TechPhone': '+1.3105551234',
                'TechEmailAddress': user_email,
                'AdminFirstName': first_name,
                'AdminLastName': last_name,
                'AdminAddress1': '123 Main St',
                'AdminCity': 'Los Angeles',
                'AdminStateProvince': 'CA',
                'AdminPostalCode': '90001',
                'AdminCountry': 'US',
                'AdminPhone': '+1.3105551234',
                'AdminEmailAddress': user_email,
                'AuxBillingFirstName': first_name,
                'AuxBillingLastName': last_name,
                'AuxBillingAddress1': '123 Main St',
                'AuxBillingCity': 'Los Angeles',
                'AuxBillingStateProvince': 'CA',
                'AuxBillingPostalCode': '90001',
                'AuxBillingCountry': 'US',
                'AuxBillingPhone': '+1.3105551234',
                'AuxBillingEmailAddress': user_email,
            }
            
            root = self._make_request('namecheap.domains.create', params)
            
            if root is None:
                return {
                    'success': False,
                    'error': 'Failed to connect to Namecheap API'
                }
            
            status = root.get('Status')
            
            if status != 'OK':
                errors = root.findall('.//Error')
                error_msg = errors[0].text if errors else 'Unknown error'
                print(f"[Namecheap] Registration Error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Parse registration result
            domain_result = root.find('.//DomainCreateResult')
            
            if domain_result is None:
                return {
                    'success': False,
                    'error': 'Invalid API response format'
                }
            
            registered = domain_result.get('Registered', 'false').lower() == 'true'
            domain = domain_result.get('Domain', domain_name)
            order_id = domain_result.get('OrderID', '')
            transaction_id = domain_result.get('TransactionID', '')
            
            if registered:
                print(f"[Namecheap] Successfully registered {domain}")
                return {
                    'success': True,
                    'domain': domain,
                    'order_id': order_id,
                    'transaction_id': transaction_id,
                    'mock': False
                }
            else:
                return {
                    'success': False,
                    'error': 'Domain registration failed',
                    'domain': domain
                }
                
        except Exception as e:
            print(f"[Namecheap] Registration error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_domain_info(self, domain_name: str) -> Dict:
        """Get information about a registered domain"""
        if self.mock_mode:
            return {
                'success': True,
                'domain': domain_name,
                'mock': True
            }
        
        try:
            root = self._make_request('namecheap.domains.getInfo', {
                'DomainName': domain_name
            })
            
            if root is None:
                return {
                    'success': False,
                    'error': 'Failed to connect to Namecheap API'
                }
            
            status = root.get('Status')
            
            if status != 'OK':
                errors = root.findall('.//Error')
                error_msg = errors[0].text if errors else 'Unknown error'
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Parse domain info
            domain_info = root.find('.//DomainGetInfoResult')
            
            if domain_info is None:
                return {
                    'success': False,
                    'error': 'Invalid API response format'
                }
            
            return {
                'success': True,
                'domain': domain_info.get('DomainName', domain_name),
                'status': domain_info.get('Status', 'Unknown'),
                'mock': False
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
