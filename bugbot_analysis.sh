#!/bin/bash

# Bugbot Analysis Script for Quantum-Claw
# Comprehensive codebase quality assurance and vulnerability scanning

set -e  # Exit on error

echo "🔍 Starting Bugbot Analysis for Quantum-Claw..."
echo "=================================================="

# Create reports directory
mkdir -p reports

# 1. Clippy Analysis (Rust Linting)
echo "📋 Running Clippy Analysis..."
if cargo clippy --all-targets --all-features -- -D warnings > reports/clippy_report.txt 2>&1; then
    echo "✅ Clippy: No warnings found"
    CLIPPY_STATUS="PASS"
else
    echo "❌ Clippy: Warnings or errors found"
    CLIPPY_STATUS="FAIL"
fi

# 2. Security Audit
echo "🔒 Running Security Audit..."
if cargo audit > reports/security_audit.txt 2>&1; then
    echo "✅ Security Audit: No vulnerabilities found"
    SECURITY_STATUS="PASS"
else
    echo "⚠️  Security Audit: Vulnerabilities found (check report)"
    SECURITY_STATUS="WARN"
fi

# 3. Dependency Analysis
echo "📦 Running Dependency Analysis..."
if command -v cargo-outdated &> /dev/null; then
    cargo outdated > reports/dependency_report.txt 2>&1 || true
    echo "✅ Dependency analysis complete"
else
    echo "⚠️  cargo-outdated not installed, skipping dependency analysis"
fi

# 4. Code Coverage
echo "📊 Running Code Coverage Analysis..."
if command -v cargo-tarpaulin &> /dev/null; then
    cargo tarpaulin --out Xml --output-dir reports/ --skip-clean > reports/coverage_report.txt 2>&1 || true
    echo "✅ Code coverage analysis complete"
else
    echo "⚠️  cargo-tarpaulin not installed, skipping coverage analysis"
fi

# 5. Documentation Check
echo "📝 Checking Documentation..."
if cargo doc --no-deps --document-private-items > reports/doc_report.txt 2>&1; then
    echo "✅ Documentation generation successful"
    DOC_STATUS="PASS"
else
    echo "❌ Documentation generation failed"
    DOC_STATUS="FAIL"
fi

# 6. Code Formatting Check
echo "✨ Checking Code Formatting..."
if cargo fmt --check > reports/formatting_report.txt 2>&1; then
    echo "✅ Code formatting: Correct"
    FMT_STATUS="PASS"
else
    echo "❌ Code formatting: Issues found (run 'cargo fmt' to fix)"
    FMT_STATUS="FAIL"
fi

# 7. Build Verification
echo "🔨 Verifying Build..."
if cargo build --release > reports/build_report.txt 2>&1; then
    echo "✅ Build verification: Successful"
    BUILD_STATUS="PASS"
else
    echo "❌ Build verification: Failed"
    BUILD_STATUS="FAIL"
fi

# 8. Test Suite Execution
echo "🧪 Running Test Suite..."
if cargo test --all > reports/test_report.txt 2>&1; then
    echo "✅ Test suite: All tests passing"
    TEST_STATUS="PASS"
else
    echo "❌ Test suite: Some tests failed"
    TEST_STATUS="FAIL"
fi

# 9. Benchmark Execution
echo "⏱️  Running Benchmarks..."
if cargo bench > reports/benchmark_report.txt 2>&1; then
    echo "✅ Benchmarks: Executed successfully"
    BENCH_STATUS="PASS"
else
    echo "⚠️  Benchmarks: Execution completed with warnings"
    BENCH_STATUS="WARN"
fi

# Generate Summary
echo ""
echo "=================================================="
echo "📊 BUGBOT ANALYSIS SUMMARY"
echo "=================================================="
echo ""
echo "Analysis Results:"
echo "  📋 Clippy:           $CLIPPY_STATUS"
echo "  🔒 Security:          $SECURITY_STATUS"
echo "  📝 Documentation:     $DOC_STATUS"
echo "  ✨ Formatting:        $FMT_STATUS"
echo "  🔨 Build:            $BUILD_STATUS"
echo "  🧪 Tests:            $TEST_STATUS"
echo "  ⏱️  Benchmarks:        $BENCH_STATUS"
echo ""

# Check if Python is available for detailed report generation
if command -v python3 &> /dev/null; then
    echo "🤖 Generating detailed bugbot report..."
    python3 scripts/generate_bugbot_report.py \
        --clippy reports/clippy_report.txt \
        --security reports/security_audit.txt \
        --dependencies reports/dependency_report.txt \
        --coverage reports/coverage_report.xml \
        --formatting reports/formatting_report.txt \
        --build reports/build_report.txt \
        --tests reports/test_report.txt \
        --output reports/bugbot_summary.md
    echo "✅ Detailed report generated: reports/bugbot_summary.md"
else
    echo "⚠️  Python 3 not available, skipping detailed report generation"
fi

echo ""
echo "=================================================="
echo "🎉 Bugbot Analysis Complete!"
echo "=================================================="
echo ""
echo "📁 Reports generated in: reports/"
echo "   - clippy_report.txt"
echo "   - security_audit.txt"
echo "   - dependency_report.txt"
echo "   - coverage_report.txt"
echo "   - doc_report.txt"
echo "   - formatting_report.txt"
echo "   - build_report.txt"
echo "   - test_report.txt"
echo "   - benchmark_report.txt"
echo "   - bugbot_summary.md (if Python available)"
echo ""

# Exit with appropriate code
if [ "$CLIPPY_STATUS" = "FAIL" ] || [ "$BUILD_STATUS" = "FAIL" ] || [ "$TEST_STATUS" = "FAIL" ]; then
    echo "❌ Critical issues found - please review reports"
    exit 1
else
    echo "✅ All critical checks passed - minor issues may exist"
    exit 0
fi