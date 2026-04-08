#!/usr/bin/env python3
"""
GCACU Architecture Integration Test

Quick verification that the new GCACU language adapter and UPL loss
functions work correctly with the existing pipeline.
"""

import sys
import torch
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from training.xlmr_standup_word_level import (
    GCACULanguageAwareAdapter,
    compute_upl_weighted_loss,
    infer_language_domain_bucket,
    LANGUAGE_DOMAIN_BUCKETS,
    XLMRStandupConfig
)
from transformers import AutoModelForTokenClassification

def test_gcacu_adapter():
    """Test GCACU adapter initialization and forward pass"""
    print("🧪 Testing GCACU Language Adapter...")

    # Create a simple base model
    base_model = AutoModelForTokenClassification.from_pretrained(
        "FacebookAI/xlm-roberta-base",
        num_labels=2
    )

    # Initialize GCACU adapter
    gcacu_adapter = GCACULanguageAwareAdapter(
        backbone=base_model,
        language_dim=128,
        language_scale=0.5,
        incongruity_window=7,
        contrast_threshold=0.3
    )

    print(f"✅ GCACU adapter initialized successfully")
    print(f"   Language domains: {LANGUAGE_DOMAIN_BUCKETS}")
    print(f"   Adapter parameters: {sum(p.numel() for p in gcacu_adapter.parameters()):,}")

    # Test forward pass with dummy data
    batch_size, seq_len = 2, 16
    input_ids = torch.randint(0, 1000, (batch_size, seq_len))
    attention_mask = torch.ones(batch_size, seq_len)

    # Test with different language domains
    for domain_idx, domain in enumerate(LANGUAGE_DOMAIN_BUCKETS):
        language_domain_ids = torch.full((batch_size,), domain_idx, dtype=torch.long)

        outputs = gcacu_adapter(
            input_ids=input_ids,
            attention_mask=attention_mask,
            language_domain_ids=language_domain_ids
        )

        assert outputs.logits.shape == (batch_size, seq_len, 2), f"Unexpected logits shape for {domain}"
        print(f"✅ {domain} domain forward pass successful")

    return gcacu_adapter

def test_upl_loss():
    """Test UPL loss computation"""
    print("\n🧪 Testing UPL Loss Computation...")

    # Create dummy logits and labels
    batch_size, seq_len, num_labels = 2, 16, 2
    logits = torch.randn(batch_size, seq_len, num_labels)
    labels = torch.randint(0, 2, (batch_size, seq_len))

    # Mask some labels as padding (-100)
    labels[0, :4] = -100

    # Test UPL loss
    upl_loss = compute_upl_weighted_loss(
        logits=logits,
        labels=labels,
        positive_class_weight=4.0,
        loss_type="cross_entropy",
        focal_gamma=2.0,
        confidence_threshold=0.7,
        uncertainty_weight=0.5
    )

    assert not torch.isnan(upl_loss), "UPL loss is NaN!"
    assert not torch.isinf(upl_loss), "UPL loss is infinite!"
    print(f"✅ UPL loss computation successful: {upl_loss.item():.4f}")

    return upl_loss

def test_language_domain_inference():
    """Test language domain inference"""
    print("\n🧪 Testing Language Domain Inference...")

    test_cases = [
        ("en", "internal", "english"),
        ("fr", "internal", "multilingual"),
        ("es", "internal", "multilingual"),
        ("cs", "internal", "multilingual"),
        ("en", "standup4ai", "standup4ai"),
        ("de", "internal", "multilingual"),
        ("unknown", "internal", "cross_lingual"),
    ]

    for language, dataset_source, expected_domain in test_cases:
        inferred_domain = infer_language_domain_bucket(language, dataset_source)
        assert inferred_domain == expected_domain, f"Expected {expected_domain}, got {inferred_domain}"
        print(f"✅ {language}+{dataset_source} → {inferred_domain}")

def test_configuration_integration():
    """Test GCACU configuration options"""
    print("\n🧪 Testing Configuration Integration...")

    config = XLMRStandupConfig(
        gcacu_language_enabled=True,
        gcacu_language_dim=128,
        gcacu_language_scale=0.5,
        gcacu_incongruity_window=7,
        gcacu_contrast_threshold=0.3,
        uncertainty_aware_upl=True,
        upl_confidence_threshold=0.7,
        upl_uncertainty_weight=0.5
    )

    assert config.gcacu_language_enabled == True
    assert config.gcacu_language_dim == 128
    assert config.uncertainty_aware_upl == True
    print("✅ Configuration options integrated successfully")
    print(f"   GCACU enabled: {config.gcacu_language_enabled}")
    print(f"   UPL enabled: {config.uncertainty_aware_upl}")

def main():
    """Run all GCACU architecture tests"""
    print("🚀 Starting GCACU Architecture Integration Tests")
    print("=" * 50)

    try:
        # Test GCACU adapter
        gcacu_adapter = test_gcacu_adapter()

        # Test UPL loss
        upl_loss = test_upl_loss()

        # Test language domain inference
        test_language_domain_inference()

        # Test configuration integration
        test_configuration_integration()

        print("\n" + "=" * 50)
        print("🎉 All GCACU Architecture Tests Passed!")
        print("✅ GCACU adapter: Functional")
        print("✅ UPL loss: Functional")
        print("✅ Language domain inference: Accurate")
        print("✅ Configuration system: Integrated")
        print("\n🚀 Ready for StandUp4AI integration and testing!")

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())