#!/usr/bin/env python3
"""
Master Analysis Runner
Runs all analysis scripts and generates summary report
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

def run_script(script_name, description):
    """Run an analysis script and capture results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    
    script_path = Path("analysis/scripts") / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False, f"Script not found: {script_name}"
    
    try:
        start_time = time.time()
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=300)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Execution time: {duration:.2f} seconds")
        print(f"📤 Return code: {result.returncode}")
        
        if result.stdout:
            print("\n📋 Output:")
            print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  Errors:")
            print(result.stderr)
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status}")
        
        return success, result.stdout if success else result.stderr
        
    except subprocess.TimeoutExpired:
        print("⏰ Script timed out after 5 minutes")
        return False, "Timeout after 5 minutes"
    except Exception as e:
        print(f"💥 Error running script: {e}")
        return False, str(e)

def generate_summary_report(results):
    """Generate a summary report of all analysis results."""
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    total_scripts = len(results)
    passed_scripts = sum(1 for success, _ in results.values() if success)
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"  Total Scripts Run: {total_scripts}")
    print(f"  Passed: {passed_scripts}")
    print(f"  Failed: {total_scripts - passed_scripts}")
    print(f"  Success Rate: {(passed_scripts/total_scripts)*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for script_name, (success, output) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {script_name:<35} {status}")
    
    # Generate recommendations based on results
    print(f"\n💡 RECOMMENDATIONS:")
    
    if passed_scripts == total_scripts:
        print("  🎉 All analysis scripts passed successfully!")
        print("  ✅ System is in excellent health")
        print("  📋 Review individual reports for detailed findings")
        print("  🔄 Schedule regular monitoring using these scripts")
    elif passed_scripts >= total_scripts * 0.8:
        print("  ✅ Most analysis scripts passed")
        print("  ⚠️  Address failed scripts for optimal system health")
        print("  📋 Focus on critical issues first")
    else:
        print("  ⚠️  Multiple analysis scripts failed")
        print("  🔴 System needs attention before production use")
        print("  📋 Review failed scripts and address issues immediately")
    
    # Save summary to file
    summary_path = Path("analysis/reports/ANALYSIS_SUMMARY.md")
    
    try:
        with open(summary_path, 'w') as f:
            f.write(f"# SCADA-IDS-KC Analysis Summary\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Results Overview\n\n")
            f.write(f"- **Total Scripts:** {total_scripts}\n")
            f.write(f"- **Passed:** {passed_scripts}\n")
            f.write(f"- **Failed:** {total_scripts - passed_scripts}\n")
            f.write(f"- **Success Rate:** {(passed_scripts/total_scripts)*100:.1f}%\n\n")
            
            f.write(f"## Detailed Results\n\n")
            for script_name, (success, output) in results.items():
                status = "✅ PASS" if success else "❌ FAIL"
                f.write(f"### {script_name} - {status}\n\n")
                if success:
                    # Extract key metrics from output if available
                    lines = output.split('\n')
                    key_lines = [line for line in lines if any(keyword in line.lower() 
                                for keyword in ['score:', 'passed', 'excellent', 'good', 'failed', 'error'])]
                    if key_lines:
                        f.write("**Key Findings:**\n")
                        for line in key_lines[:5]:  # Limit to top 5 findings
                            f.write(f"- {line.strip()}\n")
                        f.write("\n")
                else:
                    f.write(f"**Error:** {output}\n\n")
        
        print(f"\n📄 Summary report saved: {summary_path}")
        
    except Exception as e:
        print(f"⚠️  Could not save summary report: {e}")

def main():
    """Run all analysis scripts."""
    print("🔍 SCADA-IDS-KC Comprehensive Analysis Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to project root if needed
    if Path.cwd().name in ["scripts", "analysis"]:
        while Path.cwd().name != "SCADA-IDS-KC" and Path.cwd().parent != Path.cwd():
            os.chdir("..")
    
    print(f"Working directory: {Path.cwd()}")
    
    # Define analysis scripts to run
    analysis_scripts = [
        ("test_gui_packet_capture.py", "GUI Packet Capture Functionality Test"),
        ("test_cli_gui_parity.py", "CLI-GUI Parity Analysis"),
        ("feature_parity_analysis.py", "Comprehensive Feature Parity Analysis"),
        ("security_assessment.py", "Security Vulnerability Assessment"),
        ("performance_analysis.py", "Performance Bottleneck Analysis"),
        ("error_handling_assessment.py", "Error Handling Robustness Assessment"),
        ("code_quality_assessment.py", "Code Quality and Maintainability Analysis"),
        ("technical_health_check.py", "Technical Health Check"),
    ]
    
    results = {}
    start_time = time.time()
    
    # Run each analysis script
    for script_name, description in analysis_scripts:
        success, output = run_script(script_name, description)
        results[script_name] = (success, output)
        
        # Small delay between scripts
        time.sleep(1)
    
    total_time = time.time() - start_time
    
    # Generate summary
    generate_summary_report(results)
    
    print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
    print(f"📁 All reports available in: analysis/reports/")
    print(f"🔧 Analysis scripts available in: analysis/scripts/")
    
    # Determine overall success
    passed_count = sum(1 for success, _ in results.values() if success)
    total_count = len(results)
    success_rate = passed_count / total_count
    
    if success_rate >= 0.9:
        print("\n🎉 EXCELLENT: System analysis completed successfully!")
        return True
    elif success_rate >= 0.7:
        print("\n✅ GOOD: Most analysis completed successfully with minor issues")
        return True
    else:
        print("\n⚠️  ATTENTION NEEDED: Multiple analysis scripts failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
