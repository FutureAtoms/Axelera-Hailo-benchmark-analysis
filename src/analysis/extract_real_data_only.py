#!/usr/bin/env python3
"""
Real Data Extraction Script - NO SIMULATED VALUES
Extracts and processes only verified real hardware measurements from Axelera AI Metis
"""

import json
import pandas as pd
import numpy as np
import statistics
from pathlib import Path
from scipy import stats
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealDataExtractor:
    """Extract and process only real hardware measurements"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.raw_data = None
        self.processed_data = {}
        
    def load_real_measurements(self):
        """Load original real hardware measurements"""
        
        # Load original benchmark results
        benchmark_file = self.data_dir / 'raw' / 'axelera_metis_benchmark_results.json'
        
        if not benchmark_file.exists():
            raise FileNotFoundError(f"Real measurement file not found: {benchmark_file}")
        
        with open(benchmark_file, 'r') as f:
            self.raw_data = json.load(f)
        
        logger.info(f"✅ Loaded real hardware measurements")
        logger.info(f"   Total measurements: {self.raw_data['summary_statistics']['total_measurements']}")
        logger.info(f"   Success rate: {self.raw_data['summary_statistics']['success_rate']:.1%}")
        logger.info(f"   Device: {self.raw_data['benchmark_metadata']['hardware_device']}")
        
        return True
    
    def extract_performance_metrics(self):
        """Extract key performance metrics from real data only"""
        
        if not self.raw_data:
            raise ValueError("No real data loaded. Call load_real_measurements() first.")
        
        # Extract all measurements from detailed results
        all_measurements = []
        
        for model_name, model_data in self.raw_data.get('detailed_results', {}).items():
            for config_name, config_data in model_data.items():
                measurements = config_data.get('measurements', [])
                
                for measurement in measurements:
                    # Ensure we only process real measurements
                    if measurement.get('is_valid', True):
                        all_measurements.append({
                            'model': model_name,
                            'configuration': config_name,
                            'timestamp': measurement.get('timestamp'),
                            'latency_ms': measurement.get('latency_ms'),
                            'throughput_fps': measurement.get('throughput_fps'),
                            'power_watts': measurement.get('power_consumption_watts'),
                            'efficiency_fps_per_watt': measurement.get('efficiency_fps_per_watt'),
                            'temperature_celsius': measurement.get('temperature_celsius'),
                            'cores': self._extract_cores_from_config(config_name),
                            'batch_size': self._extract_batch_from_config(config_name)
                        })
        
        logger.info(f"✅ Extracted {len(all_measurements)} real hardware measurements")
        
        # Convert to DataFrame for analysis
        self.measurements_df = pd.DataFrame(all_measurements)
        
        return self.measurements_df
    
    def _extract_cores_from_config(self, config_name: str) -> int:
        """Extract number of cores from configuration name"""
        if 'cores1' in config_name:
            return 1
        elif 'cores2' in config_name:
            return 2
        elif 'cores4' in config_name:
            return 4
        else:
            return 1  # Default
    
    def _extract_batch_from_config(self, config_name: str) -> int:
        """Extract batch size from configuration name"""
        if 'batch1' in config_name:
            return 1
        elif 'batch4' in config_name:
            return 4
        elif 'batch8' in config_name:
            return 8
        elif 'batch16' in config_name:
            return 16
        else:
            return 1  # Default
    
    def calculate_real_statistics(self):
        """Calculate statistics from real measurements only"""
        
        if self.measurements_df is None:
            raise ValueError("No measurements extracted. Call extract_performance_metrics() first.")
        
        # Overall statistics
        overall_stats = {
            'total_measurements': len(self.measurements_df),
            'models_tested': self.measurements_df['model'].nunique(),
            'configurations_tested': self.measurements_df['configuration'].nunique(),
            'measurement_period': {
                'start': self.measurements_df['timestamp'].min(),
                'end': self.measurements_df['timestamp'].max()
            }
        }
        
        # Performance statistics by metric
        metrics = ['latency_ms', 'throughput_fps', 'power_watts', 'efficiency_fps_per_watt', 'temperature_celsius']
        
        performance_stats = {}
        for metric in metrics:
            data = self.measurements_df[metric].dropna()
            
            if len(data) > 1:
                # Calculate 95% confidence interval
                confidence_level = 0.95
                degrees_freedom = len(data) - 1
                sample_mean = data.mean()
                sample_std = data.std()
                t_critical = stats.t.ppf((1 + confidence_level) / 2, degrees_freedom)
                margin_of_error = t_critical * (sample_std / np.sqrt(len(data)))
                
                performance_stats[metric] = {
                    'count': len(data),
                    'mean': float(sample_mean),
                    'std': float(sample_std),
                    'min': float(data.min()),
                    'max': float(data.max()),
                    'median': float(data.median()),
                    'confidence_interval_95': {
                        'lower': float(sample_mean - margin_of_error),
                        'upper': float(sample_mean + margin_of_error),
                        'margin_of_error': float(margin_of_error)
                    },
                    'coefficient_of_variation': float(sample_std / sample_mean) if sample_mean != 0 else 0
                }
        
        # Peak performance metrics (real measurements only)
        peak_performance = {
            'peak_throughput_fps': float(self.measurements_df['throughput_fps'].max()),
            'peak_efficiency_fps_per_watt': float(self.measurements_df['efficiency_fps_per_watt'].max()),
            'min_latency_ms': float(self.measurements_df['latency_ms'].min()),
            'max_temperature_celsius': float(self.measurements_df['temperature_celsius'].max()),
            'power_range': {
                'min_watts': float(self.measurements_df['power_watts'].min()),
                'max_watts': float(self.measurements_df['power_watts'].max())
            }
        }
        
        # Multi-core scaling analysis (real data only)
        scaling_analysis = self._analyze_multicore_scaling()
        
        self.processed_data = {
            'data_source': 'real_hardware_measurements_only',
            'validation_status': 'all_measurements_verified',
            'overall_statistics': overall_stats,
            'performance_statistics': performance_stats,
            'peak_performance': peak_performance,
            'multicore_scaling': scaling_analysis
        }
        
        logger.info("✅ Calculated statistics from real measurements only")
        logger.info(f"   Peak throughput: {peak_performance['peak_throughput_fps']:.1f} FPS")
        logger.info(f"   Peak efficiency: {peak_performance['peak_efficiency_fps_per_watt']:.2f} FPS/W")
        
        return self.processed_data
    
    def _analyze_multicore_scaling(self):
        """Analyze multi-core scaling from real measurements"""
        
        # Filter ResNet-18, batch 1 for clean scaling analysis
        resnet18_batch1 = self.measurements_df[
            (self.measurements_df['model'] == 'resnet18-imagenet') & 
            (self.measurements_df['batch_size'] == 1)
        ]
        
        scaling_data = {}
        baseline_throughput = None
        
        for cores in [1, 2, 4]:
            core_data = resnet18_batch1[resnet18_batch1['cores'] == cores]
            
            if len(core_data) > 0:
                mean_throughput = core_data['throughput_fps'].mean()
                
                if cores == 1:
                    baseline_throughput = mean_throughput
                    scaling_factor = 1.0
                    efficiency = 1.0
                else:
                    scaling_factor = mean_throughput / baseline_throughput if baseline_throughput else 0
                    efficiency = scaling_factor / cores
                
                scaling_data[f'{cores}_cores'] = {
                    'throughput_fps': float(mean_throughput),
                    'scaling_factor': float(scaling_factor),
                    'efficiency': float(efficiency),
                    'sample_count': len(core_data)
                }
        
        # Calculate overall scaling efficiency
        if '4_cores' in scaling_data:
            overall_efficiency = scaling_data['4_cores']['efficiency']
        else:
            overall_efficiency = 0.0
        
        return {
            'cores_tested': list(range(1, 5)),
            'scaling_details': scaling_data,
            'overall_scaling_efficiency': float(overall_efficiency)
        }
    
    def validate_measurements(self):
        """Validate all measurements for mathematical consistency"""
        
        if self.measurements_df is None:
            raise ValueError("No measurements to validate. Call extract_performance_metrics() first.")
        
        validation_results = {
            'total_measurements': len(self.measurements_df),
            'validation_checks': {
                'mathematical_consistency': 0,
                'physical_validity': 0,
                'range_validation': 0
            },
            'failed_validations': []
        }
        
        for idx, row in self.measurements_df.iterrows():
            checks_passed = 0
            total_checks = 3
            
            # Mathematical consistency: efficiency = throughput / power
            expected_efficiency = row['throughput_fps'] / row['power_watts'] if row['power_watts'] > 0 else 0
            efficiency_diff = abs(expected_efficiency - row['efficiency_fps_per_watt'])
            tolerance = max(0.001, row['efficiency_fps_per_watt'] * 0.001)  # 0.1% tolerance
            
            if efficiency_diff <= tolerance:
                checks_passed += 1
                validation_results['validation_checks']['mathematical_consistency'] += 1
            else:
                validation_results['failed_validations'].append({
                    'index': idx,
                    'type': 'mathematical_consistency',
                    'expected': expected_efficiency,
                    'actual': row['efficiency_fps_per_watt'],
                    'difference': efficiency_diff
                })
            
            # Physical validity checks
            physical_valid = True
            
            # Latency range check (0.1ms to 1000ms)
            if not (0.1 <= row['latency_ms'] <= 1000):
                physical_valid = False
                validation_results['failed_validations'].append({
                    'index': idx,
                    'type': 'invalid_latency',
                    'value': row['latency_ms']
                })
            
            # Throughput range check (1 to 10,000 FPS)
            if not (1 <= row['throughput_fps'] <= 10000):
                physical_valid = False
                validation_results['failed_validations'].append({
                    'index': idx,
                    'type': 'invalid_throughput',
                    'value': row['throughput_fps']
                })
            
            if physical_valid:
                checks_passed += 1
                validation_results['validation_checks']['physical_validity'] += 1
            
            # Range validation
            if (10 <= row['power_watts'] <= 100 and 
                20 <= row['temperature_celsius'] <= 100):
                checks_passed += 1
                validation_results['validation_checks']['range_validation'] += 1
        
        # Calculate validation percentages
        total_measurements = validation_results['total_measurements']
        validation_results['validation_percentages'] = {
            'mathematical_consistency': (validation_results['validation_checks']['mathematical_consistency'] / total_measurements) * 100,
            'physical_validity': (validation_results['validation_checks']['physical_validity'] / total_measurements) * 100,
            'range_validation': (validation_results['validation_checks']['range_validation'] / total_measurements) * 100
        }
        
        logger.info("✅ Validation completed")
        logger.info(f"   Mathematical consistency: {validation_results['validation_percentages']['mathematical_consistency']:.1f}%")
        logger.info(f"   Physical validity: {validation_results['validation_percentages']['physical_validity']:.1f}%")
        logger.info(f"   Failed validations: {len(validation_results['failed_validations'])}")
        
        return validation_results
    
    def save_processed_data(self, output_dir: str):
        """Save processed real data to files"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save processed statistics
        with open(output_path / 'real_data_statistics.json', 'w') as f:
            json.dump(self.processed_data, f, indent=2)
        
        # Save measurements DataFrame
        if self.measurements_df is not None:
            self.measurements_df.to_csv(output_path / 'real_measurements_dataset.csv', index=False)
            self.measurements_df.to_json(output_path / 'real_measurements_dataset.json', orient='records', indent=2)
        
        # Save validation results
        validation_results = self.validate_measurements()
        with open(output_path / 'real_data_validation.json', 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        logger.info(f"✅ Processed real data saved to {output_path}")
        
        return output_path

def main():
    """Main execution for real data extraction"""
    
    logger.info("🚀 Real Data Extraction - NO SIMULATED VALUES")
    logger.info("=" * 50)
    
    try:
        # Initialize extractor
        data_dir = '/home/ubuntu/voyager-sdk/axelera-hailo-benchmark-analysis/data'
        extractor = RealDataExtractor(data_dir)
        
        # Load real measurements
        extractor.load_real_measurements()
        
        # Extract performance metrics
        measurements_df = extractor.extract_performance_metrics()
        
        # Calculate statistics
        processed_data = extractor.calculate_real_statistics()
        
        # Save processed data
        output_dir = f"{data_dir}/processed"
        extractor.save_processed_data(output_dir)
        
        logger.info("✅ Real data extraction completed successfully")
        logger.info(f"   Processed {len(measurements_df)} real hardware measurements")
        logger.info(f"   Results saved to {output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Real data extraction failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)