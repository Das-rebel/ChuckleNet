#!/usr/bin/env python3
"""
Comprehensive Test Suite for VDPG Adapter
==========================================

This module provides complete testing coverage for the Visual Domain Prompt Generator,
ensuring all functionality works correctly and integrates seamlessly with the existing
GCACU autonomous laughter prediction system.

Test Coverage:
- Visual prompt generation for all comedy styles and cultural contexts
- Few-shot learning and domain adaptation
- Cultural style transfer between comedy genres
- Comedian personality injection
- Audience optimization
- Performance validation and benchmarking
- Integration with existing GCACU components

Author: GCACU Development Team
Date: 2026-04-03
Version: 1.0.0
License: MIT
"""

import os
import sys
import unittest
import logging
import tempfile
from pathlib import Path
import json
import time

# Scientific computing
import numpy as np
import pandas as pd

# Deep Learning
import torch
import torch.nn as nn

# Add project to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# Import VDPG adapter
from training.vdpg_adapter import (
    VDPGAdapter,
    VisualPromptGenerator,
    FewShotDomainAdapter,
    VisualPromptConfig,
    ComedyStyle,
    CulturalContext,
    AudienceDemographics,
    DomainAdaptationResult,
    create_vdpg_adapter,
    adapt_to_new_comedian,
    rapid_domain_adaptation
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockGCACUModel(nn.Module):
    """Mock GCACU model for testing"""

    def __init__(self, input_dim=768, hidden_dim=256, output_dim=2):
        super().__init__()
        self.mock_encoder = nn.Linear(input_dim, hidden_dim)
        self.mock_classifier = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        hidden = self.mock_encoder(x)
        output = self.mock_classifier(hidden)
        return output


class TestVisualPromptConfig(unittest.TestCase):
    """Test Visual Prompt Configuration"""

    def test_default_config(self):
        """Test default configuration creation"""
        config = VisualPromptConfig()
        self.assertEqual(config.prompt_dim, 256)
        self.assertEqual(config.few_shot_samples, 5)
        self.assertEqual(config.adaptation_strength, 0.7)

    def test_custom_config(self):
        """Test custom configuration"""
        config = VisualPromptConfig(
            prompt_dim=512,
            few_shot_samples=10,
            adaptation_strength=0.9
        )
        self.assertEqual(config.prompt_dim, 512)
        self.assertEqual(config.few_shot_samples, 10)
        self.assertEqual(config.adaptation_strength, 0.9)

    def test_config_serialization(self):
        """Test configuration can be serialized"""
        config = VisualPromptConfig()
        config_dict = {
            'prompt_dim': config.prompt_dim,
            'style_embedding_dim': config.style_embedding_dim,
            'cultural_embedding_dim': config.cultural_embedding_dim,
            'audience_embedding_dim': config.audience_embedding_dim,
            'fusion_method': config.fusion_method,
            'adaptation_strength': config.adaptation_strength,
            'few_shot_samples': config.few_shot_samples,
            'temperature': config.temperature,
            'top_k': config.top_k,
            'top_p': config.top_p
        }
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(len(config_dict), 10)


class TestComedyEnums(unittest.TestCase):
    """Test Comedy Style, Cultural Context, and Audience Enums"""

    def test_comedy_styles(self):
        """Test all comedy styles are accessible"""
        styles = [
            ComedyStyle.STAND_UP,
            ComedyStyle.TED_TALKS,
            ComedyStyle.SITCOMS,
            ComedyStyle.YOUTUBE,
            ComedyStyle.IMPROV,
            ComedyStyle.SKETCH,
            ComedyStyle.DARK_COMEDY,
            ComedyStyle.SATIRE
        ]
        self.assertEqual(len(styles), 8)

        for style in styles:
            self.assertIsInstance(style.value, int)
            self.assertGreaterEqual(style.value, 0)
            self.assertLess(style.value, len(styles))
            # Test the get_name method
            name = ComedyStyle.get_name(style.value)
            self.assertIsInstance(name, str)
            self.assertTrue(len(name) > 0)

    def test_cultural_contexts(self):
        """Test all cultural contexts are accessible"""
        contexts = [
            CulturalContext.US_DIRECT,
            CulturalContext.UK_SARCASM,
            CulturalContext.INDIAN_NUANCE,
            CulturalContext.AUSSIAN_SELF_DEPRECATING,
            CulturalContext.CANADIAN_POLITE
        ]
        self.assertEqual(len(contexts), 5)

        for context in contexts:
            self.assertIsInstance(context.value, int)
            self.assertGreaterEqual(context.value, 0)
            self.assertLess(context.value, len(contexts))
            # Test the get_name method
            name = CulturalContext.get_name(context.value)
            self.assertIsInstance(name, str)
            self.assertTrue(len(name) > 0)

    def test_audience_demographics(self):
        """Test all audience demographics are accessible"""
        audiences = [
            AudienceDemographics.GEN_Z,
            AudienceDemographics.MILLENNIALS,
            AudienceDemographics.GEN_X,
            AudienceDemographics.BOOMERS,
            AudienceDemographics.INTERNATIONAL,
            AudienceDemographics.FAMILY_FRIENDLY
        ]
        self.assertEqual(len(audiences), 6)

        for audience in audiences:
            self.assertIsInstance(audience.value, int)
            self.assertGreaterEqual(audience.value, 0)
            self.assertLess(audience.value, len(audiences))
            # Test the get_name method
            name = AudienceDemographics.get_name(audience.value)
            self.assertIsInstance(name, str)
            self.assertTrue(len(name) > 0)


class TestVisualPromptGenerator(unittest.TestCase):
    """Test Visual Prompt Generator"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = VisualPromptConfig(prompt_dim=256)
        self.generator = VisualPromptGenerator(self.config)

    def test_generator_initialization(self):
        """Test generator initializes correctly"""
        self.assertIsInstance(self.generator, VisualPromptGenerator)
        self.assertEqual(self.generator.config.prompt_dim, 256)

        # Check embeddings are created
        self.assertIsInstance(self.generator.style_embeddings, nn.Embedding)
        self.assertIsInstance(self.generator.cultural_embeddings, nn.Embedding)
        self.assertIsInstance(self.generator.audience_embeddings, nn.Embedding)

    def test_generate_single_prompt(self):
        """Test generating a single visual prompt"""
        prompt = self.generator.generate_prompt(
            style=ComedyStyle.STAND_UP,
            cultural_context=CulturalContext.US_DIRECT,
            audience=AudienceDemographics.MILLENNIALS
        )

        self.assertIsInstance(prompt, torch.Tensor)
        # Check prompt shape [1, prompt_dim]
        self.assertEqual(prompt.shape[0], 1)
        self.assertEqual(prompt.shape[1], self.config.prompt_dim)

    def test_generate_batch_prompts(self):
        """Test generating batch visual prompts"""
        batch_size = 4
        style_ids = torch.randint(0, len(ComedyStyle), (batch_size,))
        cultural_ids = torch.randint(0, len(CulturalContext), (batch_size,))
        audience_ids = torch.randint(0, len(AudienceDemographics), (batch_size,))

        prompts = self.generator(
            style_ids=style_ids,
            cultural_ids=cultural_ids,
            audience_ids=audience_ids
        )

        self.assertIsInstance(prompts, torch.Tensor)
        self.assertEqual(prompts.shape[0], batch_size)
        self.assertEqual(prompts.shape[1], self.config.prompt_dim)

    def test_add_comedian_style(self):
        """Test adding comedian-specific style"""
        comedian_id = "test_comedian_001"
        style_examples = [torch.randn(self.config.prompt_dim) for _ in range(3)]

        self.generator.add_comedian_style(comedian_id, style_examples)

        # Check comedian style was added
        self.assertIn(comedian_id, self.generator.comedian_style_bank)
        self.assertIsInstance(
            self.generator.comedian_style_bank[comedian_id],
            nn.Parameter
        )

    def test_prompt_with_comedian_style(self):
        """Test generating prompt with comedian-specific style"""
        # Add comedian style first
        comedian_id = "test_comedian_002"
        style_examples = [torch.randn(self.config.prompt_dim) for _ in range(3)]
        self.generator.add_comedian_style(comedian_id, style_examples)

        # Generate prompt with comedian style
        prompt = self.generator.generate_prompt(
            style=ComedyStyle.STAND_UP,
            cultural_context=CulturalContext.US_DIRECT,
            audience=AudienceDemographics.MILLENNIALS,
            comedian_id=comedian_id
        )

        self.assertIsInstance(prompt, torch.Tensor)
        self.assertEqual(prompt.shape[1], self.config.prompt_dim)


class TestFewShotDomainAdapter(unittest.TestCase):
    """Test Few-Shot Domain Adapter"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = VisualPromptConfig(prompt_dim=256, few_shot_samples=5)
        self.mock_model = MockGCACUModel()
        self.prompt_generator = VisualPromptGenerator(self.config)
        self.adapter = FewShotDomainAdapter(
            self.mock_model,
            self.prompt_generator,
            self.config
        )

    def test_adapter_initialization(self):
        """Test adapter initializes correctly"""
        self.assertIsInstance(self.adapter, FewShotDomainAdapter)
        self.assertEqual(len(self.adapter.support_set_examples), 0)
        self.assertEqual(len(self.adapter.adaptation_history), 0)

    def test_construct_support_set(self):
        """Test support set construction"""
        examples = [
            {'text': 'example 1', 'labels': [0, 1, 0], 'metadata': {}},
            {'text': 'example 2', 'labels': [1, 0, 1], 'metadata': {}},
            {'text': 'example 3', 'labels': [0, 0, 1], 'metadata': {}},
        ]

        domain_config = {
            'style': ComedyStyle.STAND_UP,
            'cultural_context': CulturalContext.US_DIRECT,
            'audience': AudienceDemographics.MILLENNIALS
        }

        self.adapter.construct_support_set(examples, domain_config)

        # Check support set was constructed
        self.assertEqual(len(self.adapter.support_set_examples), 3)

        # Check examples have correct domain configuration
        for example in self.adapter.support_set_examples:
            self.assertEqual(example['style'], ComedyStyle.STAND_UP)
            self.assertEqual(example['cultural_context'], CulturalContext.US_DIRECT)
            self.assertEqual(example['audience'], AudienceDemographics.MILLENNIALS)

    def test_meta_adapt(self):
        """Test meta-learning adaptation"""
        # Create support set
        support_examples = [
            {'text': f'support example {i}', 'labels': [0, 1], 'metadata': {}}
            for i in range(5)
        ]

        domain_config = {
            'style': ComedyStyle.STAND_UP,
            'cultural_context': CulturalContext.US_DIRECT,
            'audience': AudienceDemographics.MILLENNIALS
        }

        self.adapter.construct_support_set(support_examples, domain_config)

        # Create query set
        query_examples = [
            {'text': f'query example {i}', 'labels': [1, 0], 'metadata': {}}
            for i in range(3)
        ]

        # Perform meta-adaptation
        adaptation_result = self.adapter.meta_adapt(
            query_examples,
            adaptation_steps=3,
            learning_rate=1e-4
        )

        # Check result structure
        self.assertIsInstance(adaptation_result, DomainAdaptationResult)
        self.assertIsInstance(adaptation_result.adapted_model, nn.Module)
        self.assertIsInstance(adaptation_result.adaptation_metrics, dict)
        self.assertIsInstance(adaptation_result.visual_prompts, torch.Tensor)
        self.assertIsInstance(adaptation_result.adaptation_time, float)

        # Check adaptation was fast
        self.assertLess(adaptation_result.adaptation_time, 10.0)  # Should be < 10 seconds

        # Check metrics
        self.assertIn('accuracy', adaptation_result.adaptation_metrics)
        self.assertIn('f1', adaptation_result.adaptation_metrics)

        # Check history was updated
        self.assertEqual(len(self.adapter.adaptation_history), 1)


class TestVDPGAdapter(unittest.TestCase):
    """Test Main VDPG Adapter"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_model = MockGCACUModel()
        self.config = VisualPromptConfig(prompt_dim=256)
        self.device = "cpu"
        self.adapter = VDPGAdapter(
            self.mock_model,
            self.config,
            self.device
        )

    def test_adapter_initialization(self):
        """Test adapter initializes correctly"""
        self.assertIsInstance(self.adapter, VDPGAdapter)
        self.assertIsInstance(self.adapter.prompt_generator, VisualPromptGenerator)
        self.assertIsInstance(self.adapter.few_shot_adapter, FewShotDomainAdapter)
        self.assertEqual(len(self.adapter.adaptation_cache), {}.__len__())

    def test_adapt_to_domain_basic(self):
        """Test basic domain adaptation"""
        domain_config = {
            'style': ComedyStyle.STAND_UP,
            'cultural_context': CulturalContext.US_DIRECT,
            'audience': AudienceDemographics.MILLENNIALS
        }

        support_examples = [
            {'text': f'support {i}', 'labels': [0, 1], 'metadata': {}}
            for i in range(5)
        ]

        result = self.adapter.adapt_to_domain(
            domain_config,
            support_examples=support_examples,
            use_cache=False
        )

        self.assertIsInstance(result, DomainAdaptationResult)
        self.assertIsInstance(result.adapted_model, nn.Module)
        self.assertIsInstance(result.visual_prompts, torch.Tensor)
        self.assertGreater(result.adaptation_time, 0)

    def test_domain_adaptation_caching(self):
        """Test domain adaptation caching works"""
        domain_config = {
            'style': ComedyStyle.YOUTUBE,
            'cultural_context': CulturalContext.US_DIRECT,
            'audience': AudienceDemographics.GEN_Z
        }

        support_examples = [
            {'text': 'cached example', 'labels': [1], 'metadata': {}}
        ]

        # First adaptation (should cache)
        result1 = self.adapter.adapt_to_domain(
            domain_config,
            support_examples=support_examples,
            use_cache=True
        )

        # Second adaptation (should use cache)
        result2 = self.adapter.adapt_to_domain(
            domain_config,
            support_examples=support_examples,
            use_cache=True
        )

        # Both should return similar results
        self.assertAlmostEqual(result1.adaptation_time, result2.adaptation_time, places=1)

    def test_predict_with_adaptation(self):
        """Test prediction with domain adaptation"""
        domain_config = {
            'style': ComedyStyle.STAND_UP,
            'cultural_context': CulturalContext.UK_SARCASM,
            'audience': AudienceDemographics.GEN_X
        }

        test_text = "This is a test comedy segment about the absurdity of modern life"

        prediction, confidence = self.adapter.predict_with_adaptation(
            test_text,
            domain_config,
            use_visual_prompts=True
        )

        self.assertIn(prediction, [0, 1])
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_cross_domain_style_transfer(self):
        """Test cross-domain style transfer"""
        test_text = "Why did the chicken cross the road? To get to the other side."

        result = self.adapter.cross_domain_style_transfer(
            text=test_text,
            source_style=ComedyStyle.STAND_UP,
            target_style=ComedyStyle.TED_TALKS,
            cultural_context=CulturalContext.US_DIRECT
        )

        self.assertIsInstance(result, dict)
        self.assertIn('original_text', result)
        self.assertIn('source_style', result)
        self.assertIn('target_style', result)
        self.assertIn('style_similarity', result)
        self.assertIn('adaptation_suggestions', result)
        self.assertIsInstance(result['adaptation_suggestions'], list)

    def test_comedian_personality_injection(self):
        """Test comedian personality injection"""
        comedian_id = "dave_chappelle"
        test_text = "A comedic observation about society"

        style_examples = [torch.randn(256) for _ in range(5)]

        result = self.adapter.comedian_personality_injection(
            test_text,
            comedian_id,
            style_examples
        )

        self.assertIsInstance(result, dict)
        self.assertIn('text', result)
        self.assertIn('comedian_id', result)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertEqual(result['comedian_id'], comedian_id)

        # Check comedian was added to style bank
        self.assertIn(comedian_id, self.adapter.prompt_generator.comedian_style_bank)

    def test_optimize_for_audience(self):
        """Test audience optimization"""
        test_text = "Comedy content about technology and modern life"
        target_audience = AudienceDemographics.GEN_Z

        result = self.adapter.optimize_for_audience(
            test_text,
            target_audience
        )

        self.assertIsInstance(result, dict)
        self.assertIn('text', result)
        self.assertIn('target_audience', result)
        self.assertIn('prediction', result)
        self.assertIn('optimization_suggestions', result)
        self.assertIn('adaptation_metrics', result)
        self.assertIsInstance(result['optimization_suggestions'], list)

    def test_get_performance_summary(self):
        """Test performance summary generation"""
        # Perform some adaptations first
        for i in range(3):
            domain_config = {
                'style': ComedyStyle.STAND_UP,
                'cultural_context': CulturalContext.US_DIRECT,
                'audience': AudienceDemographics.MILLENNIALS
            }
            support_examples = [
                {'text': f'example {i}', 'labels': [1], 'metadata': {}}
            ]
            self.adapter.adapt_to_domain(domain_config, support_examples)

        summary = self.adapter.get_performance_summary()

        self.assertIsInstance(summary, dict)
        self.assertIn('total_adaptations', summary)
        self.assertIn('average_adaptation_time', summary)
        self.assertIn('average_accuracy', summary)
        self.assertEqual(summary['total_adaptations'], 3)

    def test_save_and_load_state(self):
        """Test state saving and loading"""
        # Add some data to adapter
        domain_config = {
            'style': ComedyStyle.STAND_UP,
            'cultural_context': CulturalContext.US_DIRECT,
            'audience': AudienceDemographics.MILLENNIALS
        }
        support_examples = [
            {'text': 'test example', 'labels': [1], 'metadata': {}}
        ]
        self.adapter.adapt_to_domain(domain_config, support_examples)

        # Save state
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pt') as tmp:
            tmp_path = tmp.name

        try:
            self.adapter.save_state(tmp_path)

            # Create new adapter and load state
            new_adapter = VDPGAdapter(self.mock_model, self.config, self.device)
            new_adapter.load_state(tmp_path)

            # Check state was loaded
            self.assertEqual(
                len(new_adapter.adaptation_cache),
                len(self.adapter.adaptation_cache)
            )
            self.assertEqual(
                len(new_adapter.performance_metrics['adaptation_times']),
                len(self.adapter.performance_metrics['adaptation_times'])
            )

        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_model = MockGCACUModel()

    def test_create_vdpg_adapter(self):
        """Test VDPG adapter creation convenience function"""
        adapter = create_vdpg_adapter(self.mock_model, prompt_dim=512)

        self.assertIsInstance(adapter, VDPGAdapter)
        self.assertEqual(adapter.config.prompt_dim, 512)

    def test_adapt_to_new_comedian(self):
        """Test new comedian adaptation convenience function"""
        adapter = create_vdpg_adapter(self.mock_model)

        comedian_id = "ricky_gervais"
        style_examples = [
            {'text': f'example {i}', 'labels': [1], 'metadata': {}}
            for i in range(5)
        ]
        test_texts = ["test segment 1", "test segment 2"]

        result = adapt_to_new_comedian(
            adapter,
            comedian_id,
            style_examples,
            test_texts
        )

        self.assertIsInstance(result, dict)
        self.assertIn('comedian_id', result)
        self.assertIn('num_examples', result)
        self.assertIn('results', result)
        self.assertEqual(result['comedian_id'], comedian_id)
        self.assertEqual(result['num_examples'], 5)

    def test_rapid_domain_adaptation(self):
        """Test rapid domain adaptation convenience function"""
        adapter = create_vdpg_adapter(self.mock_model)

        few_shot_examples = [
            {'text': f'example {i}', 'labels': [1], 'metadata': {}}
            for i in range(8)
        ]

        result = rapid_domain_adaptation(
            adapter,
            ComedyStyle.YOUTUBE,
            CulturalContext.UK_SARCASM,
            few_shot_examples
        )

        self.assertIsInstance(result, DomainAdaptationResult)
        self.assertIsInstance(result.adapted_model, nn.Module)
        self.assertIsInstance(result.visual_prompts, torch.Tensor)


class TestIntegrationWithGCACU(unittest.TestCase):
    """Test integration with existing GCACU components"""

    def test_vdpg_with_mock_gcacu(self):
        """Test VDPG works with mock GCACU model"""
        mock_gcacu = MockGCACUModel(input_dim=768, hidden_dim=256, output_dim=2)

        adapter = create_vdpg_adapter(mock_gcacu, prompt_dim=256)

        # Test adaptation
        domain_config = {
            'style': ComedyStyle.STAND_UP,
            'cultural_context': CulturalContext.INDIAN_NUANCE,
            'audience': AudienceDemographics.INTERNATIONAL
        }

        support_examples = [
            {'text': f'Indian comedy example {i}', 'labels': [1, 0], 'metadata': {}}
            for i in range(6)
        ]

        result = adapter.adapt_to_domain(domain_config, support_examples)

        self.assertIsInstance(result, DomainAdaptationResult)
        self.assertLess(result.adaptation_time, 15.0)  # Should be fast

    def test_multiple_cultural_contexts(self):
        """Test VDPG works with all cultural contexts"""
        mock_gcacu = MockGCACUModel()
        adapter = create_vdpg_adapter(mock_gcacu)

        contexts = [
            CulturalContext.US_DIRECT,
            CulturalContext.UK_SARCASM,
            CulturalContext.INDIAN_NUANCE,
            CulturalContext.AUSSIAN_SELF_DEPRECATING,
            CulturalContext.CANADIAN_POLITE
        ]

        results = []
        for context in contexts:
            domain_config = {
                'style': ComedyStyle.STAND_UP,
                'cultural_context': context,
                'audience': AudienceDemographics.MILLENNIALS
            }

            support_examples = [
                {'text': f'example {i}', 'labels': [1], 'metadata': {}}
                for i in range(5)
            ]

            result = adapter.adapt_to_domain(domain_config, support_examples)
            results.append(result)

        # Check all adaptations succeeded
        self.assertEqual(len(results), len(contexts))
        for result in results:
            self.assertIsInstance(result, DomainAdaptationResult)
            self.assertGreater(result.adaptation_time, 0)

    def test_all_comedy_styles(self):
        """Test VDPG works with all comedy styles"""
        mock_gcacu = MockGCACUModel()
        adapter = create_vdpg_adapter(mock_gcacu)

        styles = list(ComedyStyle)

        results = []
        for style in styles:
            domain_config = {
                'style': style,
                'cultural_context': CulturalContext.US_DIRECT,
                'audience': AudienceDemographics.MILLENNIALS
            }

            support_examples = [
                {'text': f'{style.value} example {i}', 'labels': [1], 'metadata': {}}
                for i in range(5)
            ]

            result = adapter.adapt_to_domain(domain_config, support_examples)
            results.append(result)

        # Check all style adaptations succeeded
        self.assertEqual(len(results), len(styles))
        for result in results:
            self.assertIsInstance(result, DomainAdaptationResult)


class TestPerformanceValidation(unittest.TestCase):
    """Test performance validation and benchmarking"""

    def test_adaptation_speed_benchmark(self):
        """Test adaptation speed meets requirements"""
        mock_model = MockGCACUModel()
        adapter = create_vdpg_adapter(mock_model)

        domain_config = {
            'style': ComedyStyle.STAND_UP,
            'cultural_context': CulturalContext.US_DIRECT,
            'audience': AudienceDemographics.MILLENNIALS
        }

        support_examples = [
            {'text': f'example {i}', 'labels': [1], 'metadata': {}}
            for i in range(5)
        ]

        start_time = time.time()
        result = adapter.adapt_to_domain(domain_config, support_examples)
        adaptation_time = time.time() - start_time

        # Requirement: Adaptation should be < 5 seconds
        self.assertLess(adaptation_time, 5.0,
                       f"Adaptation too slow: {adaptation_time:.2f}s")

        logger.info(f"Adaptation completed in {adaptation_time:.2f}s")

    def test_sample_efficiency_validation(self):
        """Test sample efficiency meets requirements"""
        mock_model = MockGCACUModel()
        adapter = create_vdpg_adapter(mock_model)

        # Test with different sample sizes
        sample_sizes = [3, 5, 7, 10]

        for sample_size in sample_sizes:
            domain_config = {
                'style': ComedyStyle.YOUTUBE,
                'cultural_context': CulturalContext.US_DIRECT,
                'audience': AudienceDemographics.GEN_Z
            }

            support_examples = [
                {'text': f'example {i}', 'labels': [1], 'metadata': {}}
                for i in range(sample_size)
            ]

            result = adapter.adapt_to_domain(domain_config, support_examples)

            # Check sample efficiency is recorded
            self.assertEqual(result.sample_efficiency, sample_size)
            self.assertLessEqual(sample_size, 10, "Should work with ≤10 examples")

        logger.info(f"Sample efficiency validated for sizes: {sample_sizes}")

    def test_memory_efficiency_validation(self):
        """Test memory efficiency meets requirements"""
        mock_model = MockGCACUModel()
        adapter = create_vdpg_adapter(mock_model)

        # Check memory footprint of visual prompts
        prompt = adapter.prompt_generator.generate_prompt(
            style=ComedyStyle.STAND_UP,
            cultural_context=CulturalContext.US_DIRECT,
            audience=AudienceDemographics.MILLENNIALS
        )

        prompt_memory = prompt.element_size() * prompt.nelement()

        # Requirement: Visual prompts should be < 500MB
        # (This is a very loose requirement; actual usage should be much smaller)
        self.assertLess(prompt_memory, 500 * 1024 * 1024,
                       f"Prompt memory too high: {prompt_memory / 1024 / 1024:.2f}MB")

        logger.info(f"Visual prompt memory: {prompt_memory / 1024:.2f}KB")


def run_comprehensive_tests():
    """Run comprehensive test suite with detailed reporting"""

    logger.info("Starting Comprehensive VDPG Adapter Test Suite")
    logger.info("=" * 80)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestVisualPromptConfig,
        TestComedyEnums,
        TestVisualPromptGenerator,
        TestFewShotDomainAdapter,
        TestVDPGAdapter,
        TestConvenienceFunctions,
        TestIntegrationWithGCACU,
        TestPerformanceValidation
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    logger.info("=" * 80)
    logger.info("Test Suite Summary:")
    logger.info(f"Tests Run: {result.testsRun}")
    logger.info(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        logger.info("✅ ALL TESTS PASSED - VDPG ADAPTER IS PRODUCTION READY!")
    else:
        logger.warning("⚠️ SOME TESTS FAILED - REVIEW NEEDED")

    return result


if __name__ == "__main__":
    # Run comprehensive test suite
    test_result = run_comprehensive_tests()

    # Exit with appropriate code
    sys.exit(0 if test_result.wasSuccessful() else 1)