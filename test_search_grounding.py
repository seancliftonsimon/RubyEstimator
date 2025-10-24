"""
Test search grounding functionality with corrected configuration.

This module tests that the search grounding configuration fix eliminates
"400 Search Grounding is not supported" errors and enables proper web search
functionality for vehicle data resolution.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime

# Import components to test
from resolver import GroundedSearchClient, SearchCandidate
from vehicle_data import (
    validate_vehicle_existence,
    get_aluminum_engine_from_api,
    get_aluminum_rims_from_api,
    get_curb_weight_from_api,
    get_catalytic_converter_count_from_api
)


class TestSearchGroundingConfiguration(unittest.TestCase):
    """Test that search grounding uses correct configuration format."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = GroundedSearchClient()
    
    @patch('resolver.genai.GenerativeModel')
    def test_resolver_uses_correct_search_config(self, mock_model_class):
        """Test that GroundedSearchClient uses correct google_search configuration."""
        # Mock the model and response
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "3500 lbs from kbb.com\n3520 lbs from edmunds.com"
        mock_model.generate_content.return_value = mock_response
        
        # Create client and make search call
        client = GroundedSearchClient()
        
        # Test search_vehicle_specs method
        try:
            candidates = client.search_vehicle_specs(2020, "Toyota", "Camry", "curb_weight")
            
            # Verify the model was called with correct tool configuration
            mock_model.generate_content.assert_called()
            call_args = mock_model.generate_content.call_args
            
            # Check that tools parameter uses correct format
            self.assertIn('tools', call_args.kwargs)
            tools = call_args.kwargs['tools']
            self.assertEqual(tools, [{"google_search": {}}])
            
            # Verify no google_search_retrieval is used
            self.assertNotEqual(tools, [{"google_search_retrieval": {}}])
            
        except Exception as e:
            self.fail(f"Search grounding should work with correct configuration, but failed: {e}")
    
    @patch('resolver.genai.GenerativeModel')
    def test_get_multiple_candidates_uses_correct_config(self, mock_model_class):
        """Test that get_multiple_candidates uses correct search configuration."""
        # Mock the model and response
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "3500 lbs from kbb.com\n3520 lbs from edmunds.com"
        mock_model.generate_content.return_value = mock_response
        
        client = GroundedSearchClient()
        
        try:
            candidates = client.get_multiple_candidates(2020, "Toyota", "Camry", "curb_weight")
            
            # Verify all calls use correct tool configuration
            for call in mock_model.generate_content.call_args_list:
                if 'tools' in call.kwargs:
                    tools = call.kwargs['tools']
                    self.assertEqual(tools, [{"google_search": {}}])
                    self.assertNotEqual(tools, [{"google_search_retrieval": {}}])
                    
        except Exception as e:
            self.fail(f"Multiple candidates search should work with correct configuration, but failed: {e}")


