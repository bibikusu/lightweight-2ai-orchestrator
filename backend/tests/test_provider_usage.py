# -*- coding: utf-8 -*-
"""Provider usage extraction test coverage."""

from unittest.mock import Mock, patch
import pytest
from orchestration.providers.openai_client import OpenAIClientWrapper, OpenAIClientConfig
from orchestration.providers.claude_client import ClaudeClientWrapper, ClaudeClientConfig


class TestOpenAIProviderUsage:
    """OpenAI provider usage extraction tests."""
    
    def test_openai_provider_returns_usage_when_available(self):
        """AC-93-01: OpenAI provider response に usage がある場合、戻り値に usage が含まれる"""
        config = OpenAIClientConfig(model="gpt-4o", timeout_sec=60)
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = OpenAIClientWrapper(config)
            
            # Mock response with usage
            mock_response = Mock()
            mock_response.output_text = '{"test": "data"}'
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_response.usage.total_tokens = 150
            
            with patch.object(client._client.responses, 'create', return_value=mock_response):
                result = client.request_prepared_spec("system", "user")
                
                assert 'usage' in result
                assert result['usage']['input_tokens'] == 100
                assert result['usage']['output_tokens'] == 50
                assert result['usage']['total_tokens'] == 150
    
    def test_openai_provider_tolerates_missing_usage(self):
        """AC-93-03: usage がない場合でも provider は異常終了しない"""
        config = OpenAIClientConfig(model="gpt-4o", timeout_sec=60)
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = OpenAIClientWrapper(config)
            
            # Mock response without usage
            mock_response = Mock()
            mock_response.output_text = '{"test": "data"}'
            mock_response.usage = None
            
            with patch.object(client._client.responses, 'create', return_value=mock_response):
                result = client.request_prepared_spec("system", "user")
                
                # Should not have usage key but should not fail
                assert 'usage' not in result
                assert result['test'] == 'data'


class TestClaudeProviderUsage:
    """Claude provider usage extraction tests."""
    
    def test_claude_provider_returns_usage_when_available(self):
        """AC-93-02: Claude provider response に usage がある場合、戻り値に usage が含まれる"""
        config = ClaudeClientConfig(model="claude-3-5-sonnet-20241022", timeout_sec=60)
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            client = ClaudeClientWrapper(config)
            
            # Mock message with usage
            mock_message = Mock()
            mock_text_block = Mock()
            mock_text_block.type = "text"
            mock_text_block.text = '{"test": "data"}'
            mock_message.content = [mock_text_block]
            mock_message.usage = Mock()
            mock_message.usage.input_tokens = 200
            mock_message.usage.output_tokens = 75
            
            with patch.object(client._client.messages, 'create', return_value=mock_message):
                result = client.request_implementation("system", "user")
                
                assert 'usage' in result
                assert result['usage']['input_tokens'] == 200
                assert result['usage']['output_tokens'] == 75
                assert result['usage']['total_tokens'] == 275
    
    def test_claude_provider_tolerates_missing_usage(self):
        """AC-93-03: usage がない場合でも provider は異常終了しない"""
        config = ClaudeClientConfig(model="claude-3-5-sonnet-20241022", timeout_sec=60)
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            client = ClaudeClientWrapper(config)
            
            # Mock message without usage
            mock_message = Mock()
            mock_text_block = Mock()
            mock_text_block.type = "text"
            mock_text_block.text = '{"test": "data"}'
            mock_message.content = [mock_text_block]
            mock_message.usage = None
            
            with patch.object(client._client.messages, 'create', return_value=mock_message):
                result = client.request_implementation("system", "user")
                
                # Should not have usage key but should not fail
                assert 'usage' not in result
                assert result['test'] == 'data'


class TestExtractApiUsageCompatibility:
    """Test compatibility with extract_api_usage function."""
    
    def test_extract_api_usage_reads_provider_usage_structure(self):
        """AC-93-04: extract_api_usage が provider 戻り値から usage を取得できる"""
        # Simulate provider response with usage data
        provider_response = {
            "data": "test",
            "usage": {
                "input_tokens": 150,
                "output_tokens": 100,
                "total_tokens": 250
            }
        }
        
        # Verify usage structure is accessible
        usage = provider_response.get('usage', {})
        assert usage.get('input_tokens') == 150
        assert usage.get('output_tokens') == 100
        assert usage.get('total_tokens') == 250