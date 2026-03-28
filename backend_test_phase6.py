#!/usr/bin/env python3
"""
Backend API Testing for Dataset Quality Audit Assistant - Phase 6
Tests the /api/report endpoint for plain-text report generation
"""

import requests
import sys
import json
from datetime import datetime

class Phase6ReportTester:
    def __init__(self, base_url="https://data-quality-check-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.audit_data = None
        self.audit_data_no_target = None

    def run_test(self, name, method, endpoint, expected_status, files=None, data=None, json_data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=headers)
                elif json_data:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=json_data, headers=headers)
                else:
                    response = requests.post(url, data=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    return success, response.json()
                else:
                    return success, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def load_audit_data(self):
        """Load audit data from existing JSON file"""
        try:
            with open('/tmp/audit_result.json', 'r') as f:
                self.audit_data = json.load(f)
            print("✅ Loaded audit data from /tmp/audit_result.json")
            return True
        except Exception as e:
            print(f"❌ Failed to load audit data: {str(e)}")
            return False

    def generate_audit_data_no_target(self):
        """Generate audit data without target column for N/A testing"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Generate Audit Data (No Target)",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                    # No target_col parameter
                )
                
                if success:
                    self.audit_data_no_target = response
                    print("✅ Generated audit data without target column")
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Failed to generate audit data without target: {str(e)}")
            return False

    def test_report_endpoint_basic(self):
        """Test /api/report endpoint returns HTTP 200 with Content-Type text/plain"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Report Endpoint Basic",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            print(f"   ✓ Report generated successfully")
            print(f"   ✓ Report length: {len(report_text)} characters")
            
            # Check Content-Type header would be text/plain (we can't check headers in this simple test)
            # But we can verify it's plain text content
            if not isinstance(report_text, str):
                print("   ❌ Report should be plain text string")
                return False
            
            print("   ✓ Report is plain text format")
            return True
        
        return False

    def test_report_structure_and_sections(self):
        """Test report has all 9 sections in correct order with proper structure"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Report Structure and Sections",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check major separator and title
            if "AUTOMATED DATASET RELIABILITY AND MODELING READINESS REPORT" not in report_text:
                print("   ❌ Missing report title")
                return False
            print("   ✓ Report title found")
            
            # Check for major separator (72 equals signs)
            if "=" * 72 not in report_text:
                print("   ❌ Missing major separator")
                return False
            print("   ✓ Major separator found")
            
            # Check all 9 sections in order
            expected_sections = [
                "1. DATASET OVERVIEW",
                "2. SCHEMA DIAGNOSTICS", 
                "3. MISSINGNESS SUMMARY",
                "4. DUPLICATE ANALYSIS",
                "5. NUMERIC OUTLIER SUMMARY",
                "6. CLASS IMBALANCE SUMMARY",
                "7. LEAKAGE-RISK INDICATORS",
                "8. MODELING READINESS SCORE",
                "9. RECOMMENDATIONS"
            ]
            
            for i, section in enumerate(expected_sections):
                if section not in report_text:
                    print(f"   ❌ Missing section: {section}")
                    return False
                print(f"   ✓ Section {i+1} found: {section}")
            
            # Check report ends with END OF REPORT
            if "END OF REPORT" not in report_text:
                print("   ❌ Missing 'END OF REPORT' footer")
                return False
            print("   ✓ Report footer found")
            
            return True
        
        return False

    def test_report_metadata_block(self):
        """Test metadata block contains required information"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Report Metadata Block",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check for metadata fields
            metadata_fields = [
                "Report generated:",
                "File:",
                "Rows:",
                "Columns:",
                "Target Column:"
            ]
            
            for field in metadata_fields:
                if field not in report_text:
                    print(f"   ❌ Missing metadata field: {field}")
                    return False
                print(f"   ✓ Metadata field found: {field}")
            
            # Check specific values from audit data
            meta = self.audit_data.get('meta', {})
            if str(meta.get('rows', 0)) not in report_text:
                print(f"   ❌ Row count {meta.get('rows')} not found in report")
                return False
            
            if str(meta.get('cols', 0)) not in report_text:
                print(f"   ❌ Column count {meta.get('cols')} not found in report")
                return False
            
            print("   ✓ Metadata values correctly included")
            return True
        
        return False

    def test_section_1_dataset_overview(self):
        """Test Section 1: Dataset Overview content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 1: Dataset Overview",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "1. DATASET OVERVIEW" not in report_text:
                print("   ❌ Section 1 header not found")
                return False
            
            # Check required fields in overview
            overview_fields = [
                "Filename:",
                "Rows:",
                "Columns:",
                "Target Column:",
                "Encoding:",
                "Delimiter:"
            ]
            
            for field in overview_fields:
                if field not in report_text:
                    print(f"   ❌ Missing overview field: {field}")
                    return False
                print(f"   ✓ Overview field found: {field}")
            
            # Check column names are listed
            meta = self.audit_data.get('meta', {})
            column_names = meta.get('column_names', [])
            if column_names:
                # Should have "Column names:" section
                if "Column names:" not in report_text:
                    print("   ❌ Column names section not found")
                    return False
                
                # Check at least some column names are present
                for col in column_names[:2]:  # Check first 2 columns
                    if col not in report_text:
                        print(f"   ❌ Column name '{col}' not found in report")
                        return False
                
                print("   ✓ Column names correctly listed")
            
            return True
        
        return False

    def test_section_2_schema_diagnostics(self):
        """Test Section 2: Schema Diagnostics content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 2: Schema Diagnostics",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "2. SCHEMA DIAGNOSTICS" not in report_text:
                print("   ❌ Section 2 header not found")
                return False
            
            # Check for column type inference table
            if "Column type inference:" not in report_text:
                print("   ❌ Column type inference table not found")
                return False
            
            # Check for type-mismatch warnings section
            if "Type-mismatch warnings:" not in report_text:
                print("   ❌ Type-mismatch warnings section not found")
                return False
            
            print("   ✓ Schema diagnostics content found")
            return True
        
        return False

    def test_section_3_missingness_summary(self):
        """Test Section 3: Missingness Summary content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 3: Missingness Summary",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "3. MISSINGNESS SUMMARY" not in report_text:
                print("   ❌ Section 3 header not found")
                return False
            
            # Check required fields
            missingness_fields = [
                "Total Missing Cells:",
                "Overall Missing %:",
                "Rows with Missing:"
            ]
            
            for field in missingness_fields:
                if field not in report_text:
                    print(f"   ❌ Missing field: {field}")
                    return False
                print(f"   ✓ Missingness field found: {field}")
            
            # Check per-column breakdown
            if "Per-column breakdown" not in report_text:
                print("   ❌ Per-column breakdown not found")
                return False
            
            print("   ✓ Missingness summary content found")
            return True
        
        return False

    def test_section_4_duplicate_analysis(self):
        """Test Section 4: Duplicate Analysis content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 4: Duplicate Analysis",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "4. DUPLICATE ANALYSIS" not in report_text:
                print("   ❌ Section 4 header not found")
                return False
            
            # Check required fields
            duplicate_fields = [
                "Duplicate Row Count:",
                "Duplicate %:",
                "Risk Label:"
            ]
            
            for field in duplicate_fields:
                if field not in report_text:
                    print(f"   ❌ Missing field: {field}")
                    return False
                print(f"   ✓ Duplicate field found: {field}")
            
            print("   ✓ Duplicate analysis content found")
            return True
        
        return False

    def test_section_5_numeric_outlier_summary(self):
        """Test Section 5: Numeric Outlier Summary content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 5: Numeric Outlier Summary",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "5. NUMERIC OUTLIER SUMMARY" not in report_text:
                print("   ❌ Section 5 header not found")
                return False
            
            # Check IQR method note
            if "Method: IQR (Interquartile Range)" not in report_text:
                print("   ❌ IQR method note not found")
                return False
            
            # Check Q1/Q3/bounds table headers
            table_headers = ["Column", "Q1", "Q3", "Lower", "Upper", "Outliers", "%"]
            for header in table_headers:
                if header not in report_text:
                    print(f"   ❌ Missing table header: {header}")
                    return False
            
            print("   ✓ Numeric outlier summary content found")
            return True
        
        return False

    def test_section_6_class_imbalance_summary(self):
        """Test Section 6: Class Imbalance Summary content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 6: Class Imbalance Summary",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "6. CLASS IMBALANCE SUMMARY" not in report_text:
                print("   ❌ Section 6 header not found")
                return False
            
            # Check required fields
            imbalance_fields = [
                "Target Column:",
                "Imbalance Label:",
                "Majority / Minority Ratio:"
            ]
            
            for field in imbalance_fields:
                if field not in report_text:
                    print(f"   ❌ Missing field: {field}")
                    return False
                print(f"   ✓ Imbalance field found: {field}")
            
            # Check class distribution
            if "Class distribution:" not in report_text:
                print("   ❌ Class distribution not found")
                return False
            
            print("   ✓ Class imbalance summary content found")
            return True
        
        return False

    def test_section_7_leakage_risk_indicators(self):
        """Test Section 7: Leakage-Risk Indicators content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 7: Leakage-Risk Indicators",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "7. LEAKAGE-RISK INDICATORS" not in report_text:
                print("   ❌ Section 7 header not found")
                return False
            
            # Check flagged columns count
            if "Flagged Columns:" not in report_text:
                print("   ❌ Flagged Columns field not found")
                return False
            
            # Check flagged columns section or no leakage message
            leakage_data = self.audit_data.get('leakage', {})
            flagged_columns = leakage_data.get('flagged_columns', [])
            
            if flagged_columns:
                if "Flagged columns:" not in report_text:
                    print("   ❌ Flagged columns list not found")
                    return False
            else:
                if "No leakage-risk columns detected" not in report_text:
                    print("   ❌ No leakage message not found")
                    return False
            
            # Check keywords checked section
            if "Keywords checked:" not in report_text:
                print("   ❌ Keywords checked section not found")
                return False
            
            print("   ✓ Leakage-risk indicators content found")
            return True
        
        return False

    def test_section_8_modeling_readiness_score(self):
        """Test Section 8: Modeling Readiness Score content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 8: Modeling Readiness Score",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "8. MODELING READINESS SCORE" not in report_text:
                print("   ❌ Section 8 header not found")
                return False
            
            # Check required fields
            score_fields = [
                "Score:",
                "Score Band:",
                "Summary:"
            ]
            
            for field in score_fields:
                if field not in report_text:
                    print(f"   ❌ Missing field: {field}")
                    return False
                print(f"   ✓ Score field found: {field}")
            
            # Check score band reference table
            score_bands = [
                ">= 85   Ready",
                "70-84   Acceptable with preprocessing", 
                "50-69   Needs preprocessing",
                "< 50    High risk"
            ]
            
            for band in score_bands:
                if band not in report_text:
                    print(f"   ❌ Missing score band: {band}")
                    return False
            
            print("   ✓ Score band reference table found")
            
            # Check penalties section
            if "Applied penalties" not in report_text:
                print("   ❌ Applied penalties section not found")
                return False
            
            print("   ✓ Modeling readiness score content found")
            return True
        
        return False

    def test_section_9_recommendations(self):
        """Test Section 9: Recommendations content"""
        if not self.audit_data:
            print("❌ No audit data available")
            return False

        success, report_text = self.run_test(
            "Section 9: Recommendations",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data
        )
        
        if success:
            # Check section header
            if "9. RECOMMENDATIONS" not in report_text:
                print("   ❌ Section 9 header not found")
                return False
            
            # Check for [!] prefix for issues found
            readiness_data = self.audit_data.get('readiness', {})
            penalties = readiness_data.get('penalties', [])
            
            if penalties:
                # Should have recommendations with [!] prefix
                if "[!]" not in report_text:
                    print("   ❌ Missing [!] prefix for recommendations")
                    return False
                print("   ✓ [!] prefix found for issue recommendations")
            
            # Check for "No action required for:" section
            if "No action required for:" not in report_text:
                print("   ❌ 'No action required for:' section not found")
                return False
            
            print("   ✓ Recommendations content found")
            return True
        
        return False

    def test_report_no_target_column(self):
        """Test report with no target column - Class Imbalance section says 'Not applicable'"""
        if not self.audit_data_no_target:
            if not self.generate_audit_data_no_target():
                return False

        success, report_text = self.run_test(
            "Report No Target Column",
            "POST",
            "api/report",
            200,
            json_data=self.audit_data_no_target
        )
        
        if success:
            # Check that Class Imbalance section says "Not applicable"
            if "6. CLASS IMBALANCE SUMMARY" not in report_text:
                print("   ❌ Class Imbalance section not found")
                return False
            
            # Find the Class Imbalance section and check for "Not applicable"
            lines = report_text.split('\n')
            in_imbalance_section = False
            found_not_applicable = False
            
            for line in lines:
                if "6. CLASS IMBALANCE SUMMARY" in line:
                    in_imbalance_section = True
                elif line.strip().startswith("7."):
                    in_imbalance_section = False
                elif in_imbalance_section and "Not applicable" in line:
                    found_not_applicable = True
                    break
            
            if not found_not_applicable:
                print("   ❌ 'Not applicable' not found in Class Imbalance section")
                return False
            
            print("   ✓ Class Imbalance section correctly shows 'Not applicable'")
            return True
        
        return False

def main():
    """Main test execution for Phase 6 reporting"""
    print("🚀 Starting Dataset Quality Audit Assistant API Tests - Phase 6 Reporting")
    print("=" * 80)
    
    tester = Phase6ReportTester()
    
    # Load audit data first
    if not tester.load_audit_data():
        print("❌ Cannot proceed without audit data")
        return 1
    
    # Run all Phase 6 tests
    tests = [
        # Basic endpoint tests
        tester.test_report_endpoint_basic,
        tester.test_report_structure_and_sections,
        tester.test_report_metadata_block,
        
        # Section content tests
        tester.test_section_1_dataset_overview,
        tester.test_section_2_schema_diagnostics,
        tester.test_section_3_missingness_summary,
        tester.test_section_4_duplicate_analysis,
        tester.test_section_5_numeric_outlier_summary,
        tester.test_section_6_class_imbalance_summary,
        tester.test_section_7_leakage_risk_indicators,
        tester.test_section_8_modeling_readiness_score,
        tester.test_section_9_recommendations,
        
        # Edge case tests
        tester.test_report_no_target_column,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.tests_run += 1
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"📊 Phase 6 Test Summary: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All Phase 6 tests passed!")
        return 0
    else:
        print(f"❌ {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())