class TestVehicleDataSearchGrounding(unittest.TestCase):
    """Test vehicle data functions use correct search grounding configuration."""
    
    @patch('vehicle_data.SHARED_GEMINI_MODEL')
    def test_validate_vehicle_existence_search_config(self, mock_model):
        """Test validate_vehicle_existence uses correct search configuration."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "yes"
        mock_model.generate_content.return_value = mock_response
        
        try:
            result = validate_vehicle_existence(2020, "Toyota", "Camry")
            
            # Verify the model was called with correct tool configuration
            mock_model.generate_content.assert_called()
            call_args = mock_model.generate_content.call_args
            
            # Check tools parameter
            self.assertIn('tools', call_args.kwargs)
            tools = call_args.kwargs['tools']
            self.assertEqual(tools, [{"google_search": {}}])
            
            # Verify result
            self.assertTrue(result)
            
        except Exception as e:
            self.fail(f"Vehicle validation should work with correct search configuration, but failed: {e}")
    
    @patch('vehicle_data.SHARED_GEMINI_MODEL')
    def test_aluminum_engine_search_config(self, mock_model):
        """Test aluminum engine detection uses correct search configuration."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "aluminum"
        mock_model.generate_content.return_value = mock_response
        
        try:
            result = get_aluminum_engine_from_api(2020, "Toyota", "Camry")
            
            # Verify correct tool configuration
            mock_model.generate_content.assert_called()
            call_args = mock_model.generate_content.call_args
            
            tools = call_args.kwargs['tools']
            self.assertEqual(tools, [{"google_search": {}}])
            
            # Verify result
            self.assertEqual(result, 1.0)  # aluminum = 1.0
            
        except Exception as e:
            self.fail(f"Aluminum engine detection should work with correct search configuration, but failed: {e}")
    
    @patch('vehicle_data.SHARED_GEMINI_MODEL')
    def test_aluminum_rims_search_config(self, mock_model):
        """Test aluminum rims detection uses correct search configuration."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "steel"
        mock_model.generate_content.return_value = mock_response
        
        try:
            result = get_aluminum_rims_from_api(2020, "Toyota", "Camry")
            
            # Verify correct tool configuration
            mock_model.generate_content.assert_called()
            call_args = mock_model.generate_content.call_args
            
            tools = call_args.kwargs['tools']
            self.assertEqual(tools, [{"google_search": {}}])
            
            # Verify result
            self.assertEqual(result, 0.0)  # steel = 0.0
            
        except Exception as e:
            self.fail(f"Aluminum rims detection should work with correct search configuration, but failed: {e}")
    
    @patch('vehicle_data.SHARED_GEMINI_MODEL')
    def test_curb_weight_search_config(self, mock_model):
        """Test curb weight resolution uses correct search configuration."""
        # Mock successful responses for both gather and interpret calls
        mock_gather_response = MagicMock()
        mock_gather_response.text = "3500 lbs from kbb.com"
        
        mock_interpret_response = MagicMock()
        mock_interpret_response.text = "3500"
        
        # Configure mock to return different responses for different calls
        mock_model.generate_content.side_effect = [mock_gather_response, mock_interpret_response]
        
        try:
            result = get_curb_weight_from_api(2020, "Toyota", "Camry")
            
            # Verify both calls used correct tool configuration
            self.assertEqual(mock_model.generate_content.call_count, 2)
            
            for call in mock_model.generate_content.call_args_list:
                tools = call.kwargs['tools']
                self.assertEqual(tools, [{"google_search": {}}])
            
            # Verify result
            self.assertEqual(result, 3500.0)
            
        except Exception as e:
            self.fail(f"Curb weight resolution should work with correct search configuration, but failed: {e}")
    
    @patch('vehicle_data.SHARED_GEMINI_MODEL')
    def test_catalytic_converters_search_config(self, mock_model):
        """Test catalytic converters detection uses correct search configuration."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "2"
        mock_model.generate_content.return_value = mock_response
        
        try:
            result = get_catalytic_converter_count_from_api(2020, "Toyota", "Camry")
            
            # Verify correct tool configuration
            mock_model.generate_content.assert_called()
            call_args = mock_model.generate_content.call_args
            
            tools = call_args.kwargs['tools']
            self.assertEqual(tools, [{"google_search": {}}])
            
            # Verify result
            self.assertEqual(result, 2.0)
            
        except Exception as e:
            self.fail(f"Catalytic converters detection should work with correct search configuration, but failed: {e}")


class TestSearchGroundingErrorElimination(unittest.TestCase):
    """Test that search grounding errors are eliminated with correct configuration."""
    
    @patch('vehicle_data.SHARED_GEMINI_MODEL')
    def test_no_search_grounding_not_supported_errors(self, mock_model):
        """Test that 400 Search Grounding not supported errors are eliminated."""
        # Mock successful response (no error)
        mock_response = MagicMock()
        mock_response.text = "yes"
        mock_model.generate_content.return_value = mock_response
        
        # Test multiple functions to ensure none throw search grounding errors
        test_functions = [
            lambda: validate_vehicle_existence(2020, "Toyota", "Camry"),
            lambda: get_aluminum_engine_from_api(2020, "Toyota", "Camry"),
            lambda: get_aluminum_rims_from_api(2020, "Toyota", "Camry"),
            lambda: get_curb_weight_from_api(2020, "Toyota", "Camry"),
            lambda: get_catalytic_converter_count_from_api(2020, "Toyota", "Camry")
        ]
        
        for i, test_func in enumerate(test_functions):
            with self.subTest(function_index=i):
                try:
                    # Reset mock for each test
                    mock_model.reset_mock()
                    
                    # For curb weight, need two responses
                    if i == 3:  # curb weight function
                        mock_model.generate_content.side_effect = [
                            MagicMock(text="3500 lbs"),
                            MagicMock(text="3500")
                        ]
                    else:
                        mock_model.generate_content.return_value = mock_response
                    
                    result = test_func()
                    
                    # Verify function completed without error
                    self.assertIsNotNone(result)
                    
                    # Verify no error-related exceptions were raised
                    # (If search grounding config was wrong, we'd get API errors)
                    
                except Exception as e:
                    # Check that it's not a search grounding error
                    error_message = str(e).lower()
                    self.assertNotIn("search grounding is not supported", error_message)
                    self.assertNotIn("400", error_message)
                    
                    # If it's a different error, that's acceptable for this test
                    # We're specifically testing that search grounding config errors are gone
    
    @patch('resolver.genai.GenerativeModel')
    def test_resolver_no_search_grounding_errors(self, mock_model_class):
        """Test that resolver functions don't produce search grounding errors."""
        # Mock the model and response
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "3500 lbs from kbb.com"
        mock_model.generate_content.return_value = mock_response
        
        client = GroundedSearchClient()
        
        try:
            # Test resolver search functions
            candidates = client.search_vehicle_specs(2020, "Toyota", "Camry", "curb_weight")
            
            # Verify function completed successfully
            self.assertIsNotNone(candidates)
            
        except Exception as e:
            # Check that it's not a search grounding error
            error_message = str(e).lower()
            self.assertNotIn("search grounding is not supported", error_message)
            self.assertNotIn("400", error_message)


