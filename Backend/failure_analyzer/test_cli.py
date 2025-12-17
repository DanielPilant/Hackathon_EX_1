"""
Standalone CLI for Testing the Failure Analyzer

Run the analyzer without MCP server for development and testing.

Usage:
    python -m failure_analyzer.test_cli                        # Run all fixtures
    python -m failure_analyzer.test_cli --fixture timeout_error # Run specific fixture
    python -m failure_analyzer.test_cli --list                 # List available fixtures
    python -m failure_analyzer.test_cli --json '{"type":"log",...}'  # Custom JSON
    python -m failure_analyzer.test_cli --file sample.json     # From file
    python -m failure_analyzer.test_cli --no-ai                # Skip OpenAI (rules only)
    python -m failure_analyzer.test_cli --verbose              # Show detailed output
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from failure_analyzer.analyzer import FailureAnalyzer
from failure_analyzer.normalizer import normalize_mcp_event, is_failure_event
from failure_analyzer.classifier import classify_failure
from failure_analyzer.test_fixtures import (
    SAMPLE_FAILURES,
    EXPECTED_CLASSIFICATIONS,
    get_fixture,
    get_all_failure_fixtures,
    get_non_failure_fixtures
)


# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")


def print_section(title: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.DIM}{'-'*40}{Colors.ENDC}")


def print_json(data: Any, indent: int = 2):
    print(json.dumps(data, indent=indent, ensure_ascii=False, default=str))


def print_result(label: str, value: str, color: str = Colors.GREEN):
    print(f"  {Colors.BOLD}{label}:{Colors.ENDC} {color}{value}{Colors.ENDC}")


async def analyze_fixture(
    name: str,
    fixture: Dict[str, Any],
    analyzer: FailureAnalyzer,
    verbose: bool = False
) -> Dict[str, Any]:
    """Analyze a single fixture and display results."""
    print_header(f"Fixture: {name}")
    
    # Show input
    print_section("Input Event")
    if verbose:
        print_json(fixture)
    else:
        # Truncated view
        truncated = json.dumps(fixture, ensure_ascii=False)
        if len(truncated) > 200:
            truncated = truncated[:200] + "..."
        print(truncated)
    
    # Check if failure
    is_fail = is_failure_event(fixture)
    print_section("Failure Detection")
    if is_fail:
        print_result("Is Failure", "YES", Colors.RED)
    else:
        print_result("Is Failure", "NO", Colors.GREEN)
        return {"status": "ignored_non_failure_log"}
    
    # Normalize
    normalized = normalize_mcp_event(fixture)
    print_section("Normalized Data")
    if normalized:
        print_result("Step", normalized.step or "(none)")
        print_result("Locator Hints", str(normalized.locator_hints) or "(none)")
        if verbose:
            print_result("Raw Message", normalized.raw_message[:200])
            if normalized.console_lines:
                print_result("Console", str(normalized.console_lines[:2]))
    else:
        print(f"  {Colors.RED}Normalization failed{Colors.ENDC}")
    
    # Classify
    if normalized:
        classification = classify_failure(normalized)
        print_section("Classification (Rule-Based)")
        
        expected = EXPECTED_CLASSIFICATIONS.get(name)
        actual = classification.category.value
        
        if expected and expected == actual:
            print_result("Category", actual, Colors.GREEN)
        elif expected:
            print_result("Category", f"{actual} (expected: {expected})", Colors.YELLOW)
        else:
            print_result("Category", actual, Colors.BLUE)
        
        print_result("Evidence", "")
        for ev in classification.evidence[:5]:
            print(f"    - {ev}")
        print_result("Confidence Modifier", f"{classification.confidence_modifier:+.2f}")
    
    # Full analysis
    print_section("Full Analysis")
    result = await analyzer.analyze(fixture)
    
    if "status" in result and result["status"] == "ignored_non_failure_log":
        print(f"  {Colors.DIM}Event ignored (not a failure){Colors.ENDC}")
    else:
        print_result("Analysis ID", result.get("analysis_id", "N/A"))
        print_result("Failed Step", result.get("failed_step") or "(unknown)")
        print_result("Category", result.get("failure_category", "UNKNOWN"))
        print_result("Confidence", f"{result.get('confidence', 0):.2f}")
        print()
        print(f"  {Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"    {result.get('summary', 'N/A')}")
        print()
        print(f"  {Colors.BOLD}Why:{Colors.ENDC}")
        print(f"    {result.get('why', 'N/A')}")
        print()
        print(f"  {Colors.BOLD}Suggested Fix:{Colors.ENDC}")
        print(f"    {result.get('suggested_fix', 'N/A')}")
    
    return result


async def run_all_fixtures(analyzer: FailureAnalyzer, verbose: bool = False):
    """Run all test fixtures."""
    print_header("Running All Fixtures")
    
    results = {}
    passed = 0
    failed = 0
    
    for name, fixture in get_all_failure_fixtures().items():
        result = await analyze_fixture(name, fixture, analyzer, verbose)
        results[name] = result
        
        # Check if classification matches expected
        expected = EXPECTED_CLASSIFICATIONS.get(name)
        actual = result.get("failure_category")
        
        if expected and expected == actual:
            passed += 1
        elif expected:
            failed += 1
            print(f"{Colors.YELLOW}  ⚠ Classification mismatch: expected {expected}, got {actual}{Colors.ENDC}")
    
    # Test non-failure fixtures
    print_header("Testing Non-Failure Events")
    for name, fixture in get_non_failure_fixtures().items():
        result = await analyze_fixture(name, fixture, analyzer, verbose)
        if result.get("status") == "ignored_non_failure_log":
            passed += 1
            print(f"{Colors.GREEN}  ✓ Correctly ignored{Colors.ENDC}")
        else:
            failed += 1
            print(f"{Colors.RED}  ✗ Should have been ignored{Colors.ENDC}")
    
    # Summary
    print_header("Summary")
    total = passed + failed
    print(f"  {Colors.GREEN}Passed:{Colors.ENDC} {passed}/{total}")
    if failed > 0:
        print(f"  {Colors.RED}Failed:{Colors.ENDC} {failed}/{total}")
    
    return results


async def analyze_custom_json(
    json_str: str,
    analyzer: FailureAnalyzer,
    verbose: bool = False
) -> Dict[str, Any]:
    """Analyze custom JSON input."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}Invalid JSON: {e}{Colors.ENDC}")
        sys.exit(1)
    
    return await analyze_fixture("custom", data, analyzer, verbose)


