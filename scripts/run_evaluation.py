#!/usr/bin/env python3
"""
Main evaluation script for multilingual risk evaluation.

This script runs comprehensive evaluations of language models across multiple 
languages and high-risk domains (healthcare, legal, education).
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from utils.prompt_builder import PromptBuilder
from utils.metrics import RiskEvaluator
from models.model_loader import load_model


class MultilingualRiskEvaluator:
    """Main evaluator class for multilingual risk assessment."""
    
    def __init__(self, config_path: str):
        """Initialize evaluator with configuration."""
        self.config = self._load_config(config_path)
        self.logger = setup_logger(
            log_level=self.config.get("log_level", "INFO"),
            log_dir="logs"
        )
        self.prompt_builder = PromptBuilder()
        self.risk_evaluator = RiskEvaluator()
        self.model = None
        
        self.logger.info(f"Initialized evaluator with config: {config_path}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Validate required fields
        required_fields = ["model", "languages", "domains", "num_samples", "output_path"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Required configuration field missing: {field}")
        
        return config
    
    def _load_model(self):
        """Load the specified model."""
        model_name = self.config["model"]
        model_params = self.config.get("model_params", {})
        
        self.logger.info(f"Loading model: {model_name}")
        
        try:
            self.model = load_model(model_name, **model_params)
            self.logger.info(f"Successfully loaded model: {model_name}")
            
            # Log model info
            model_info = self.model.get_model_info()
            self.logger.info(f"Model info: {model_info}")
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise
    
    def _generate_prompts(self) -> List[Dict[str, Any]]:
        """Generate evaluation prompts based on configuration."""
        languages = self.config["languages"]
        domains = self.config["domains"]
        num_samples = self.config["num_samples"]
        prompt_template = self.config.get("prompt_template")
        
        self.logger.info(f"Generating prompts for {len(languages)} languages, {len(domains)} domains, {num_samples} samples each")
        
        prompts = self.prompt_builder.build_prompts(
            languages=languages,
            domains=domains,
            num_samples=num_samples,
            prompt_template=prompt_template
        )
        
        # Save prompts if requested
        if self.config.get("save_prompts", False):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompts_file = f"data/prompts/evaluation_prompts_{timestamp}.json"
            self.prompt_builder.save_prompts(prompts, prompts_file)
        
        return prompts
    
    def _generate_responses(self, prompts: List[Dict[str, Any]]) -> List[str]:
        """Generate model responses for all prompts."""
        self.logger.info(f"Generating responses for {len(prompts)} prompts...")
        
        # Extract just the prompt text
        prompt_texts = [p["prompt"] for p in prompts]
        
        # Generate responses in batch
        responses = self.model.batch_generate(prompt_texts)
        
        self.logger.info(f"Generated {len(responses)} responses")
        return responses
    
    def _evaluate_responses(
        self, 
        prompts: List[Dict[str, Any]], 
        responses: List[str]
    ) -> List[Dict[str, Any]]:
        """Evaluate all responses for risk factors."""
        self.logger.info(f"Evaluating {len(responses)} responses...")
        
        evaluations = self.risk_evaluator.evaluate_responses(prompts, responses)
        
        # Log summary statistics
        summary_stats = self.risk_evaluator.get_summary_statistics(evaluations)
        self.logger.info("Evaluation Summary:")
        self.logger.info(f"  - Total evaluations: {summary_stats['total_evaluations']}")
        self.logger.info(f"  - Mean risk score: {summary_stats['risk_score_stats']['mean']:.3f}")
        self.logger.info(f"  - Mean safety score: {summary_stats['safety_score_stats']['mean']:.3f}")
        self.logger.info(f"  - High risk responses: {summary_stats['high_risk_count']}")
        
        # Log recommendation breakdown
        self.logger.info("Recommendations:")
        for rec, count in summary_stats['recommendation_counts'].items():
            self.logger.info(f"  - {rec}: {count}")
        
        return evaluations
    
    def _save_results(
        self, 
        prompts: List[Dict[str, Any]], 
        responses: List[str], 
        evaluations: List[Dict[str, Any]]
    ):
        """Save evaluation results to file."""
        output_path = self.config["output_path"]
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prepare results data
        results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "config": self.config,
                "model_info": self.model.get_model_info() if self.model else None,
                "total_prompts": len(prompts),
                "total_responses": len(responses),
                "total_evaluations": len(evaluations)
            },
            "summary_statistics": self.risk_evaluator.get_summary_statistics(evaluations),
            "evaluations": evaluations
        }
        
        # Optionally include individual responses
        if self.config.get("save_individual_responses", False):
            results["detailed_results"] = []
            for prompt, response, evaluation in zip(prompts, responses, evaluations):
                results["detailed_results"].append({
                    "prompt_data": prompt,
                    "response": response,
                    "evaluation": evaluation
                })
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Results saved to: {output_path}")
        
        # Also save a human-readable summary
        summary_path = output_path.replace('.json', '_summary.txt')
        self._save_summary_report(results, summary_path)
    
    def _save_summary_report(self, results: Dict[str, Any], summary_path: str):
        """Save a human-readable summary report."""
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("MULTILINGUAL RISK EVALUATION SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            metadata = results["metadata"]
            f.write(f"Evaluation Date: {metadata['timestamp']}\n")
            f.write(f"Model: {metadata.get('model_info', {}).get('model_name', 'Unknown')}\n")
            f.write(f"Total Evaluations: {metadata['total_evaluations']}\n\n")
            
            # Summary statistics
            stats = results["summary_statistics"]
            f.write("OVERALL STATISTICS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Mean Risk Score: {stats['risk_score_stats']['mean']:.3f}\n")
            f.write(f"Mean Safety Score: {stats['safety_score_stats']['mean']:.3f}\n")
            f.write(f"High Risk Responses: {stats['high_risk_count']}\n")
            f.write(f"Safe Responses: {stats['safe_response_count']}\n\n")
            
            # Recommendations
            f.write("RECOMMENDATION BREAKDOWN\n")
            f.write("-" * 25 + "\n")
            for rec, count in stats['recommendation_counts'].items():
                percentage = (count / stats['total_evaluations']) * 100
                f.write(f"{rec}: {count} ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Language breakdown
            f.write("RISK BY LANGUAGE\n")
            f.write("-" * 16 + "\n")
            for lang, risk_mean in stats['language_risk_means'].items():
                f.write(f"{lang}: {risk_mean:.3f}\n")
            f.write("\n")
            
            # Domain breakdown
            f.write("RISK BY DOMAIN\n")
            f.write("-" * 14 + "\n")
            for domain, risk_mean in stats['domain_risk_means'].items():
                f.write(f"{domain}: {risk_mean:.3f}\n")
        
        self.logger.info(f"Summary report saved to: {summary_path}")
    
    def run_evaluation(self):
        """Run the complete evaluation pipeline."""
        try:
            self.logger.info("Starting multilingual risk evaluation...")
            
            # Load model
            self._load_model()
            
            # Generate prompts
            prompts = self._generate_prompts()
            
            # Generate responses
            responses = self._generate_responses(prompts)
            
            # Evaluate responses
            evaluations = self._evaluate_responses(prompts, responses)
            
            # Save results
            self._save_results(prompts, responses, evaluations)
            
            self.logger.info("Evaluation completed successfully!")
            
            # Return results for potential further processing
            return {
                "prompts": prompts,
                "responses": responses,
                "evaluations": evaluations,
                "summary": self.risk_evaluator.get_summary_statistics(evaluations)
            }
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {str(e)}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run multilingual risk evaluation for language models"
    )
    parser.add_argument(
        "config",
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual API calls)"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No actual API calls will be made")
        # TODO: Implement dry-run mode with mock responses
        return
    
    try:
        evaluator = MultilingualRiskEvaluator(args.config)
        results = evaluator.run_evaluation()
        
        # Print quick summary to console
        summary = results["summary"]
        print(f"\nEVALUATION COMPLETED")
        print(f"Total Evaluations: {summary['total_evaluations']}")
        print(f"Mean Risk Score: {summary['risk_score_stats']['mean']:.3f}")
        print(f"Mean Safety Score: {summary['safety_score_stats']['mean']:.3f}")
        print(f"High Risk Count: {summary['high_risk_count']}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()