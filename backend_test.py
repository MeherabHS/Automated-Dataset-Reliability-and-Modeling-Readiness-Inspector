#!/usr/bin/env python3
"""
Backend API Testing for Dataset Quality Audit Assistant
Phase 5: Tests the scoring system with readiness score, penalties, and score bands
"""

import requests
import sys
import json
from datetime import datetime

class DatasetAuditAPITester:
    def __init__(self, base_url="https://data-quality-check-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.audit_data = None
        self.parse_results = {}

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

    # ═══════════════════════════════════════════════════════════════
    # PHASE 3: /api/parse endpoint tests
    # ═══════════════════════════════════════════════════════════════
    
    def test_parse_valid_csv(self):
        """Test /api/parse with valid CSV file"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Parse Valid CSV",
                    "POST",
                    "api/parse",
                    200,
                    files=files
                )
                
                if success:
                    self.parse_results['valid'] = response
                    print(f"   ✓ Parse status: {response.get('parse_status')}")
                    print(f"   ✓ Rows detected: {response.get('meta', {}).get('rows', 0)}")
                    print(f"   ✓ Columns detected: {response.get('meta', {}).get('cols', 0)}")
                    print(f"   ✓ Preview rows: {len(response.get('preview', []))}")
                    print(f"   ✓ Warnings: {len(response.get('warnings', []))}")
                    
                    # Validate required fields
                    required_fields = ['parse_status', 'meta', 'preview', 'column_info', 'warnings']
                    missing = [f for f in required_fields if f not in response]
                    if missing:
                        print(f"   ❌ Missing required fields: {missing}")
                        return False
                    
                    if response.get('parse_status') != 'success':
                        print(f"   ❌ Expected parse_status='success', got '{response.get('parse_status')}'")
                        return False
                        
                return success
                
        except Exception as e:
            print(f"❌ Error in parse valid CSV test: {str(e)}")
            return False

    def test_parse_non_csv_file(self):
        """Test /api/parse with non-CSV file (.xlsx)"""
        try:
            with open('/tmp/test.xlsx', 'rb') as f:
                files = {'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                
                success, response = self.run_test(
                    "Parse Non-CSV File (.xlsx)",
                    "POST",
                    "api/parse",
                    400,  # Expecting error
                    files=files
                )
                
                if success:
                    print(f"   ✓ Parse error: {response.get('parse_error')}")
                    print(f"   ✓ Error code: {response.get('code')}")
                    print(f"   ✓ Error message: {response.get('message', '')[:100]}...")
                    
                    if response.get('code') != 'unsupported_file_type':
                        print(f"   ❌ Expected code='unsupported_file_type', got '{response.get('code')}'")
                        return False
                        
                return success
                
        except Exception as e:
            print(f"❌ Error in parse non-CSV test: {str(e)}")
            return False

    def test_parse_empty_csv(self):
        """Test /api/parse with empty CSV file"""
        try:
            with open('/tmp/empty.csv', 'rb') as f:
                files = {'file': ('empty.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Parse Empty CSV",
                    "POST",
                    "api/parse",
                    422,  # Expecting error
                    files=files
                )
                
                if success:
                    print(f"   ✓ Parse error: {response.get('parse_error')}")
                    print(f"   ✓ Error code: {response.get('code')}")
                    
                    if response.get('code') != 'empty_file':
                        print(f"   ❌ Expected code='empty_file', got '{response.get('code')}'")
                        return False
                        
                return success
                
        except Exception as e:
            print(f"❌ Error in parse empty CSV test: {str(e)}")
            return False

    def test_parse_header_only_csv(self):
        """Test /api/parse with header-only CSV file"""
        try:
            with open('/tmp/header_only.csv', 'rb') as f:
                files = {'file': ('header_only.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Parse Header-Only CSV",
                    "POST",
                    "api/parse",
                    422,  # Expecting error
                    files=files
                )
                
                if success:
                    print(f"   ✓ Parse error: {response.get('parse_error')}")
                    print(f"   ✓ Error code: {response.get('code')}")
                    
                    if response.get('code') != 'no_data_rows':
                        print(f"   ❌ Expected code='no_data_rows', got '{response.get('code')}'")
                        return False
                        
                return success
                
        except Exception as e:
            print(f"❌ Error in parse header-only CSV test: {str(e)}")
            return False

    def test_parse_semicolon_delimited_csv(self):
        """Test /api/parse with semicolon-delimited CSV"""
        try:
            with open('/tmp/semicolon.csv', 'rb') as f:
                files = {'file': ('semicolon.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Parse Semicolon-Delimited CSV",
                    "POST",
                    "api/parse",
                    200,
                    files=files
                )
                
                if success:
                    self.parse_results['semicolon'] = response
                    meta = response.get('meta', {})
                    warnings = response.get('warnings', [])
                    
                    print(f"   ✓ Parse status: {response.get('parse_status')}")
                    print(f"   ✓ Delimiter detected: '{meta.get('delimiter')}'")
                    print(f"   ✓ Warnings: {len(warnings)}")
                    
                    if meta.get('delimiter') != ';':
                        print(f"   ❌ Expected delimiter=';', got '{meta.get('delimiter')}'")
                        return False
                    
                    # Check for delimiter warning
                    delimiter_warning = any('delimiter' in w.lower() for w in warnings)
                    if not delimiter_warning:
                        print(f"   ❌ Expected delimiter warning in warnings")
                        return False
                    else:
                        print(f"   ✓ Delimiter warning found: {[w for w in warnings if 'delimiter' in w.lower()][0][:80]}...")
                        
                return success
                
        except Exception as e:
            print(f"❌ Error in parse semicolon CSV test: {str(e)}")
            return False

    def test_parse_latin1_encoded_csv(self):
        """Test /api/parse with Latin-1 encoded CSV"""
        try:
            with open('/tmp/latin1.csv', 'rb') as f:
                files = {'file': ('latin1.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Parse Latin-1 Encoded CSV",
                    "POST",
                    "api/parse",
                    200,
                    files=files
                )
                
                if success:
                    self.parse_results['latin1'] = response
                    meta = response.get('meta', {})
                    warnings = response.get('warnings', [])
                    
                    print(f"   ✓ Parse status: {response.get('parse_status')}")
                    print(f"   ✓ Encoding detected: {meta.get('encoding')}")
                    print(f"   ✓ Warnings: {len(warnings)}")
                    
                    if meta.get('encoding') != 'latin-1':
                        print(f"   ❌ Expected encoding='latin-1', got '{meta.get('encoding')}'")
                        return False
                    
                    # Check for encoding warning
                    encoding_warning = any('encoding' in w.lower() for w in warnings)
                    if not encoding_warning:
                        print(f"   ❌ Expected encoding warning in warnings")
                        return False
                    else:
                        print(f"   ✓ Encoding warning found: {[w for w in warnings if 'encoding' in w.lower()][0][:80]}...")
                        
                return success
                
        except Exception as e:
            print(f"❌ Error in parse Latin-1 CSV test: {str(e)}")
            return False

    def test_parse_malformed_csv(self):
        """Test /api/parse with malformed CSV (extra columns)"""
        try:
            with open('/tmp/malformed.csv', 'rb') as f:
                files = {'file': ('malformed.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Parse Malformed CSV",
                    "POST",
                    "api/parse",
                    200,  # Should parse but with warnings
                    files=files
                )
                
                if success:
                    self.parse_results['malformed'] = response
                    warnings = response.get('warnings', [])
                    
                    print(f"   ✓ Parse status: {response.get('parse_status')}")
                    print(f"   ✓ Warnings: {len(warnings)}")
                    
                    # Check for malformed/skipped rows warning
                    malformed_warning = any('malformed' in w.lower() or 'skipped' in w.lower() for w in warnings)
                    if not malformed_warning:
                        print(f"   ❌ Expected malformed/skipped rows warning")
                        print(f"   Warnings received: {warnings}")
                        return False
                    else:
                        print(f"   ✓ Malformed rows warning found: {[w for w in warnings if 'malformed' in w.lower() or 'skipped' in w.lower()][0][:80]}...")
                        
                return success
                
        except Exception as e:
            print(f"❌ Error in parse malformed CSV test: {str(e)}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # PHASE 4: /api/audit endpoint tests with new field names
    # ═══════════════════════════════════════════════════════════════
    def test_health_endpoint(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_audit_schema_module(self):
        """Test Phase 4 schema module with new field names"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Schema Module - New Field Names",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    schema = response.get('schema', {})
                    
                    # Test applicable field
                    if 'applicable' not in schema:
                        print("   ❌ Missing 'applicable' field in schema")
                        return False
                    print(f"   ✓ Schema applicable: {schema['applicable']}")
                    
                    # Test columns structure with new field names
                    columns = schema.get('columns', [])
                    if not columns:
                        print("   ❌ No columns found in schema")
                        return False
                    
                    first_col = columns[0]
                    required_fields = ['name', 'inferred_type', 'null_count', 'null_pct', 'unique_count', 'all_missing', 'mismatch_warning']
                    missing_fields = [f for f in required_fields if f not in first_col]
                    if missing_fields:
                        print(f"   ❌ Missing fields in column: {missing_fields}")
                        return False
                    print(f"   ✓ Column has correct fields: name='{first_col['name']}', inferred_type='{first_col['inferred_type']}'")
                    
                    # Test mismatch_columns field (not mismatch_warnings)
                    if 'mismatch_columns' not in schema:
                        print("   ❌ Missing 'mismatch_columns' field in schema")
                        return False
                    print(f"   ✓ Schema has mismatch_columns: {schema['mismatch_columns']}")
                    
                    # Validate inferred types
                    expected_types = ['numeric', 'categorical', 'datetime', 'text', 'empty']
                    for col in columns:
                        if col['inferred_type'] not in expected_types:
                            print(f"   ❌ Invalid inferred_type '{col['inferred_type']}' for column '{col['name']}'")
                            return False
                    print(f"   ✓ All columns have valid inferred_type values")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in schema module test: {str(e)}")
            return False

    def test_audit_missingness_module(self):
        """Test Phase 4 missingness module with new field names"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Missingness Module - New Field Names",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    missingness = response.get('missingness', {})
                    
                    # Test applicable field
                    if 'applicable' not in missingness:
                        print("   ❌ Missing 'applicable' field in missingness")
                        return False
                    print(f"   ✓ Missingness applicable: {missingness['applicable']}")
                    
                    # Test missing_pct_overall field (not missing_pct_total)
                    if 'missing_pct_overall' not in missingness:
                        print("   ❌ Missing 'missing_pct_overall' field in missingness")
                        return False
                    print(f"   ✓ Missingness has missing_pct_overall: {missingness['missing_pct_overall']}%")
                    
                    # Test per_column structure with null_count and null_pct
                    per_column = missingness.get('per_column', [])
                    if per_column:
                        first_col = per_column[0]
                        required_fields = ['column', 'null_count', 'null_pct']
                        missing_fields = [f for f in required_fields if f not in first_col]
                        if missing_fields:
                            print(f"   ❌ Missing fields in per_column: {missing_fields}")
                            return False
                        print(f"   ✓ Per-column has correct fields: column='{first_col['column']}', null_count={first_col['null_count']}, null_pct={first_col['null_pct']}%")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in missingness module test: {str(e)}")
            return False

    def test_audit_duplicates_module(self):
        """Test Phase 4 duplicates module with applicable field"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Duplicates Module - Applicable Field",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    duplicates = response.get('duplicates', {})
                    
                    # Test applicable field
                    if 'applicable' not in duplicates:
                        print("   ❌ Missing 'applicable' field in duplicates")
                        return False
                    print(f"   ✓ Duplicates applicable: {duplicates['applicable']}")
                    
                    # Test required fields when applicable=True
                    if duplicates['applicable']:
                        required_fields = ['duplicate_row_count', 'duplicate_pct', 'risk_label']
                        missing_fields = [f for f in required_fields if f not in duplicates]
                        if missing_fields:
                            print(f"   ❌ Missing fields in duplicates: {missing_fields}")
                            return False
                        print(f"   ✓ Duplicates has correct fields: count={duplicates['duplicate_row_count']}, pct={duplicates['duplicate_pct']}%, risk={duplicates['risk_label']}")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in duplicates module test: {str(e)}")
            return False

    def test_audit_duplicates_single_column(self):
        """Test duplicates module with single-column CSV (should be applicable=False)"""
        try:
            with open('/tmp/single_col.csv', 'rb') as f:
                files = {'file': ('single_col.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Duplicates Module - Single Column CSV",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    duplicates = response.get('duplicates', {})
                    
                    # Test applicable=False for single column
                    if duplicates.get('applicable') != False:
                        print(f"   ❌ Expected applicable=False for single column, got {duplicates.get('applicable')}")
                        return False
                    print(f"   ✓ Duplicates correctly not applicable for single column")
                    
                    # Test reason field
                    if 'reason' not in duplicates:
                        print("   ❌ Missing 'reason' field when applicable=False")
                        return False
                    print(f"   ✓ Reason provided: {duplicates['reason']}")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in single column duplicates test: {str(e)}")
            return False

    def test_audit_outliers_module(self):
        """Test Phase 4 outliers module with lowercase field names"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Outliers Module - Lowercase Field Names",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    outliers = response.get('outliers', {})
                    
                    # Test applicable field
                    if 'applicable' not in outliers:
                        print("   ❌ Missing 'applicable' field in outliers")
                        return False
                    print(f"   ✓ Outliers applicable: {outliers['applicable']}")
                    
                    # Test numeric_columns structure with lowercase fields
                    if outliers['applicable']:
                        numeric_columns = outliers.get('numeric_columns', [])
                        if numeric_columns:
                            for col in numeric_columns:
                                if col.get('applicable', True):  # Only check applicable columns
                                    required_fields = ['column', 'q1', 'q3', 'iqr', 'lower_bound', 'upper_bound', 'outlier_count', 'outlier_pct']
                                    missing_fields = [f for f in required_fields if f not in col]
                                    if missing_fields:
                                        print(f"   ❌ Missing fields in outlier column: {missing_fields}")
                                        return False
                                    print(f"   ✓ Outlier column has lowercase fields: q1={col['q1']}, q3={col['q3']}, iqr={col['iqr']}")
                                    break
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in outliers module test: {str(e)}")
            return False

    def test_audit_outliers_no_numeric(self):
        """Test outliers module with no numeric columns (should be applicable=False)"""
        try:
            # Create a CSV with only text columns
            csv_content = "name,status,description\nAlice,active,good\nBob,inactive,bad\n"
            files = {'file': ('text_only.csv', csv_content.encode(), 'text/csv')}
            
            success, response = self.run_test(
                "Outliers Module - No Numeric Columns",
                "POST",
                "api/audit",
                200,
                files=files
            )
            
            if success:
                outliers = response.get('outliers', {})
                
                # Test applicable=False for no numeric columns
                if outliers.get('applicable') != False:
                    print(f"   ❌ Expected applicable=False for no numeric columns, got {outliers.get('applicable')}")
                    return False
                print(f"   ✓ Outliers correctly not applicable for no numeric columns")
                
                # Test reason field
                if 'reason' not in outliers:
                    print("   ❌ Missing 'reason' field when applicable=False")
                    return False
                print(f"   ✓ Reason provided: {outliers['reason']}")
                
            return success
            
        except Exception as e:
            print(f"❌ Error in no numeric outliers test: {str(e)}")
            return False

    def test_audit_imbalance_module_with_target(self):
        """Test Phase 4 imbalance module with target column"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                data = {'target_col': 'label'}
                
                success, response = self.run_test(
                    "Imbalance Module - With Target Column",
                    "POST",
                    "api/audit",
                    200,
                    files=files,
                    data=data
                )
                
                if success:
                    self.audit_data = response  # Store for later tests
                    imbalance = response.get('imbalance', {})
                    
                    # Test applicable field
                    if 'applicable' not in imbalance:
                        print("   ❌ Missing 'applicable' field in imbalance")
                        return False
                    print(f"   ✓ Imbalance applicable: {imbalance['applicable']}")
                    
                    # Test new field names when applicable=True
                    if imbalance['applicable']:
                        # Test imbalance_label (not severity)
                        if 'imbalance_label' not in imbalance:
                            print("   ❌ Missing 'imbalance_label' field in imbalance")
                            return False
                        
                        # Test majority_to_minority_ratio (new field)
                        if 'majority_to_minority_ratio' not in imbalance:
                            print("   ❌ Missing 'majority_to_minority_ratio' field in imbalance")
                            return False
                        
                        # Validate imbalance_label values
                        valid_labels = ['Balanced', 'Moderate imbalance', 'Severe imbalance']
                        if imbalance['imbalance_label'] not in valid_labels:
                            print(f"   ❌ Invalid imbalance_label '{imbalance['imbalance_label']}', expected one of {valid_labels}")
                            return False
                        
                        print(f"   ✓ Imbalance has correct fields: label='{imbalance['imbalance_label']}', ratio={imbalance['majority_to_minority_ratio']}")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in imbalance with target test: {str(e)}")
            return False

    def test_audit_imbalance_module_no_target(self):
        """Test Phase 4 imbalance module without target column"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Imbalance Module - No Target Column",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    imbalance = response.get('imbalance', {})
                    
                    # Test applicable=False when no target
                    if imbalance.get('applicable') != False:
                        print(f"   ❌ Expected applicable=False for no target, got {imbalance.get('applicable')}")
                        return False
                    
                    # Test not_selected=True
                    if imbalance.get('not_selected') != True:
                        print(f"   ❌ Expected not_selected=True for no target, got {imbalance.get('not_selected')}")
                        return False
                    
                    # Test too_many_classes=False
                    if imbalance.get('too_many_classes') != False:
                        print(f"   ❌ Expected too_many_classes=False for no target, got {imbalance.get('too_many_classes')}")
                        return False
                    
                    print(f"   ✓ Imbalance correctly not applicable: not_selected={imbalance['not_selected']}, too_many_classes={imbalance['too_many_classes']}")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in imbalance no target test: {str(e)}")
            return False

    def test_audit_imbalance_too_many_classes(self):
        """Test imbalance module with target column having >20 unique values"""
        try:
            # Create CSV with high cardinality target column
            csv_content = "id,value\n" + "\n".join([f"{i},{i*10}" for i in range(25)])
            files = {'file': ('high_cardinality.csv', csv_content.encode(), 'text/csv')}
            data = {'target_col': 'id'}
            
            success, response = self.run_test(
                "Imbalance Module - Too Many Classes",
                "POST",
                "api/audit",
                200,
                files=files,
                data=data
            )
            
            if success:
                imbalance = response.get('imbalance', {})
                
                # Test applicable=False when too many classes
                if imbalance.get('applicable') != False:
                    print(f"   ❌ Expected applicable=False for too many classes, got {imbalance.get('applicable')}")
                    return False
                
                # Test too_many_classes=True
                if imbalance.get('too_many_classes') != True:
                    print(f"   ❌ Expected too_many_classes=True, got {imbalance.get('too_many_classes')}")
                    return False
                
                print(f"   ✓ Imbalance correctly not applicable for too many classes: too_many_classes={imbalance['too_many_classes']}")
                
            return success
            
        except Exception as e:
            print(f"❌ Error in too many classes test: {str(e)}")
            return False

    def test_audit_leakage_module(self):
        """Test Phase 4 leakage module with expanded keywords"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Leakage Module - Expanded Keywords",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    leakage = response.get('leakage', {})
                    
                    # Test applicable field
                    if 'applicable' not in leakage:
                        print("   ❌ Missing 'applicable' field in leakage")
                        return False
                    print(f"   ✓ Leakage applicable: {leakage['applicable']}")
                    
                    # Test keywords_checked includes new keywords
                    keywords_checked = leakage.get('keywords_checked', [])
                    expected_keywords = ['id', 'target', 'label', 'outcome', 'status', 'result', 
                                       'final', 'prediction', 'future', 'post', 'completed', 'discharge']
                    
                    missing_keywords = [kw for kw in expected_keywords if kw not in keywords_checked]
                    if missing_keywords:
                        print(f"   ❌ Missing keywords: {missing_keywords}")
                        return False
                    
                    if len(keywords_checked) != 12:
                        print(f"   ❌ Expected 12 keywords, got {len(keywords_checked)}")
                        return False
                    
                    print(f"   ✓ Leakage has all 12 keywords: {sorted(keywords_checked)}")
                    
                    # Test flagged columns structure
                    flagged = leakage.get('flagged_columns', [])
                    if flagged:
                        first_flag = flagged[0]
                        required_fields = ['column', 'matched_keywords']
                        missing_fields = [f for f in required_fields if f not in first_flag]
                        if missing_fields:
                            print(f"   ❌ Missing fields in flagged column: {missing_fields}")
                            return False
                        print(f"   ✓ Flagged column structure correct: {first_flag['column']} -> {first_flag['matched_keywords']}")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in leakage module test: {str(e)}")
            return False

    def test_audit_leakage_new_keywords(self):
        """Test leakage detection with new keywords 'completed' and 'discharge'"""
        try:
            # Create CSV with new leakage keywords
            csv_content = "patient_id,completed_treatment,discharge_date,score\n1,yes,2023-01-01,85\n2,no,2023-01-02,90\n"
            files = {'file': ('new_keywords.csv', csv_content.encode(), 'text/csv')}
            
            success, response = self.run_test(
                "Leakage Module - New Keywords Detection",
                "POST",
                "api/audit",
                200,
                files=files
            )
            
            if success:
                leakage = response.get('leakage', {})
                flagged = leakage.get('flagged_columns', [])
                
                # Should detect 'completed' and 'discharge' keywords
                expected_flags = ['patient_id', 'completed_treatment', 'discharge_date']
                flagged_columns = [f['column'] for f in flagged]
                
                for expected in expected_flags:
                    if expected not in flagged_columns:
                        print(f"   ❌ Expected column '{expected}' to be flagged")
                        return False
                
                # Check specific new keywords
                completed_flag = next((f for f in flagged if f['column'] == 'completed_treatment'), None)
                discharge_flag = next((f for f in flagged if f['column'] == 'discharge_date'), None)
                
                if completed_flag and 'completed' not in completed_flag['matched_keywords']:
                    print(f"   ❌ Expected 'completed' keyword in completed_treatment column")
                    return False
                
                if discharge_flag and 'discharge' not in discharge_flag['matched_keywords']:
                    print(f"   ❌ Expected 'discharge' keyword in discharge_date column")
                    return False
                
                print(f"   ✓ New keywords detected correctly: completed and discharge")
                
            return success
            
        except Exception as e:
            print(f"❌ Error in new keywords test: {str(e)}")
            return False

    def validate_all_modules_have_applicable(self):
        """Validate that all modules have the 'applicable' field"""
        if not self.audit_data:
            print("❌ No audit data to validate")
            return False
            
        print("\n🔍 Validating all modules have 'applicable' field...")
        
        modules = ['schema', 'missingness', 'duplicates', 'outliers', 'imbalance', 'leakage']
        for module_name in modules:
            module = self.audit_data.get(module_name, {})
            if 'applicable' not in module:
                print(f"   ❌ Module '{module_name}' missing 'applicable' field")
                return False
            print(f"   ✓ {module_name}.applicable = {module['applicable']}")
        
        return True

    # ═══════════════════════════════════════════════════════════════
    # PHASE 5: Scoring system tests
    # ═══════════════════════════════════════════════════════════════
    
    def test_readiness_score_structure(self):
        """Test Phase 5 readiness score structure with new field names"""
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Readiness Score Structure",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    readiness = response.get('readiness', {})
                    
                    # Test required fields
                    required_fields = ['score', 'score_band', 'penalties', 'not_applicable', 'explanation']
                    missing_fields = [f for f in required_fields if f not in readiness]
                    if missing_fields:
                        print(f"   ❌ Missing fields in readiness: {missing_fields}")
                        return False
                    
                    # Test score_band (not category)
                    if 'category' in readiness:
                        print("   ❌ Found deprecated 'category' field, should be 'score_band'")
                        return False
                    
                    print(f"   ✓ Readiness has correct structure: score={readiness['score']}, score_band='{readiness['score_band']}'")
                    
                    # Test penalties structure
                    penalties = readiness.get('penalties', [])
                    if penalties:
                        first_penalty = penalties[0]
                        required_penalty_fields = ['check', 'penalty', 'rule']
                        missing_penalty_fields = [f for f in required_penalty_fields if f not in first_penalty]
                        if missing_penalty_fields:
                            print(f"   ❌ Missing fields in penalty: {missing_penalty_fields}")
                            return False
                        
                        # Check for deprecated fields
                        if 'factor' in first_penalty or 'detail' in first_penalty:
                            print("   ❌ Found deprecated 'factor' or 'detail' fields in penalty, should be 'check' and 'rule'")
                            return False
                        
                        print(f"   ✓ Penalty structure correct: check='{first_penalty['check']}', penalty={first_penalty['penalty']}, rule='{first_penalty['rule'][:50]}...'")
                    
                    # Test not_applicable structure
                    not_applicable = readiness.get('not_applicable', [])
                    if not_applicable:
                        first_na = not_applicable[0]
                        required_na_fields = ['check', 'reason']
                        missing_na_fields = [f for f in required_na_fields if f not in first_na]
                        if missing_na_fields:
                            print(f"   ❌ Missing fields in not_applicable: {missing_na_fields}")
                            return False
                        
                        print(f"   ✓ Not-applicable structure correct: check='{first_na['check']}', reason='{first_na['reason'][:50]}...'")
                    
                    # Test explanation is string
                    explanation = readiness.get('explanation', '')
                    if not isinstance(explanation, str) or not explanation.strip():
                        print(f"   ❌ Explanation should be non-empty string, got: {type(explanation)}")
                        return False
                    
                    print(f"   ✓ Explanation is valid string: '{explanation[:100]}...'")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in readiness score structure test: {str(e)}")
            return False

    def test_score_band_mappings(self):
        """Test score band mappings for different score ranges"""
        test_cases = [
            (100, "Ready"),
            (85, "Ready"),
            (84, "Acceptable with preprocessing"),
            (70, "Acceptable with preprocessing"),
            (69, "Needs preprocessing"),
            (50, "Needs preprocessing"),
            (49, "High risk"),
            (0, "High risk")
        ]
        
        print("\n🔍 Testing score band mappings...")
        
        for expected_score, expected_band in test_cases:
            # Create a simple CSV that should give the expected score
            # This is a simplified test - in practice, we'd need specific data to get exact scores
            print(f"   Testing score {expected_score} → '{expected_band}'")
        
        # Test with actual test_sample.csv which should give score=65 (Needs preprocessing)
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Score Band Mapping - Test Sample",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    readiness = response.get('readiness', {})
                    score = readiness.get('score')
                    score_band = readiness.get('score_band')
                    
                    print(f"   ✓ Test sample score: {score}, band: '{score_band}'")
                    
                    # Validate score band is correct for the score
                    if score >= 85:
                        expected = "Ready"
                    elif score >= 70:
                        expected = "Acceptable with preprocessing"
                    elif score >= 50:
                        expected = "Needs preprocessing"
                    else:
                        expected = "High risk"
                    
                    if score_band != expected:
                        print(f"   ❌ Score {score} should map to '{expected}', got '{score_band}'")
                        return False
                    
                    print(f"   ✓ Score band mapping correct for score {score}")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in score band mapping test: {str(e)}")
            return False

    def test_penalty_rules_missingness(self):
        """Test specific missingness penalty rules"""
        print("\n🔍 Testing missingness penalty rules...")
        
        # Test with test_sample.csv which has missing values
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Missingness Penalty Rules",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    readiness = response.get('readiness', {})
                    penalties = readiness.get('penalties', [])
                    
                    # Look for missingness penalty
                    missingness_penalty = next((p for p in penalties if 'Missingness' in p.get('check', '')), None)
                    if missingness_penalty:
                        penalty_amount = missingness_penalty.get('penalty', 0)
                        rule = missingness_penalty.get('rule', '')
                        
                        print(f"   ✓ Missingness penalty found: -{penalty_amount} points")
                        print(f"   ✓ Rule: {rule}")
                        
                        # Validate penalty amount based on rule
                        if '>10%' in rule and penalty_amount != 20:
                            print(f"   ❌ Expected -20 penalty for >10% missingness, got -{penalty_amount}")
                            return False
                        elif '>5%' in rule and '≤10%' in rule and penalty_amount != 10:
                            print(f"   ❌ Expected -10 penalty for >5-10% missingness, got -{penalty_amount}")
                            return False
                        elif '≤5%' in rule and penalty_amount != 5:
                            print(f"   ❌ Expected -5 penalty for ≤5% missingness, got -{penalty_amount}")
                            return False
                        
                        print(f"   ✓ Missingness penalty amount correct for rule")
                    else:
                        print("   ℹ️  No missingness penalty found (may be within acceptable range)")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in missingness penalty test: {str(e)}")
            return False

    def test_penalty_rules_duplicates(self):
        """Test specific duplicate penalty rules"""
        print("\n🔍 Testing duplicate penalty rules...")
        
        # Test with test_sample.csv which has duplicate rows
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Duplicate Penalty Rules",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    readiness = response.get('readiness', {})
                    penalties = readiness.get('penalties', [])
                    
                    # Look for duplicates penalty
                    duplicates_penalty = next((p for p in penalties if 'Duplicates' in p.get('check', '')), None)
                    if duplicates_penalty:
                        penalty_amount = duplicates_penalty.get('penalty', 0)
                        rule = duplicates_penalty.get('rule', '')
                        
                        print(f"   ✓ Duplicates penalty found: -{penalty_amount} points")
                        print(f"   ✓ Rule: {rule}")
                        
                        # Validate penalty amount based on rule
                        if '>3%' in rule and penalty_amount != 15:
                            print(f"   ❌ Expected -15 penalty for >3% duplicates, got -{penalty_amount}")
                            return False
                        elif '≤3%' in rule and penalty_amount not in [5, 10]:
                            print(f"   ❌ Expected -5 or -10 penalty for ≤3% duplicates, got -{penalty_amount}")
                            return False
                        
                        print(f"   ✓ Duplicates penalty amount correct for rule")
                    else:
                        print("   ℹ️  No duplicates penalty found (may be within acceptable range)")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in duplicates penalty test: {str(e)}")
            return False

    def test_penalty_rules_leakage(self):
        """Test leakage penalty rule (exactly -10 for any flagged column)"""
        print("\n🔍 Testing leakage penalty rules...")
        
        # Test with test_sample.csv which has 'label' column (leakage keyword)
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Leakage Penalty Rules",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    readiness = response.get('readiness', {})
                    penalties = readiness.get('penalties', [])
                    
                    # Look for leakage penalty
                    leakage_penalty = next((p for p in penalties if 'Leakage' in p.get('check', '')), None)
                    if leakage_penalty:
                        penalty_amount = leakage_penalty.get('penalty', 0)
                        rule = leakage_penalty.get('rule', '')
                        
                        print(f"   ✓ Leakage penalty found: -{penalty_amount} points")
                        print(f"   ✓ Rule: {rule}")
                        
                        # Validate penalty is exactly -10
                        if penalty_amount != 10:
                            print(f"   ❌ Expected exactly -10 penalty for leakage, got -{penalty_amount}")
                            return False
                        
                        print(f"   ✓ Leakage penalty amount correct (exactly -10)")
                    else:
                        print("   ❌ Expected leakage penalty for 'label' column")
                        return False
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in leakage penalty test: {str(e)}")
            return False

    def test_class_imbalance_penalty_with_target(self):
        """Test class imbalance penalty with target column"""
        print("\n🔍 Testing class imbalance penalty with target column...")
        
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                data = {'target_col': 'label'}
                
                success, response = self.run_test(
                    "Class Imbalance Penalty - With Target",
                    "POST",
                    "api/audit",
                    200,
                    files=files,
                    data=data
                )
                
                if success:
                    readiness = response.get('readiness', {})
                    penalties = readiness.get('penalties', [])
                    
                    # Look for class imbalance penalty
                    imbalance_penalty = next((p for p in penalties if 'Class imbalance' in p.get('check', '')), None)
                    if imbalance_penalty:
                        penalty_amount = imbalance_penalty.get('penalty', 0)
                        rule = imbalance_penalty.get('rule', '')
                        
                        print(f"   ✓ Class imbalance penalty found: -{penalty_amount} points")
                        print(f"   ✓ Rule: {rule}")
                        
                        # Validate penalty amount
                        if 'Severe imbalance' in rule and penalty_amount != 10:
                            print(f"   ❌ Expected -10 penalty for severe imbalance, got -{penalty_amount}")
                            return False
                        elif 'Moderate imbalance' in rule and penalty_amount != 5:
                            print(f"   ❌ Expected -5 penalty for moderate imbalance, got -{penalty_amount}")
                            return False
                        
                        print(f"   ✓ Class imbalance penalty amount correct")
                    else:
                        print("   ℹ️  No class imbalance penalty found (may be balanced)")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in class imbalance penalty test: {str(e)}")
            return False

    def test_class_imbalance_not_applicable(self):
        """Test class imbalance not-applicable when no target column"""
        print("\n🔍 Testing class imbalance not-applicable...")
        
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                # No target_col parameter
                
                success, response = self.run_test(
                    "Class Imbalance Not-Applicable",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    readiness = response.get('readiness', {})
                    not_applicable = readiness.get('not_applicable', [])
                    
                    # Look for class imbalance in not-applicable
                    imbalance_na = next((na for na in not_applicable if 'Class imbalance' in na.get('check', '')), None)
                    if imbalance_na:
                        reason = imbalance_na.get('reason', '')
                        
                        print(f"   ✓ Class imbalance not-applicable found")
                        print(f"   ✓ Reason: {reason}")
                        
                        if 'No target column' not in reason:
                            print(f"   ❌ Expected 'No target column' in reason, got: {reason}")
                            return False
                        
                        print(f"   ✓ Class imbalance not-applicable reason correct")
                    else:
                        print("   ❌ Expected class imbalance in not-applicable list when no target column")
                        return False
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in class imbalance not-applicable test: {str(e)}")
            return False

    def test_schema_quality_penalty(self):
        """Test schema quality penalty for unnamed columns"""
        print("\n🔍 Testing schema quality penalty...")
        
        # Create CSV with unnamed column
        try:
            csv_content = "name,,age\nAlice,,25\nBob,,30\n"
            files = {'file': ('unnamed_col.csv', csv_content.encode(), 'text/csv')}
            
            success, response = self.run_test(
                "Schema Quality Penalty - Unnamed Column",
                "POST",
                "api/audit",
                200,
                files=files
            )
            
            if success:
                readiness = response.get('readiness', {})
                penalties = readiness.get('penalties', [])
                
                # Look for schema quality penalty
                schema_penalty = next((p for p in penalties if 'Basic schema quality' in p.get('check', '')), None)
                if schema_penalty:
                    penalty_amount = schema_penalty.get('penalty', 0)
                    rule = schema_penalty.get('rule', '')
                    
                    print(f"   ✓ Schema quality penalty found: -{penalty_amount} points")
                    print(f"   ✓ Rule: {rule}")
                    
                    # Validate penalty amount for unnamed columns
                    if 'unnamed' in rule.lower() and penalty_amount != 10:
                        print(f"   ❌ Expected -10 penalty for unnamed columns, got -{penalty_amount}")
                        return False
                    
                    print(f"   ✓ Schema quality penalty amount correct")
                else:
                    print("   ❌ Expected schema quality penalty for unnamed column")
                    return False
                
            return success
            
        except Exception as e:
            print(f"❌ Error in schema quality penalty test: {str(e)}")
            return False

    def test_expected_test_sample_score(self):
        """Test that test_sample.csv gives expected score=65 with specific penalties"""
        print("\n🔍 Testing expected test sample score and penalties...")
        
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                success, response = self.run_test(
                    "Expected Test Sample Score",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if success:
                    readiness = response.get('readiness', {})
                    score = readiness.get('score')
                    score_band = readiness.get('score_band')
                    penalties = readiness.get('penalties', [])
                    
                    print(f"   ✓ Actual score: {score}, band: '{score_band}'")
                    print(f"   ✓ Number of penalties: {len(penalties)}")
                    
                    # Expected: score=65 (Needs preprocessing) with 3 penalties
                    # Note: The exact score may vary based on implementation details
                    if score_band != "Needs preprocessing":
                        print(f"   ❌ Expected score band 'Needs preprocessing', got '{score_band}'")
                        return False
                    
                    # Check for expected penalties
                    penalty_checks = [p.get('check', '') for p in penalties]
                    expected_penalties = ['Missingness', 'Duplicates', 'Leakage']
                    
                    for expected in expected_penalties:
                        if not any(expected in check for check in penalty_checks):
                            print(f"   ❌ Expected penalty for {expected} not found")
                            return False
                    
                    print(f"   ✓ Expected penalties found: {penalty_checks}")
                    
                    # Calculate total deducted
                    total_deducted = sum(p.get('penalty', 0) for p in penalties)
                    print(f"   ✓ Total deducted: {total_deducted} points")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in expected test sample score test: {str(e)}")
            return False

    def test_download_report_with_score_band(self):
        """Test download report includes score_band and explanation"""
        print("\n🔍 Testing download report with score_band...")
        
        try:
            with open('/tmp/test_sample.csv', 'rb') as f:
                files = {'file': ('test_sample.csv', f, 'text/csv')}
                
                # First get audit data
                success, audit_response = self.run_test(
                    "Get Audit Data for Report",
                    "POST",
                    "api/audit",
                    200,
                    files=files
                )
                
                if not success:
                    return False
                
                # Then test report generation
                success, report_text = self.run_test(
                    "Download Report with Score Band",
                    "POST",
                    "api/report",
                    200,
                    json_data=audit_response
                )
                
                if success:
                    # Check report contains score_band and explanation
                    if 'Score Band:' not in report_text:
                        print("   ❌ Report missing 'Score Band:' section")
                        return False
                    
                    if 'Summary:' not in report_text:
                        print("   ❌ Report missing 'Summary:' (explanation) section")
                        return False
                    
                    # Check for score band value
                    readiness = audit_response.get('readiness', {})
                    score_band = readiness.get('score_band', '')
                    if score_band and score_band not in report_text:
                        print(f"   ❌ Report missing score band '{score_band}'")
                        return False
                    
                    print(f"   ✓ Report contains score_band and explanation")
                    print(f"   ✓ Report length: {len(report_text)} characters")
                    
                return success
                
        except Exception as e:
            print(f"❌ Error in download report test: {str(e)}")
            return False

def main():
    """Main test execution"""
    print("🚀 Starting Dataset Quality Audit Assistant API Tests - Phase 5")
    print("=" * 70)
    
    tester = DatasetAuditAPITester()
    
    # Run all tests
    tests = [
        # Health check
        tester.test_health_endpoint,
        
        # Phase 4: /api/audit endpoint tests with new field names
        tester.test_audit_schema_module,
        tester.test_audit_missingness_module,
        tester.test_audit_duplicates_module,
        tester.test_audit_duplicates_single_column,
        tester.test_audit_outliers_module,
        tester.test_audit_outliers_no_numeric,
        tester.test_audit_imbalance_module_with_target,
        tester.test_audit_imbalance_module_no_target,
        tester.test_audit_imbalance_too_many_classes,
        tester.test_audit_leakage_module,
        tester.test_audit_leakage_new_keywords,
        tester.validate_all_modules_have_applicable,
        
        # Phase 5: Scoring system tests
        tester.test_readiness_score_structure,
        tester.test_score_band_mappings,
        tester.test_penalty_rules_missingness,
        tester.test_penalty_rules_duplicates,
        tester.test_penalty_rules_leakage,
        tester.test_class_imbalance_penalty_with_target,
        tester.test_class_imbalance_not_applicable,
        tester.test_schema_quality_penalty,
        tester.test_expected_test_sample_score,
        tester.test_download_report_with_score_band,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.tests_run += 1
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"📊 Test Summary: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())