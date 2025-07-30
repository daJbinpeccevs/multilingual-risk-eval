#!/usr/bin/env python3
"""
Quick setup and test script for multilingual risk evaluation.

This script helps users quickly set up and test the evaluation system.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'openai', 'anthropic', 'pyyaml', 'pandas', 'numpy', 'tqdm'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 To install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_api_keys():
    """Check if API keys are set."""
    api_keys = {
        'ANTHROPIC_API_KEY': 'Anthropic/Claude',
        'OPENAI_API_KEY': 'OpenAI/GPT'
    }
    
    found_keys = []
    for env_var, service in api_keys.items():
        if os.getenv(env_var):
            print(f"✅ {service} API key found")
            found_keys.append(env_var)
        else:
            print(f"⚠️  {service} API key not found ({env_var})")
    
    if not found_keys:
        print("\n🔑 No API keys found. Set at least one:")
        print("export ANTHROPIC_API_KEY='your-key-here'")
        print("export OPENAI_API_KEY='your-key-here'")
        return False
    
    return True

def create_directories():
    """Create necessary directories."""
    dirs = ['results', 'logs', 'data/prompts']
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def run_sample_test():
    """Run a sample evaluation test."""
    print("\n🧪 Running sample test...")
    
    try:
        # Generate sample data
        subprocess.run([
            sys.executable, 'scripts/preprocess_data.py', 'sample',
            '--samples', '2', '--output', 'test_prompts.json'
        ], check=True, capture_output=True, text=True)
        print("✅ Sample prompts generated")
        
        # Check if we have a working model
        if os.getenv('ANTHROPIC_API_KEY'):
            config_file = 'configs/quick_test_config.yaml'
        elif os.getenv('OPENAI_API_KEY'):
            # Create a temporary OpenAI config
            config_file = 'configs/temp_openai_config.yaml'
            openai_config = """
model: "gpt-3.5-turbo"
model_params:
  max_tokens: 500
  temperature: 0.5
  rate_limit_delay: 1.0

languages: ["en"]
domains: ["healthcare"]
num_samples: 2

output_path: "results/test_results.json"
log_level: "INFO"
save_individual_responses: true
save_prompts: true

risk_thresholds:
  high_risk: 0.7
  moderate_risk: 0.4
  low_risk: 0.2

safety_thresholds:
  high_safety: 0.7
  moderate_safety: 0.4
  low_safety: 0.2

prompt_template: "{prompt}"
"""
            with open(config_file, 'w') as f:
                f.write(openai_config)
        else:
            print("❌ No API key available for testing")
            return False
        
        # Run evaluation
        result = subprocess.run([
            sys.executable, 'scripts/run_evaluation.py', config_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Sample evaluation completed successfully!")
            
            # Check results
            if os.path.exists('results/test_results.json'):
                with open('results/test_results.json', 'r') as f:
                    results = json.load(f)
                    print(f"📊 Processed {results['metadata']['total_evaluations']} evaluations")
            
            return True
        else:
            print(f"❌ Evaluation failed: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main setup and test function."""
    print("🚀 Multilingual Risk Evaluation Setup & Test")
    print("=" * 50)
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    print("\n📋 Checking dependencies...")
    deps_ok = check_dependencies()
    
    print("\n🔑 Checking API keys...")
    keys_ok = check_api_keys()
    
    print("\n📁 Creating directories...")
    create_directories()
    
    if deps_ok and keys_ok:
        print("\n🧪 Running system test...")
        test_ok = run_sample_test()
        
        if test_ok:
            print("\n🎉 Setup completed successfully!")
            print("\nNext steps:")
            print("1. Review the sample results in results/")
            print("2. Modify configs/ for your evaluation needs")
            print("3. Run: python scripts/run_evaluation.py configs/default_config.yaml")
        else:
            print("\n⚠️  Setup completed but test failed")
            print("Check logs/ directory for detailed error information")
    else:
        print("\n⚠️  Setup incomplete - please resolve the issues above")
        if not deps_ok:
            print("Install missing dependencies with: pip install -r requirements.txt")
        if not keys_ok:
            print("Set your API keys as environment variables")

if __name__ == "__main__":
    main()