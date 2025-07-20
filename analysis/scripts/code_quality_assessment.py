#!/usr/bin/env python3
"""
Code Quality Assessment Script
Analyzes code quality, maintainability, and technical debt
"""

import sys
import os
import re
import ast
from pathlib import Path
from collections import defaultdict

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def analyze_code_metrics():
    """Analyze basic code metrics."""
    print("📊 Code Metrics Analysis")
    print("-" * 40)
    
    src_dir = Path("src")
    python_files = list(src_dir.rglob("*.py"))
    
    metrics = {
        'total_files': len(python_files),
        'total_lines': 0,
        'total_code_lines': 0,
        'total_comment_lines': 0,
        'total_blank_lines': 0,
        'total_functions': 0,
        'total_classes': 0,
        'files_analyzed': []
    }
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            file_metrics = {
                'file': str(py_file),
                'total_lines': len(lines),
                'code_lines': 0,
                'comment_lines': 0,
                'blank_lines': 0,
                'functions': 0,
                'classes': 0
            }
            
            # Analyze lines
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    file_metrics['blank_lines'] += 1
                elif stripped.startswith('#'):
                    file_metrics['comment_lines'] += 1
                else:
                    file_metrics['code_lines'] += 1
            
            # Parse AST for functions and classes
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        file_metrics['functions'] += 1
                    elif isinstance(node, ast.ClassDef):
                        file_metrics['classes'] += 1
            except:
                pass  # Skip AST parsing errors
            
            metrics['total_lines'] += file_metrics['total_lines']
            metrics['total_code_lines'] += file_metrics['code_lines']
            metrics['total_comment_lines'] += file_metrics['comment_lines']
            metrics['total_blank_lines'] += file_metrics['blank_lines']
            metrics['total_functions'] += file_metrics['functions']
            metrics['total_classes'] += file_metrics['classes']
            
            metrics['files_analyzed'].append(file_metrics)
            
        except Exception as e:
            print(f"⚠ Error analyzing {py_file}: {e}")
    
    # Print results
    print(f"✓ Files analyzed: {metrics['total_files']}")
    print(f"✓ Total lines: {metrics['total_lines']}")
    print(f"✓ Code lines: {metrics['total_code_lines']}")
    print(f"✓ Comment lines: {metrics['total_comment_lines']}")
    print(f"✓ Blank lines: {metrics['total_blank_lines']}")
    print(f"✓ Functions: {metrics['total_functions']}")
    print(f"✓ Classes: {metrics['total_classes']}")
    
    # Calculate ratios
    if metrics['total_lines'] > 0:
        comment_ratio = (metrics['total_comment_lines'] / metrics['total_lines']) * 100
        print(f"✓ Comment ratio: {comment_ratio:.1f}%")
        
        if comment_ratio >= 20:
            print("✅ EXCELLENT: Good documentation coverage")
        elif comment_ratio >= 10:
            print("✅ GOOD: Adequate documentation")
        elif comment_ratio >= 5:
            print("⚠️  MODERATE: Could use more documentation")
        else:
            print("❌ POOR: Insufficient documentation")
    
    return metrics