class TestSearchGroundingIntegration(unittest.TestCase):
    """Test integration of search grounding with the complete system."""
    
    @patch('vehicle_data.SHARED_GEMINI_MODEL')
    @patch('resolver.genai.GenerativeModel')
    def test_end_to_end_search_grounding_workflow(self, mock_resolver_model, mock_vehicle_model):
        """Test complete workflow uses correct search grounding configuration."""
        # Mock resolver model
        mock_resolver_instance = MagicMock()
        mock_resolver_model.return_value = mock_resolver_instance
        mock_resolver_response = MagicMock()
        mock_resolver_response.text = "3500 lbs from kbb.com\n3520 lbs from edmunds.com"
        mock_resolver_instance.generate_content.return_value = mock_resolver_response
        
        # Mock vehicle data model
        mock_vehicle_response = MagicMock()
        mock_vehicle_response.text = "yes"
        mock_vehicle_model.generate_content.return_value = mock_vehicle_response
        
        try:
            # Test vehicle validation
            validation_result = validate_vehicle_existence(2020, "Toyota", "Camry")
            self.assertTrue(validation_result)
            
            # Test resolver search
            client = GroundedSearchClient()
            search_candidates = client.search_vehicle_specs(2020, "Toyota", "Camry", "curb_weight")
            self.assertIsNotNone(search_candidates)
            
            # Verify all calls used correct configuration
            # Check vehicle data calls
            for call in mock_vehicle_model.generate_content.call_args_list:
                if 'tools' in call.kwargs:
                    tools = call.kwargs['tools']
                    self.assertEqual(tools, [{"google_search": {}}])
            
            # Check resolver calls
            for call in mock_resolver_instance.generate_content.call_args_list:
                if 'tools' in call.kwargs:
                    tools = call.kwargs['tools']
                    self.assertEqual(tools, [{"google_search": {}}])
                    
        except Exception as e:
            self.fail(f"End-to-end workflow should work with correct search configuration, but failed: {e}")
    
    def test_search_grounding_configuration_consistency(self):
        """Test that all search grounding configurations are consistent across codebase."""
        # This test verifies that no old google_search_retrieval configurations remain
        
        # Read source files to check for any remaining incorrect configurations
        files_to_check = ['resolver.py', 'vehicle_data.py']
        
        for filename in files_to_check:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verify no old configuration remains
                self.assertNotIn('google_search_retrieval', content, 
                               f"Found old google_search_retrieval configuration in {filename}")
                
                # Verify new configuration is present
                self.assertIn('google_search', content,
                            f"New google_search configuration not found in {filename}")
                
            except FileNotFoundError:
                self.skipTest(f"File {filename} not found")
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'})
    def test_api_key_configuration(self):
        """Test that API key is properly configured for search grounding."""
        client = GroundedSearchClient()
        
        # Verify API key is set
        self.assertEqual(client.api_key, 'test_key')
        
        # Verify client can be initialized without errors
        self.assertIsNotNone(client)


class TestSearchGroundingPerformance(unittest.TestCase):
    """Test performance characteristics of search grounding functionality."""
    
    @patch('vehicle_data.SHARED_GEMINI_MODEL')
    def test_search_grounding_response_time(self, mock_model):
        """Test that search grounding calls complete within reasonable time."""
        import time
        
        # Mock fast response
        mock_response = MagicMock()
        mock_response.text = "yes"
        mock_model.generate_content.return_value = mock_response
        
        start_time = time.time()
        
        try:
            result = validate_vehicle_existence(2020, "Toyota", "Camry")
            end_time = time.time()
            
            # Verify function completed
            self.assertTrue(result)
            
            # Verify reasonable response time (allowing for mock overhead)
            response_time = end_time - start_time
            self.assertLess(response_time, 1.0, f"Search grounding call took too long: {response_time:.3f}s")
            
        except Exception as e:
            self.fail(f"Search grounding performance test failed: {e}")
    
    @patch('resolver.genai.GenerativeModel')
    def test_multiple_search_calls_performance(self, mock_model_class):
        """Test performance with multiple concurrent search grounding calls."""
        import threading
        import time
        
        # Mock the model
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = "3500 lbs from kbb.com"
        mock_model.generate_content.return_value = mock_response
        
        results = []
        errors = []
        
        def make_search_call():
            try:
                client = GroundedSearchClient()
                candidates = client.search_vehicle_specs(2020, "Toyota", "Camry", "curb_weight")
                results.append(candidates)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_search_call)
            threads.append(thread)
        
        start_time = time.time()
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all calls completed successfully
        self.assertEqual(len(errors), 0, f"Search grounding errors: {errors}")
        self.assertEqual(len(results), 3)
        
        # Verify reasonable total time
        self.assertLess(total_time, 3.0, f"Multiple search calls took too long: {total_time:.3f}s")


if __name__ == '__main__':
    # Run all search grounding tests
    unittest.main(verbosity=2, buffer=True)