async def analyze_file(
    file_path: str,
    analyzer: FailureAnalyzer,
    verbose: bool = False
) -> Dict[str, Any]:
    """Analyze JSON from file."""
    path = Path(file_path)
    if not path.exists():
        print(f"{Colors.RED}File not found: {file_path}{Colors.ENDC}")
        sys.exit(1)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}Invalid JSON in file: {e}{Colors.ENDC}")
        sys.exit(1)
    
    return await analyze_fixture(path.name, data, analyzer, verbose)


def list_fixtures():
    """List all available test fixtures."""
    print_header("Available Test Fixtures")
    
    print_section("Failure Fixtures")
    for name in get_all_failure_fixtures().keys():
        expected = EXPECTED_CLASSIFICATIONS.get(name, "?")
        print(f"  - {name} ({expected})")
    
    print_section("Non-Failure Fixtures")
    for name in get_non_failure_fixtures().keys():
        print(f"  - {name}")


async def main():
    parser = argparse.ArgumentParser(
        description="Test the Failure Analyzer without MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m failure_analyzer.test_cli                        # Run all fixtures
  python -m failure_analyzer.test_cli --fixture timeout_error
  python -m failure_analyzer.test_cli --list
  python -m failure_analyzer.test_cli --no-ai
  python -m failure_analyzer.test_cli --json '{"type":"error","data":"TimeoutError"}'
        """
    )
    
    parser.add_argument(
        "--fixture", "-f",
        help="Run specific fixture by name"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available fixtures"
    )
    parser.add_argument(
        "--json", "-j",
        help="Analyze custom JSON string"
    )
    parser.add_argument(
        "--file",
        help="Analyze JSON from file"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip OpenAI calls (use mock responses)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    
    args = parser.parse_args()
    
    # List fixtures
    if args.list:
        list_fixtures()
        return
    
    # Create analyzer
    analyzer = FailureAnalyzer(mock_openai=args.no_ai)
    
    if args.no_ai:
        print(f"{Colors.YELLOW}Running with mock OpenAI (--no-ai){Colors.ENDC}")
    
    # Run based on arguments
    if args.json:
        await analyze_custom_json(args.json, analyzer, args.verbose)
    elif args.file:
        await analyze_file(args.file, analyzer, args.verbose)
    elif args.fixture:
        try:
            fixture = get_fixture(args.fixture)
            await analyze_fixture(args.fixture, fixture, analyzer, args.verbose)
        except KeyError as e:
            print(f"{Colors.RED}{e}{Colors.ENDC}")
            print("Use --list to see available fixtures")
            sys.exit(1)
    else:
        # Run all fixtures
        await run_all_fixtures(analyzer, args.verbose)


if __name__ == "__main__":
    asyncio.run(main())