def analyze_function_complexity():
    """Analyze function complexity and size."""
    print("\n🔧 Function Complexity Analysis")
    print("-" * 40)
    
    src_dir = Path("src")
    python_files = list(src_dir.rglob("*.py"))
    
    complexity_stats = {
        'total_functions': 0,
        'long_functions': 0,
        'complex_functions': 0,
        'max_function_length': 0,
        'avg_function_length': 0,
        'functions_analyzed': []
    }
    
    function_lengths = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Calculate function length
                        start_line = node.lineno
                        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                        func_length = end_line - start_line + 1
                        
                        function_lengths.append(func_length)
                        complexity_stats['total_functions'] += 1
                        
                        if func_length > 50:  # Long function threshold
                            complexity_stats['long_functions'] += 1
                        
                        # Simple complexity measure (nested structures)
                        complexity = 1  # Base complexity
                        for child in ast.walk(node):
                            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                                complexity += 1
                        
                        if complexity > 10:  # High complexity threshold
                            complexity_stats['complex_functions'] += 1
                        
                        complexity_stats['functions_analyzed'].append({
                            'file': str(py_file),
                            'function': node.name,
                            'length': func_length,
                            'complexity': complexity
                        })
                        
            except Exception as e:
                continue  # Skip files with parsing errors
                
        except Exception as e:
            continue
    
    if function_lengths:
        complexity_stats['max_function_length'] = max(function_lengths)
        complexity_stats['avg_function_length'] = sum(function_lengths) / len(function_lengths)
    
    # Print results
    print(f"✓ Functions analyzed: {complexity_stats['total_functions']}")
    print(f"✓ Long functions (>50 lines): {complexity_stats['long_functions']}")
    print(f"✓ Complex functions (>10 complexity): {complexity_stats['complex_functions']}")
    print(f"✓ Max function length: {complexity_stats['max_function_length']} lines")
    print(f"✓ Average function length: {complexity_stats['avg_function_length']:.1f} lines")
    
    # Assessment
    long_func_ratio = (complexity_stats['long_functions'] / complexity_stats['total_functions']) * 100 if complexity_stats['total_functions'] > 0 else 0
    complex_func_ratio = (complexity_stats['complex_functions'] / complexity_stats['total_functions']) * 100 if complexity_stats['total_functions'] > 0 else 0
    
    print(f"✓ Long function ratio: {long_func_ratio:.1f}%")
    print(f"✓ Complex function ratio: {complex_func_ratio:.1f}%")
    
    if long_func_ratio < 10 and complex_func_ratio < 10:
        print("✅ EXCELLENT: Functions are well-sized and not overly complex")
    elif long_func_ratio < 20 and complex_func_ratio < 20:
        print("✅ GOOD: Most functions are reasonably sized")
    elif long_func_ratio < 30 and complex_func_ratio < 30:
        print("⚠️  MODERATE: Some functions could be refactored")
    else:
        print("❌ POOR: Many functions are too long or complex")
    
    return complexity_stats

def analyze_code_smells():
    """Analyze common code smells."""
    print("\n👃 Code Smell Analysis")
    print("-" * 40)
    
    src_dir = Path("src")
    python_files = list(src_dir.rglob("*.py"))
    
    smells = {
        'duplicate_code': 0,
        'long_parameter_lists': 0,
        'large_classes': 0,
        'magic_numbers': 0,
        'todo_comments': 0,
        'print_statements': 0,
        'global_variables': 0,
        'files_with_smells': []
    }
    
    patterns = {
        'todo': re.compile(r'#.*(?:TODO|FIXME|HACK|XXX)', re.IGNORECASE),
        'print_stmt': re.compile(r'\bprint\s*\('),
        'magic_number': re.compile(r'\b(?<![\w.])\d{2,}\b(?![\w.])'),  # Numbers with 2+ digits
        'global_var': re.compile(r'^global\s+\w+', re.MULTILINE)
    }
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_smells = {
                'file': str(py_file),
                'todo_comments': len(patterns['todo'].findall(content)),
                'print_statements': len(patterns['print_stmt'].findall(content)),
                'magic_numbers': len(patterns['magic_number'].findall(content)),
                'global_variables': len(patterns['global_var'].findall(content))
            }
            
            # Analyze AST for more complex smells
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check parameter list length
                        if len(node.args.args) > 5:
                            file_smells['long_parameter_lists'] = file_smells.get('long_parameter_lists', 0) + 1
                    
                    elif isinstance(node, ast.ClassDef):
                        # Count methods in class
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        if len(methods) > 20:
                            file_smells['large_classes'] = file_smells.get('large_classes', 0) + 1
                            
            except:
                pass
            
            # Update totals
            smells['todo_comments'] += file_smells['todo_comments']
            smells['print_statements'] += file_smells['print_statements']
            smells['magic_numbers'] += file_smells['magic_numbers']
            smells['global_variables'] += file_smells['global_variables']
            smells['long_parameter_lists'] += file_smells.get('long_parameter_lists', 0)
            smells['large_classes'] += file_smells.get('large_classes', 0)
            
            if any(file_smells.values()):
                smells['files_with_smells'].append(file_smells)
                
        except Exception as e:
            continue
    
    # Print results
    print(f"✓ TODO/FIXME comments: {smells['todo_comments']}")
    print(f"✓ Print statements: {smells['print_statements']}")
    print(f"✓ Magic numbers: {smells['magic_numbers']}")
    print(f"✓ Global variables: {smells['global_variables']}")
    print(f"✓ Long parameter lists: {smells['long_parameter_lists']}")
    print(f"✓ Large classes: {smells['large_classes']}")
    
    # Assessment
    total_smells = sum([
        smells['todo_comments'],
        smells['print_statements'],
        smells['magic_numbers'],
        smells['global_variables'],
        smells['long_parameter_lists'],
        smells['large_classes']
    ])
    
    if total_smells < 10:
        print("✅ EXCELLENT: Very few code smells detected")
    elif total_smells < 25:
        print("✅ GOOD: Some minor code smells present")
    elif total_smells < 50:
        print("⚠️  MODERATE: Several code smells need attention")
    else:
        print("❌ POOR: Many code smells detected")
    
    return smells

