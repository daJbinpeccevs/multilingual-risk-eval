#!/usr/bin/env python3
"""
Project validation and self-check script.

This script performs comprehensive validation of the multilingual risk evaluation project,
checking for logical consistency, architectural integrity, and potential issues.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple

class ProjectValidator:
    """Comprehensive project validation."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.validation_results = {
            "overall_status": "unknown",
            "checks": {},
            "issues": [],
            "recommendations": []
        }
    
    def validate_structure(self) -> bool:
        """Validate project directory structure."""
        required_dirs = [
            "configs", "data", "models", "scripts", "utils", "results", "tests", "logs"
        ]
        required_files = [
            "README.md", "requirements.txt", ".gitignore", "setup_and_test.py"
        ]
        
        structure_valid = True
        missing_dirs = []
        missing_files = []
        
        # Check directories
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
                structure_valid = False
        
        # Check files
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                missing_files.append(file_name)
                structure_valid = False
        
        self.validation_results["checks"]["structure"] = {
            "status": "pass" if structure_valid else "fail",
            "missing_directories": missing_dirs,
            "missing_files": missing_files
        }
        
        return structure_valid
    
    def validate_python_modules(self) -> bool:
        """Validate Python module structure and imports."""
        required_modules = {
            "models": ["__init__.py", "base_model.py", "model_loader.py", 
                      "claude_api_wrapper.py", "openai_api_wrapper.py"],
            "utils": ["__init__.py", "logger.py", "metrics.py", "prompt_builder.py"],
            "scripts": ["__init__.py", "run_evaluation.py", "preprocess_data.py"],
            "tests": ["__init__.py"]
        }
        
        modules_valid = True
        issues = []
        
        for module_dir, files in required_modules.items():
            module_path = self.project_root / module_dir
            
            if not module_path.exists():
                issues.append(f"Missing module directory: {module_dir}")
                modules_valid = False
                continue
            
            for file_name in files:
                file_path = module_path / file_name
                if not file_path.exists():
                    issues.append(f"Missing module file: {module_dir}/{file_name}")
                    modules_valid = False
        
        self.validation_results["checks"]["python_modules"] = {
            "status": "pass" if modules_valid else "fail",
            "issues": issues
        }
        
        return modules_valid
    
    def validate_configurations(self) -> bool:
        """Validate YAML configuration files."""
        config_files = ["default_config.yaml", "quick_test_config.yaml", "comprehensive_config.yaml"]
        required_fields = ["model", "languages", "domains", "num_samples", "output_path"]
        
        configs_valid = True
        issues = []
        
        for config_file in config_files:
            config_path = self.project_root / "configs" / config_file
            
            if not config_path.exists():
                issues.append(f"Missing configuration file: {config_file}")
                configs_valid = False
                continue
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # Check required fields
                for field in required_fields:
                    if field not in config:
                        issues.append(f"{config_file}: Missing required field '{field}'")
                        configs_valid = False
                
                # Validate specific field types
                if "languages" in config and not isinstance(config["languages"], list):
                    issues.append(f"{config_file}: 'languages' should be a list")
                    configs_valid = False
                
                if "domains" in config and not isinstance(config["domains"], list):
                    issues.append(f"{config_file}: 'domains' should be a list")
                    configs_valid = False
                
            except yaml.YAMLError as e:
                issues.append(f"{config_file}: Invalid YAML format - {str(e)}")
                configs_valid = False
            except Exception as e:
                issues.append(f"{config_file}: Error reading file - {str(e)}")
                configs_valid = False
        
        self.validation_results["checks"]["configurations"] = {
            "status": "pass" if configs_valid else "fail",
            "issues": issues
        }
        
        return configs_valid
    
    def validate_dependencies(self) -> bool:
        """Validate requirements.txt and dependencies."""
        requirements_path = self.project_root / "requirements.txt"
        
        if not requirements_path.exists():
            self.validation_results["checks"]["dependencies"] = {
                "status": "fail",
                "issues": ["Missing requirements.txt file"]
            }
            return False
        
        try:
            with open(requirements_path, 'r') as f:
                requirements = f.read().strip().split('\n')
            
            expected_packages = ["openai", "anthropic", "pyyaml", "pandas", "numpy", "tqdm"]
            missing_packages = []
            
            for package in expected_packages:
                if not any(req.startswith(package) for req in requirements if req.strip()):
                    missing_packages.append(package)
            
            deps_valid = len(missing_packages) == 0
            
            self.validation_results["checks"]["dependencies"] = {
                "status": "pass" if deps_valid else "fail",
                "missing_packages": missing_packages,
                "total_requirements": len([r for r in requirements if r.strip()])
            }
            
            return deps_valid
            
        except Exception as e:
            self.validation_results["checks"]["dependencies"] = {
                "status": "fail",
                "issues": [f"Error reading requirements.txt: {str(e)}"]
            }
            return False
    
    def validate_code_logic(self) -> Tuple[bool, List[str]]:
        """Validate logical consistency and architectural patterns."""
        issues = []
        recommendations = []
        
        # Check model inheritance pattern
        base_model_path = self.project_root / "models" / "base_model.py"
        if base_model_path.exists():
            try:
                with open(base_model_path, 'r') as f:
                    base_content = f.read()
                
                if "class BaseModel" not in base_content or "@abstractmethod" not in base_content:
                    issues.append("BaseModel should be an abstract base class with abstract methods")
            except Exception as e:
                issues.append(f"Error reading base_model.py: {str(e)}")
        
        # Check if model wrappers implement the interface
        model_files = ["claude_api_wrapper.py", "openai_api_wrapper.py"]
        for model_file in model_files:
            model_path = self.project_root / "models" / model_file
            if model_path.exists():
                try:
                    with open(model_path, 'r') as f:
                        content = f.read()
                    
                    if "BaseModel" not in content:
                        issues.append(f"{model_file} should inherit from BaseModel")
                    
                    if "def generate(" not in content:
                        issues.append(f"{model_file} should implement generate() method")
                        
                except Exception as e:
                    issues.append(f"Error reading {model_file}: {str(e)}")
        
        # Check risk evaluation logic
        metrics_path = self.project_root / "utils" / "metrics.py"
        if metrics_path.exists():
            try:
                with open(metrics_path, 'r') as f:
                    content = f.read()
                
                if "RISK_KEYWORDS" not in content:
                    issues.append("Risk evaluation should include keyword-based detection")
                
                if "SAFETY_INDICATORS" not in content:
                    issues.append("Risk evaluation should include safety indicators")
                    
            except Exception as e:
                issues.append(f"Error reading metrics.py: {str(e)}")
        
        # Check prompt builder multilingual support
        prompt_builder_path = self.project_root / "utils" / "prompt_builder.py"
        if prompt_builder_path.exists():
            try:
                with open(prompt_builder_path, 'r') as f:
                    content = f.read()
                
                languages = ["en", "zh", "es", "fr"]
                for lang in languages:
                    if f'"{lang}"' not in content:
                        recommendations.append(f"Consider adding more {lang} language prompts")
                        
            except Exception as e:
                issues.append(f"Error reading prompt_builder.py: {str(e)}")
        
        logic_valid = len(issues) == 0
        
        self.validation_results["checks"]["code_logic"] = {
            "status": "pass" if logic_valid else "fail",
            "issues": issues,
            "recommendations": recommendations
        }
        
        return logic_valid, recommendations
    
    def validate_security(self) -> bool:
        """Validate security best practices."""
        security_issues = []
        
        # Check for hardcoded secrets
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for potential hardcoded API keys
                if "sk-" in content and "api_key" in content.lower():
                    if "os.getenv" not in content:
                        security_issues.append(f"{py_file.name}: Potential hardcoded API key")
                
                # Check for eval() or exec() usage
                if "eval(" in content or "exec(" in content:
                    security_issues.append(f"{py_file.name}: Use of eval() or exec() detected")
                    
            except Exception:
                pass  # Skip files that can't be read
        
        # Check .gitignore includes sensitive files
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r') as f:
                    gitignore_content = f.read()
                
                if ".env" not in gitignore_content:
                    security_issues.append(".gitignore should include .env files")
                
                if "*.key" not in gitignore_content:
                    security_issues.append(".gitignore should include *.key files")
                    
            except Exception as e:
                security_issues.append(f"Error reading .gitignore: {str(e)}")
        
        security_valid = len(security_issues) == 0
        
        self.validation_results["checks"]["security"] = {
            "status": "pass" if security_valid else "fail",
            "issues": security_issues
        }
        
        return security_valid
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete project validation."""
        print("🔍 Running comprehensive project validation...")
        print("=" * 50)
        
        # Run all validation checks
        structure_ok = self.validate_structure()
        modules_ok = self.validate_python_modules()
        configs_ok = self.validate_configurations()
        deps_ok = self.validate_dependencies()
        logic_ok, recommendations = self.validate_code_logic()
        security_ok = self.validate_security()
        
        # Determine overall status
        all_checks = [structure_ok, modules_ok, configs_ok, deps_ok, logic_ok, security_ok]
        overall_status = "pass" if all(all_checks) else "fail"
        
        self.validation_results["overall_status"] = overall_status
        self.validation_results["recommendations"].extend(recommendations)
        
        # Print results
        self._print_validation_results()
        
        return self.validation_results
    
    def _print_validation_results(self):
        """Print formatted validation results."""
        print(f"\n📊 VALIDATION RESULTS")
        print(f"Overall Status: {'✅ PASS' if self.validation_results['overall_status'] == 'pass' else '❌ FAIL'}")
        print(f"=" * 50)
        
        # Print individual check results
        for check_name, check_data in self.validation_results["checks"].items():
            status_icon = "✅" if check_data["status"] == "pass" else "❌"
            print(f"{status_icon} {check_name.replace('_', ' ').title()}: {check_data['status'].upper()}")
            
            if "issues" in check_data and check_data["issues"]:
                for issue in check_data["issues"]:
                    print(f"   - {issue}")
            
            if "missing_directories" in check_data and check_data["missing_directories"]:
                for missing in check_data["missing_directories"]:
                    print(f"   - Missing directory: {missing}")
            
            if "missing_files" in check_data and check_data["missing_files"]:
                for missing in check_data["missing_files"]:
                    print(f"   - Missing file: {missing}")
        
        # Print recommendations
        if self.validation_results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS")
            print(f"-" * 20)
            for rec in self.validation_results["recommendations"]:
                print(f"• {rec}")
        
        print(f"\n🎯 PROJECT SUMMARY")
        print(f"-" * 20)
        print(f"• Complete multilingual risk evaluation framework")
        print(f"• Support for Claude and OpenAI models")
        print(f"• Risk assessment across healthcare, legal, and education domains")
        print(f"• Multi-language support (English, Chinese, Spanish, French)")
        print(f"• Comprehensive logging and reporting system")
        print(f"• Flexible configuration and extensible architecture")


def main():
    """Main validation entry point."""
    validator = ProjectValidator()
    results = validator.run_full_validation()
    
    # Save validation report
    report_path = Path("validation_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Detailed validation report saved to: {report_path}")
    
    # Return appropriate exit code
    return 0 if results["overall_status"] == "pass" else 1


if __name__ == "__main__":
    exit(main())