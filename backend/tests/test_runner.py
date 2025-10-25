"""
Test Runner
Comprehensive test execution and reporting
"""
import pytest
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import subprocess

class TestRunner:
    """Comprehensive test runner for the NLP Query Engine."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites."""
        self.start_time = time.time()
        
        print("🚀 Starting comprehensive test suite...")
        print("=" * 60)
        
        # Run different test categories
        test_categories = [
            ("unit", "Unit Tests", self.run_unit_tests),
            ("integration", "Integration Tests", self.run_integration_tests),
            ("performance", "Performance Tests", self.run_performance_tests),
            ("security", "Security Tests", self.run_security_tests),
            ("e2e", "End-to-End Tests", self.run_e2e_tests)
        ]
        
        for category, name, test_func in test_categories:
            print(f"\n📋 Running {name}...")
            print("-" * 40)
            
            try:
                result = test_func()
                self.test_results[category] = result
                print(f"✅ {name} completed successfully")
            except Exception as e:
                print(f"❌ {name} failed: {str(e)}")
                self.test_results[category] = {
                    "success": False,
                    "error": str(e),
                    "tests_run": 0,
                    "tests_passed": 0,
                    "tests_failed": 0
                }
        
        self.end_time = time.time()
        self.generate_report()
        
        return self.test_results
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""
        return self._run_pytest([
            "tests/test_schema_service.py",
            "-v",
            "--tb=short",
            "--junitxml=test-results/unit-tests.xml"
        ])
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        return self._run_pytest([
            "tests/test_integration.py",
            "-v",
            "--tb=short",
            "--junitxml=test-results/integration-tests.xml"
        ])
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        return self._run_pytest([
            "tests/test_performance.py",
            "-v",
            "--tb=short",
            "--junitxml=test-results/performance-tests.xml",
            "-m", "not slow"
        ])
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests."""
        return self._run_pytest([
            "tests/test_security.py",
            "-v",
            "--tb=short",
            "--junitxml=test-results/security-tests.xml"
        ])
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests."""
        return self._run_pytest([
            "tests/test_integration.py::TestEndToEndWorkflows",
            "-v",
            "--tb=short",
            "--junitxml=test-results/e2e-tests.xml"
        ])
    
    def _run_pytest(self, args: List[str]) -> Dict[str, Any]:
        """Run pytest with given arguments."""
        cmd = ["python", "-m", "pytest"] + args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "tests_run": self._parse_test_count(result.stdout, "collected"),
                "tests_passed": self._parse_test_count(result.stdout, "passed"),
                "tests_failed": self._parse_test_count(result.stdout, "failed")
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test timeout",
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
    
    def _parse_test_count(self, output: str, keyword: str) -> int:
        """Parse test count from pytest output."""
        lines = output.split('\n')
        for line in lines:
            if keyword in line.lower():
                # Extract number from line
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    return int(numbers[0])
        return 0
    
    def generate_report(self):
        """Generate comprehensive test report."""
        total_time = self.end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 TEST REPORT")
        print("=" * 60)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for category, result in self.test_results.items():
            if result.get("success", False):
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            
            tests_run = result.get("tests_run", 0)
            tests_passed = result.get("tests_passed", 0)
            tests_failed = result.get("tests_failed", 0)
            
            total_tests += tests_run
            total_passed += tests_passed
            total_failed += tests_failed
            
            print(f"{category.upper():<15} {status:<10} {tests_run:>3} tests ({tests_passed} passed, {tests_failed} failed)")
        
        print("-" * 60)
        print(f"{'TOTAL':<15} {'':<10} {total_tests:>3} tests ({total_passed} passed, {total_failed} failed)")
        print(f"{'TIME':<15} {'':<10} {total_time:.2f} seconds")
        
        # Calculate success rate
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"{'SUCCESS RATE':<15} {'':<10} {success_rate:.1f}%")
        
        # Save detailed report
        self._save_detailed_report()
    
    def _save_detailed_report(self):
        """Save detailed test report to file."""
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time": self.end_time - self.start_time,
            "results": self.test_results
        }
        
        os.makedirs("test-results", exist_ok=True)
        
        with open("test-results/detailed-report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: test-results/detailed-report.json")

def main():
    """Main test runner entry point."""
    runner = TestRunner()
    results = runner.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(result.get("success", False) for result in results.values())
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