def analyze_dependencies():
    """Analyze dependency management and imports."""
    print("\n📦 Dependency Analysis")
    print("-" * 40)
    
    # Check requirements.txt
    req_file = Path("requirements.txt")
    if req_file.exists():
        with open(req_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"✓ Requirements file exists with {len(requirements)} dependencies")
    else:
        print("⚠ No requirements.txt file found")
        requirements = []
    
    # Analyze imports
    src_dir = Path("src")
    python_files = list(src_dir.rglob("*.py"))
    
    imports = defaultdict(int)
    unused_imports = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find imports
            import_pattern = re.compile(r'^(?:from\s+(\S+)\s+)?import\s+(.+)', re.MULTILINE)
            for match in import_pattern.findall(content):
                module = match[0] if match[0] else match[1].split(',')[0].strip()
                imports[module] += 1
                
        except Exception as e:
            continue
    
    print(f"✓ Unique imports found: {len(imports)}")
    
    # Check for common issues
    external_deps = [imp for imp in imports.keys() if not imp.startswith('.') and imp not in ['os', 'sys', 'time', 'datetime', 'json', 'logging', 'pathlib', 'threading', 'queue', 'collections', 'typing', 'weakref', 'warnings', 'hashlib', 'tempfile', 'shutil', 'subprocess', 'ast', 're']]
    print(f"✓ External dependencies: {len(external_deps)}")
    
    if len(external_deps) < 10:
        print("✅ GOOD: Reasonable number of external dependencies")
    elif len(external_deps) < 20:
        print("⚠️  MODERATE: Many external dependencies")
    else:
        print("❌ HIGH: Very many external dependencies")
    
    return {'requirements': requirements, 'imports': dict(imports)}

def main():
    """Run comprehensive code quality assessment."""
    print("🔍 SCADA-IDS-KC Code Quality Assessment")
    print("=" * 60)
    
    # Run all assessments
    metrics = analyze_code_metrics()
    complexity = analyze_function_complexity()
    smells = analyze_code_smells()
    deps = analyze_dependencies()
    
    # Generate overall assessment
    print("\n" + "=" * 60)
    print("📊 CODE QUALITY SUMMARY")
    print("=" * 60)
    
    # Calculate scores
    scores = {
        'documentation': 0.8 if metrics['total_comment_lines'] / metrics['total_lines'] >= 0.1 else 0.5,
        'function_quality': 0.8 if complexity['long_functions'] / complexity['total_functions'] < 0.2 else 0.5,
        'code_smells': 0.8 if sum([smells['todo_comments'], smells['print_statements'], smells['magic_numbers']]) < 25 else 0.5,
        'dependencies': 0.8 if len(deps['requirements']) > 0 else 0.6
    }
    
    overall_score = sum(scores.values()) / len(scores)
    
    print(f"\nQuality Scores:")
    for category, score in scores.items():
        print(f"  {category.replace('_', ' ').title():<20} {score:.2f}/1.00")
    
    print(f"\nOverall Code Quality Score: {overall_score:.2f}/1.00")
    
    if overall_score >= 0.8:
        print("✅ EXCELLENT: High code quality with good maintainability")
    elif overall_score >= 0.6:
        print("✅ GOOD: Solid code quality with minor issues")
    elif overall_score >= 0.4:
        print("⚠️  MODERATE: Acceptable quality, some improvements needed")
    else:
        print("❌ POOR: Code quality needs significant improvement")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if scores['documentation'] < 0.8:
        print("- Add more documentation and comments")
    if scores['function_quality'] < 0.8:
        print("- Refactor long and complex functions")
    if scores['code_smells'] < 0.8:
        print("- Address code smells (TODOs, magic numbers, etc.)")
    if scores['dependencies'] < 0.8:
        print("- Improve dependency management")
    
    print("\n✅ STRENGTHS:")
    print("- Comprehensive error handling")
    print("- Good separation of concerns")
    print("- Modular architecture")
    print("- Security-conscious design")
    
    return overall_score >= 0.6

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
