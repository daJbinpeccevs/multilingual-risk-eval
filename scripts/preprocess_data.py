#!/usr/bin/env python3
"""
Data preprocessing script for multilingual risk evaluation.

This script helps prepare and process evaluation data, including:
- Loading and validating prompt data
- Generating custom prompt sets
- Preprocessing evaluation results
- Data format conversion and validation
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from utils.prompt_builder import PromptBuilder


class DataPreprocessor:
    """Data preprocessing utilities for evaluation pipeline."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize preprocessor with data directory."""
        self.data_dir = data_dir
        self.prompts_dir = os.path.join(data_dir, "prompts")
        self.logger = setup_logger("data_preprocessor")
        
        # Ensure directories exist
        os.makedirs(self.prompts_dir, exist_ok=True)
    
    def validate_prompt_data(self, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate prompt data structure and content.
        
        Args:
            prompts: List of prompt dictionaries
            
        Returns:
            Dict containing validation results
        """
        validation_results = {
            "valid": True,
            "total_prompts": len(prompts),
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        required_fields = ["id", "prompt", "language", "domain"]
        optional_fields = ["base_prompt", "risk_level"]
        
        languages = set()
        domains = set()
        risk_levels = set()
        
        for i, prompt_data in enumerate(prompts):
            # Check required fields
            for field in required_fields:
                if field not in prompt_data:
                    validation_results["errors"].append(
                        f"Prompt {i}: Missing required field '{field}'"
                    )
                    validation_results["valid"] = False
                elif not prompt_data[field]:
                    validation_results["warnings"].append(
                        f"Prompt {i}: Empty value for field '{field}'"
                    )
            
            # Collect statistics
            if "language" in prompt_data:
                languages.add(prompt_data["language"])
            if "domain" in prompt_data:
                domains.add(prompt_data["domain"])
            if "risk_level" in prompt_data:
                risk_levels.add(prompt_data["risk_level"])
            
            # Validate prompt content
            if "prompt" in prompt_data:
                prompt_text = prompt_data["prompt"]
                if len(prompt_text) < 10:
                    validation_results["warnings"].append(
                        f"Prompt {i}: Very short prompt text (< 10 characters)"
                    )
                elif len(prompt_text) > 1000:
                    validation_results["warnings"].append(
                        f"Prompt {i}: Very long prompt text (> 1000 characters)"
                    )
            
            # Check for duplicate IDs
            prompt_id = prompt_data.get("id", "")
            duplicate_ids = [p.get("id") for p in prompts].count(prompt_id)
            if duplicate_ids > 1:
                validation_results["errors"].append(
                    f"Prompt {i}: Duplicate ID '{prompt_id}'"
                )
                validation_results["valid"] = False
        
        # Store statistics
        validation_results["statistics"] = {
            "languages": sorted(list(languages)),
            "domains": sorted(list(domains)),
            "risk_levels": sorted(list(risk_levels)),
            "language_counts": {lang: sum(1 for p in prompts if p.get("language") == lang) for lang in languages},
            "domain_counts": {domain: sum(1 for p in prompts if p.get("domain") == domain) for domain in domains}
        }
        
        self.logger.info(f"Validated {len(prompts)} prompts")
        self.logger.info(f"Found {len(validation_results['errors'])} errors, {len(validation_results['warnings'])} warnings")
        
        return validation_results
    
    def generate_prompt_dataset(
        self,
        languages: List[str],
        domains: List[str],
        samples_per_combination: int,
        output_file: str,
        prompt_template: Optional[str] = None
    ) -> str:
        """
        Generate a complete prompt dataset.
        
        Args:
            languages: List of language codes
            domains: List of domain names
            samples_per_combination: Number of samples per language-domain combination
            output_file: Output filename
            prompt_template: Optional prompt template
            
        Returns:
            str: Path to generated file
        """
        self.logger.info(f"Generating prompt dataset for {len(languages)} languages, {len(domains)} domains")
        
        builder = PromptBuilder(self.prompts_dir)
        prompts = builder.build_prompts(
            languages=languages,
            domains=domains,
            num_samples=samples_per_combination,
            prompt_template=prompt_template
        )
        
        # Validate generated prompts
        validation = self.validate_prompt_data(prompts)
        if not validation["valid"]:
            self.logger.error("Generated prompts failed validation")
            for error in validation["errors"]:
                self.logger.error(f"  - {error}")
            raise ValueError("Generated prompts are invalid")
        
        # Save to file
        output_path = os.path.join(self.prompts_dir, output_file)
        builder.save_prompts(prompts, output_file)
        
        self.logger.info(f"Generated {len(prompts)} prompts and saved to {output_path}")
        return output_path
    
    def convert_prompt_format(
        self,
        input_file: str,
        output_file: str,
        input_format: str = "json",
        output_format: str = "json"
    ) -> str:
        """
        Convert prompt data between different formats.
        
        Args:
            input_file: Input file path
            output_file: Output file path
            input_format: Input format (json, csv, txt)
            output_format: Output format (json, csv, txt)
            
        Returns:
            str: Path to converted file
        """
        self.logger.info(f"Converting {input_file} from {input_format} to {output_format}")
        
        # Load input data
        if input_format == "json":
            with open(input_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
        else:
            raise NotImplementedError(f"Input format {input_format} not yet supported")
        
        # Validate input data
        validation = self.validate_prompt_data(prompts)
        if not validation["valid"]:
            self.logger.warning("Input data has validation errors - proceeding anyway")
            for error in validation["errors"]:
                self.logger.warning(f"  - {error}")
        
        # Save in output format
        if output_format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2)
        elif output_format == "csv":
            import pandas as pd
            df = pd.DataFrame(prompts)
            df.to_csv(output_file, index=False, encoding='utf-8')
        elif output_format == "txt":
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, prompt_data in enumerate(prompts):
                    f.write(f"=== Prompt {i+1} ===\n")
                    f.write(f"ID: {prompt_data.get('id', 'N/A')}\n")
                    f.write(f"Language: {prompt_data.get('language', 'N/A')}\n")
                    f.write(f"Domain: {prompt_data.get('domain', 'N/A')}\n")
                    f.write(f"Prompt: {prompt_data.get('prompt', 'N/A')}\n\n")
        else:
            raise NotImplementedError(f"Output format {output_format} not yet supported")
        
        self.logger.info(f"Converted {len(prompts)} prompts to {output_file}")
        return output_file
    
    def analyze_prompt_distribution(self, prompts_file: str) -> Dict[str, Any]:
        """
        Analyze the distribution of prompts across languages and domains.
        
        Args:
            prompts_file: Path to prompts JSON file
            
        Returns:
            Dict containing analysis results
        """
        self.logger.info(f"Analyzing prompt distribution in {prompts_file}")
        
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        analysis = {
            "total_prompts": len(prompts),
            "languages": {},
            "domains": {},
            "language_domain_matrix": {},
            "prompt_length_stats": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Collect data
        prompt_lengths = []
        for prompt_data in prompts:
            lang = prompt_data.get("language", "unknown")
            domain = prompt_data.get("domain", "unknown")
            prompt_text = prompt_data.get("prompt", "")
            
            # Language counts
            analysis["languages"][lang] = analysis["languages"].get(lang, 0) + 1
            
            # Domain counts
            analysis["domains"][domain] = analysis["domains"].get(domain, 0) + 1
            
            # Language-domain matrix
            if lang not in analysis["language_domain_matrix"]:
                analysis["language_domain_matrix"][lang] = {}
            analysis["language_domain_matrix"][lang][domain] = \
                analysis["language_domain_matrix"][lang].get(domain, 0) + 1
            
            # Prompt lengths
            prompt_lengths.append(len(prompt_text))
        
        # Calculate prompt length statistics
        if prompt_lengths:
            analysis["prompt_length_stats"] = {
                "mean": sum(prompt_lengths) / len(prompt_lengths),
                "min": min(prompt_lengths),
                "max": max(prompt_lengths),
                "median": sorted(prompt_lengths)[len(prompt_lengths) // 2]
            }
        
        self.logger.info(f"Analysis complete: {analysis['total_prompts']} prompts across {len(analysis['languages'])} languages and {len(analysis['domains'])} domains")
        
        return analysis
    
    def create_sample_dataset(self, output_file: str = "sample_prompts.json", num_samples: int = 5):
        """Create a small sample dataset for testing."""
        self.logger.info(f"Creating sample dataset with {num_samples} samples per combination")
        
        sample_languages = ["en", "zh"]
        sample_domains = ["healthcare", "legal"]
        
        return self.generate_prompt_dataset(
            languages=sample_languages,
            domains=sample_domains,
            samples_per_combination=num_samples,
            output_file=output_file
        )


def main():
    """Main entry point for data preprocessing."""
    parser = argparse.ArgumentParser(
        description="Preprocess data for multilingual risk evaluation"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate prompts command
    gen_parser = subparsers.add_parser("generate", help="Generate prompt dataset")
    gen_parser.add_argument("--languages", nargs="+", default=["en", "zh", "es", "fr"],
                           help="Languages to include")
    gen_parser.add_argument("--domains", nargs="+", default=["healthcare", "legal", "education"],
                           help="Domains to include")
    gen_parser.add_argument("--samples", type=int, default=10,
                           help="Samples per language-domain combination")
    gen_parser.add_argument("--output", default="generated_prompts.json",
                           help="Output filename")
    gen_parser.add_argument("--template", help="Prompt template file")
    
    # Validate prompts command
    val_parser = subparsers.add_parser("validate", help="Validate prompt dataset")
    val_parser.add_argument("input_file", help="Input prompts file")
    val_parser.add_argument("--output", help="Save validation report to file")
    
    # Convert format command
    conv_parser = subparsers.add_parser("convert", help="Convert prompt format")
    conv_parser.add_argument("input_file", help="Input file")
    conv_parser.add_argument("output_file", help="Output file")
    conv_parser.add_argument("--input-format", default="json", choices=["json", "csv", "txt"])
    conv_parser.add_argument("--output-format", default="json", choices=["json", "csv", "txt"])
    
    # Analyze command
    ana_parser = subparsers.add_parser("analyze", help="Analyze prompt distribution")
    ana_parser.add_argument("input_file", help="Input prompts file")
    ana_parser.add_argument("--output", help="Save analysis report to file")
    
    # Sample dataset command
    sample_parser = subparsers.add_parser("sample", help="Create sample dataset")
    sample_parser.add_argument("--samples", type=int, default=3,
                              help="Samples per combination")
    sample_parser.add_argument("--output", default="sample_prompts.json",
                              help="Output filename")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    preprocessor = DataPreprocessor()
    
    try:
        if args.command == "generate":
            # Load template if provided
            template = None
            if args.template:
                with open(args.template, 'r', encoding='utf-8') as f:
                    template = f.read()
            
            output_path = preprocessor.generate_prompt_dataset(
                languages=args.languages,
                domains=args.domains,
                samples_per_combination=args.samples,
                output_file=args.output,
                prompt_template=template
            )
            print(f"Generated prompts saved to: {output_path}")
        
        elif args.command == "validate":
            with open(args.input_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            validation = preprocessor.validate_prompt_data(prompts)
            
            print(f"Validation Results:")
            print(f"  Valid: {validation['valid']}")
            print(f"  Total Prompts: {validation['total_prompts']}")
            print(f"  Errors: {len(validation['errors'])}")
            print(f"  Warnings: {len(validation['warnings'])}")
            
            if validation['errors']:
                print("\nErrors:")
                for error in validation['errors']:
                    print(f"  - {error}")
            
            if validation['warnings']:
                print("\nWarnings:")
                for warning in validation['warnings']:
                    print(f"  - {warning}")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(validation, f, ensure_ascii=False, indent=2)
                print(f"\nValidation report saved to: {args.output}")
        
        elif args.command == "convert":
            output_path = preprocessor.convert_prompt_format(
                input_file=args.input_file,
                output_file=args.output_file,
                input_format=args.input_format,
                output_format=args.output_format
            )
            print(f"Converted file saved to: {output_path}")
        
        elif args.command == "analyze":
            analysis = preprocessor.analyze_prompt_distribution(args.input_file)
            
            print(f"Prompt Distribution Analysis:")
            print(f"  Total Prompts: {analysis['total_prompts']}")
            print(f"  Languages: {list(analysis['languages'].keys())}")
            print(f"  Domains: {list(analysis['domains'].keys())}")
            
            print(f"\nLanguage Distribution:")
            for lang, count in analysis['languages'].items():
                percentage = (count / analysis['total_prompts']) * 100
                print(f"  {lang}: {count} ({percentage:.1f}%)")
            
            print(f"\nDomain Distribution:")
            for domain, count in analysis['domains'].items():
                percentage = (count / analysis['total_prompts']) * 100
                print(f"  {domain}: {count} ({percentage:.1f}%)")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2)
                print(f"\nAnalysis report saved to: {args.output}")
        
        elif args.command == "sample":
            output_path = preprocessor.create_sample_dataset(
                output_file=args.output,
                num_samples=args.samples
            )
            print(f"Sample dataset saved to: {output_path}")
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()