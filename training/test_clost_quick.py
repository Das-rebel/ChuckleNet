"""
Quick CLoST Framework Test
Essential functionality testing for CLoST components
"""

import torch
import numpy as np
import sys
import time

# Test individual components with minimal dependencies
def test_clost_core():
    """Test core CLoST functionality"""
    print("🧪 Testing CLoST Core Components")

    try:
        # Test 1: Import core components
        print("📦 Testing imports...")
        from clost_reasoning import (
            CLoSTReasoningFramework,
            ComedyKnowledgeGraph,
            ComedyConcept
        )
        print("   ✅ Core imports successful")

        # Test 2: Create knowledge graph
        print("🕸️ Testing knowledge graph creation...")
        kg = ComedyKnowledgeGraph(embedding_dim=768)

        # Add test concepts
        concept1 = ComedyConcept(
            id="setup",
            name="Setup Concept",
            category="setup",
            embedding=torch.randn(768),
            properties={},
            relationships={}
        )
        concept2 = ComedyConcept(
            id="punchline",
            name="Punchline Concept",
            category="punchline",
            embedding=torch.randn(768),
            properties={},
            relationships={}
        )

        kg.add_concept(concept1)
        kg.add_concept(concept2)
        kg.add_relationship("setup", "punchline", "subverts", 0.8)

        print(f"   ✅ Knowledge graph: {len(kg.concepts)} concepts, {kg.graph.number_of_edges()} edges")

        # Test 3: Test causal inference
        print("🔍 Testing causal inference...")
        clost = CLoSTReasoningFramework(embedding_dim=768)

        setup_emb = torch.randn(32, 768)
        punchline_emb = torch.randn(32, 768)

        causal_strength = clost.causal_engine.detect_causal_relationships(
            setup_emb.mean(dim=0).unsqueeze(0),
            punchline_emb.mean(dim=0).unsqueeze(0)
        )

        print(f"   ✅ Causal strength: {causal_strength.item():.4f}")

        # Test 4: Test thought leap detection
        print("🎯 Testing thought leap detection...")
        thought_leap = clost.leap_detector.quantify_leap(
            setup_emb.mean(dim=0),
            punchline_emb.mean(dim=0)
        )

        print(f"   ✅ Leap score: {thought_leap.leap_score:.4f}")
        print(f"   ✅ Semantic distance: {thought_leap.semantic_distance:.4f}")
        print(f"   ✅ Humor mechanism: {thought_leap.humor_mechanism}")

        # Test 5: Test complete analysis
        print("📊 Testing complete CLoST analysis...")
        analysis = clost.analyze_setup_punchline(setup_emb, punchline_emb)

        print(f"   ✅ Humor strength: {analysis['humor_strength']}")
        print(f"   ✅ Reasoning paths: {len(analysis['reasoning_paths'])}")

        print("\n✅ All core CLoST tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ CLoST test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """Test performance metrics"""
    print("\n⚡ Testing Performance Metrics")

    try:
        from clost_reasoning import CLoSTReasoningFramework

        # Create CLoST framework
        clost = CLoSTReasoningFramework(embedding_dim=768)

        # Test inference speed
        print("🔄 Testing inference speed...")
        embeddings = torch.randn(64, 768)

        times = []
        for i in range(5):
            start = time.time()
            analysis = clost.analyze_setup_punchline(
                embeddings[:32],
                embeddings[32:]
            )
            end = time.time()
            times.append((end - start) * 1000)  # Convert to ms

        avg_time = np.mean(times)
        print(f"   ✅ Average inference time: {avg_time:.2f}ms")

        # Check if meets target (<50ms)
        if avg_time < 50:
            print(f"   ✅ Meets speed target (<50ms)")
        else:
            print(f"   ⚠️  Above speed target (target: <50ms)")

        # Test memory usage
        print("💾 Testing memory usage...")
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / (1024 ** 2)

        print(f"   ✅ Memory usage: {memory_mb:.2f}MB")

        # Check if meets target (<500MB)
        if memory_mb < 500:
            print(f"   ✅ Meets memory target (<500MB)")
        else:
            print(f"   ⚠️  Above memory target (target: <500MB)")

        return True

    except Exception as e:
        print(f"\n❌ Performance test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_base():
    """Test knowledge base functionality"""
    print("\n📚 Testing Knowledge Base")

    try:
        from clost_knowledge_base import ComedyKnowledgeBase

        # Create knowledge base
        kb = ComedyKnowledgeBase(embedding_dim=768)

        print(f"   ✅ Total patterns: {len(kb.patterns)}")
        print(f"   ✅ Causal templates: {len(kb.causal_templates)}")
        print(f"   ✅ Semantic clusters: {len(kb.semantic_clusters)}")

        # Test pattern categories
        categories = set(p.category for p in kb.patterns.values())
        print(f"   ✅ Pattern categories: {len(categories)}")

        # Test specific patterns
        incongruity_patterns = kb.get_patterns_by_category("incongruity")
        print(f"   ✅ Incongruity patterns: {len(incongruity_patterns)}")

        if incongruity_patterns:
            pattern = incongruity_patterns[0]
            print(f"   ✅ Sample pattern: {pattern.name}")
            print(f"      Examples: {len(pattern.examples)}")

        return True

    except Exception as e:
        print(f"\n❌ Knowledge base test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all quick tests"""
    print("🚀 Starting Quick CLoST Framework Tests")
    print("="*60)

    results = []

    # Run tests
    results.append(("Core Components", test_clost_core()))
    results.append(("Performance", test_performance()))
    results.append(("Knowledge Base", test_knowledge_base()))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)