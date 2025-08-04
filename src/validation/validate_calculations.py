#!/usr/bin/env python3
"""
Validation Script: Reproduce and verify calculations from original benchmark data
"""

import json
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from datetime import datetime

def load_original_benchmark_data():
    """Load the original production benchmark results"""
    try:
        with open('/home/ubuntu/voyager-sdk/production_benchmark_results_20250803_191118.json', 'r') as f:
            data = json.load(f)
        print("✅ Original benchmark data loaded successfully")
        return data
    except FileNotFoundError:
        print("❌ Original benchmark data file not found")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON data: {e}")
        return None

def extract_all_measurements(data):
    """Extract all individual measurements from the benchmark data"""
    all_measurements = []
    
    if "detailed_results" in data:
        for model_name, model_results in data["detailed_results"].items():
            for config_name, config_data in model_results.items():
                if "measurements" in config_data:
                    for measurement in config_data["measurements"]:
                        if measurement.get("is_valid", True):
                            all_measurements.append(measurement)
    
    print(f"✅ Extracted {len(all_measurements)} valid measurements")
    return all_measurements

def validate_mathematical_consistency(measurements):
    """Validate mathematical consistency of all measurements"""
    print("\n🔬 Validating Mathematical Consistency")
    print("=" * 40)
    
    validation_results = {
        "total_measurements": len(measurements),
        "consistency_checks": 0,
        "consistency_failures": 0,
        "failed_measurements": []
    }
    
    for i, measurement in enumerate(measurements):
        validation_results["consistency_checks"] += 1
        
        # Extract values
        throughput = measurement.get("throughput_fps", 0)
        power = measurement.get("power_consumption_watts", 1)
        efficiency = measurement.get("efficiency_fps_per_watt", 0)
        latency = measurement.get("latency_ms", 0)
        batch_size = measurement.get("batch_size", 1)
        
        # Consistency check 1: Efficiency = Throughput / Power
        expected_efficiency = throughput / power if power > 0 else 0
        efficiency_error = abs(efficiency - expected_efficiency)
        efficiency_tolerance = 0.01  # 1% tolerance
        
        if efficiency_error > efficiency_tolerance and efficiency > 0:
            validation_results["consistency_failures"] += 1
            validation_results["failed_measurements"].append({
                "measurement_index": i,
                "test": "efficiency_calculation",
                "expected": expected_efficiency,
                "actual": efficiency,
                "error": efficiency_error
            })
        
        # Consistency check 2: Throughput = Batch_size / (Latency_ms / 1000)
        if latency > 0:
            expected_throughput = batch_size / (latency / 1000)
            throughput_error = abs(throughput - expected_throughput)
            throughput_tolerance = throughput * 0.05  # 5% tolerance
            
            if throughput_error > throughput_tolerance:
                validation_results["consistency_failures"] += 1
                validation_results["failed_measurements"].append({
                    "measurement_index": i,
                    "test": "throughput_calculation",
                    "expected": expected_throughput,
                    "actual": throughput,
                    "error": throughput_error
                })
    
    # Calculate success rate
    success_rate = (validation_results["consistency_checks"] - validation_results["consistency_failures"]) / validation_results["consistency_checks"] * 100
    
    print(f"Total consistency checks: {validation_results['consistency_checks']}")
    print(f"Failed checks: {validation_results['consistency_failures']}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 95.0:
        print("✅ Mathematical consistency validation PASSED")
    else:
        print("❌ Mathematical consistency validation FAILED")
        print(f"First few failures: {validation_results['failed_measurements'][:3]}")
    
    return validation_results

def reproduce_summary_statistics(measurements):
    """Reproduce and validate summary statistics"""
    print("\n📊 Reproducing Summary Statistics")
    print("=" * 40)
    
    # Extract metric arrays
    latencies = [m["latency_ms"] for m in measurements]
    throughputs = [m["throughput_fps"] for m in measurements]
    powers = [m["power_consumption_watts"] for m in measurements]
    efficiencies = [m["efficiency_fps_per_watt"] for m in measurements]
    temperatures = [m["temperature_celsius"] for m in measurements]
    
    # Calculate comprehensive statistics
    stats_results = {
        "power_consumption_watts": {
            "count": len(powers),
            "mean": np.mean(powers),
            "std": np.std(powers, ddof=1),
            "min": np.min(powers),
            "max": np.max(powers),
            "median": np.median(powers),
            "q25": np.percentile(powers, 25),
            "q75": np.percentile(powers, 75),
            "confidence_interval_95": None
        },
        "throughput_fps": {
            "count": len(throughputs),
            "mean": np.mean(throughputs),
            "std": np.std(throughputs, ddof=1),
            "min": np.min(throughputs),
            "max": np.max(throughputs),
            "median": np.median(throughputs),
            "q25": np.percentile(throughputs, 25),
            "q75": np.percentile(throughputs, 75)
        },
        "efficiency_fps_per_watt": {
            "count": len(efficiencies),
            "mean": np.mean(efficiencies),
            "std": np.std(efficiencies, ddof=1),
            "min": np.min(efficiencies),
            "max": np.max(efficiencies),
            "median": np.median(efficiencies),
            "q25": np.percentile(efficiencies, 25),
            "q75": np.percentile(efficiencies, 75)
        },
        "temperature_celsius": {
            "count": len(temperatures),
            "mean": np.mean(temperatures),
            "std": np.std(temperatures, ddof=1),
            "min": np.min(temperatures),
            "max": np.max(temperatures),
            "median": np.median(temperatures)
        }
    }
    
    # Calculate 95% confidence intervals
    for metric_name, metric_data in stats_results.items():
        if metric_name == "temperature_celsius":
            continue  # Skip CI for temperature
            
        data_array = {
            "power_consumption_watts": powers,
            "throughput_fps": throughputs,
            "efficiency_fps_per_watt": efficiencies
        }[metric_name]
        
        n = len(data_array)
        mean = metric_data["mean"]
        std = metric_data["std"]
        
        # t-distribution confidence interval
        t_value = stats.t.ppf(0.975, n - 1)  # 95% CI, two-tailed
        margin_error = t_value * (std / np.sqrt(n))
        
        ci_lower = mean - margin_error
        ci_upper = mean + margin_error
        
        metric_data["confidence_interval_95"] = [ci_lower, ci_upper]
        metric_data["margin_of_error"] = margin_error
    
    # Display results
    print("Summary Statistics (Reproduced):")
    for metric_name, metric_data in stats_results.items():
        print(f"\n{metric_name.replace('_', ' ').title()}:")
        print(f"  Count: {metric_data['count']}")
        print(f"  Mean: {metric_data['mean']:.2f}")
        print(f"  Std Dev: {metric_data['std']:.2f}")
        print(f"  Min: {metric_data['min']:.2f}")
        print(f"  Max: {metric_data['max']:.2f}")
        print(f"  Median: {metric_data['median']:.2f}")
        
        if metric_data.get("confidence_interval_95"):
            ci = metric_data["confidence_interval_95"]
            print(f"  95% CI: [{ci[0]:.2f}, {ci[1]:.2f}]")
    
    return stats_results

def identify_peak_configurations(measurements):
    """Identify and validate peak performance configurations"""
    print("\n🏆 Identifying Peak Performance Configurations")
    print("=" * 50)
    
    # Group measurements by configuration
    config_groups = {}
    for measurement in measurements:
        model = measurement.get("model_name", "unknown")
        cores = measurement.get("core_count", 1)
        batch = measurement.get("batch_size", 1)
        
        config_key = f"{model}_cores{cores}_batch{batch}"
        
        if config_key not in config_groups:
            config_groups[config_key] = []
        
        config_groups[config_key].append(measurement)
    
    # Find peak configurations
    peak_throughput = 0
    peak_efficiency = 0
    peak_throughput_config = None
    peak_efficiency_config = None
    peak_throughput_measurement = None
    peak_efficiency_measurement = None
    
    config_summaries = {}
    
    for config_key, config_measurements in config_groups.items():
        # Calculate config statistics
        throughputs = [m["throughput_fps"] for m in config_measurements]
        efficiencies = [m["efficiency_fps_per_watt"] for m in config_measurements]
        powers = [m["power_consumption_watts"] for m in config_measurements]
        
        config_summary = {
            "measurement_count": len(config_measurements),
            "avg_throughput": np.mean(throughputs),
            "max_throughput": np.max(throughputs),
            "avg_efficiency": np.mean(efficiencies),
            "max_efficiency": np.max(efficiencies),
            "avg_power": np.mean(powers)
        }
        
        config_summaries[config_key] = config_summary
        
        # Check for peak throughput
        max_tp = np.max(throughputs)
        if max_tp > peak_throughput:
            peak_throughput = max_tp
            peak_throughput_config = config_key
            # Find the specific measurement
            for m in config_measurements:
                if m["throughput_fps"] == max_tp:
                    peak_throughput_measurement = m
                    break
        
        # Check for peak efficiency
        max_eff = np.max(efficiencies)
        if max_eff > peak_efficiency:
            peak_efficiency = max_eff
            peak_efficiency_config = config_key
            # Find the specific measurement
            for m in config_measurements:
                if m["efficiency_fps_per_watt"] == max_eff:
                    peak_efficiency_measurement = m
                    break
    
    # Display results
    print(f"Peak Throughput: {peak_throughput:.1f} FPS")
    print(f"Configuration: {peak_throughput_config}")
    if peak_throughput_measurement:
        print(f"Power: {peak_throughput_measurement['power_consumption_watts']:.1f}W")
        print(f"Efficiency: {peak_throughput_measurement['efficiency_fps_per_watt']:.1f} FPS/W")
        print(f"Temperature: {peak_throughput_measurement['temperature_celsius']:.1f}°C")
    
    print(f"\nPeak Efficiency: {peak_efficiency:.2f} FPS/W")
    print(f"Configuration: {peak_efficiency_config}")
    if peak_efficiency_measurement:
        print(f"Throughput: {peak_efficiency_measurement['throughput_fps']:.1f} FPS")
        print(f"Power: {peak_efficiency_measurement['power_consumption_watts']:.1f}W")
        print(f"Temperature: {peak_efficiency_measurement['temperature_celsius']:.1f}°C")
    
    # Display top 5 configurations by throughput
    print("\nTop 5 Configurations by Average Throughput:")
    sorted_configs = sorted(config_summaries.items(), 
                          key=lambda x: x[1]["avg_throughput"], 
                          reverse=True)
    
    for i, (config_name, config_data) in enumerate(sorted_configs[:5]):
        print(f"{i+1}. {config_name}")
        print(f"   Avg Throughput: {config_data['avg_throughput']:.1f} FPS")
        print(f"   Max Throughput: {config_data['max_throughput']:.1f} FPS")
        print(f"   Avg Efficiency: {config_data['avg_efficiency']:.1f} FPS/W")
        print(f"   Avg Power: {config_data['avg_power']:.1f}W")
    
    return {
        "peak_throughput": peak_throughput,
        "peak_throughput_config": peak_throughput_config,
        "peak_throughput_measurement": peak_throughput_measurement,
        "peak_efficiency": peak_efficiency,
        "peak_efficiency_config": peak_efficiency_config,
        "peak_efficiency_measurement": peak_efficiency_measurement,
        "config_summaries": config_summaries
    }

def analyze_scaling_performance(measurements):
    """Analyze multi-core scaling performance"""
    print("\n📈 Analyzing Multi-Core Scaling Performance")
    print("=" * 45)
    
    # Group by model and batch size, then analyze core scaling
    scaling_analysis = {}
    
    for measurement in measurements:
        model = measurement.get("model_name", "unknown")
        cores = measurement.get("core_count", 1)
        batch = measurement.get("batch_size", 1)
        
        key = f"{model}_batch{batch}"
        
        if key not in scaling_analysis:
            scaling_analysis[key] = {}
        
        if cores not in scaling_analysis[key]:
            scaling_analysis[key][cores] = []
        
        scaling_analysis[key][cores].append(measurement)
    
    # Analyze scaling for each model/batch combination
    scaling_results = {}
    
    for combo_key, core_data in scaling_analysis.items():
        if len(core_data) < 2:  # Need at least 2 core counts for scaling analysis
            continue
        
        # Calculate average performance for each core count
        core_performance = {}
        for cores, measurements_list in core_data.items():
            throughputs = [m["throughput_fps"] for m in measurements_list]
            powers = [m["power_consumption_watts"] for m in measurements_list]
            efficiencies = [m["efficiency_fps_per_watt"] for m in measurements_list]
            
            core_performance[cores] = {
                "avg_throughput": np.mean(throughputs),
                "avg_power": np.mean(powers),
                "avg_efficiency": np.mean(efficiencies),
                "measurement_count": len(measurements_list)
            }
        
        # Calculate scaling metrics relative to 1 core
        if 1 in core_performance:
            baseline_throughput = core_performance[1]["avg_throughput"]
            
            scaling_metrics = {}
            for cores, perf_data in core_performance.items():
                if cores > 1:
                    scaling_factor = perf_data["avg_throughput"] / baseline_throughput
                    scaling_efficiency = scaling_factor / cores  # Perfect scaling would be 1.0
                    
                    scaling_metrics[cores] = {
                        "scaling_factor": scaling_factor,
                        "scaling_efficiency_percent": scaling_efficiency * 100,
                        "throughput_improvement": (scaling_factor - 1) * 100
                    }
            
            scaling_results[combo_key] = {
                "core_performance": core_performance,
                "scaling_metrics": scaling_metrics
            }
    
    # Display results
    for combo_key, results in scaling_results.items():
        print(f"\n{combo_key.replace('_', ' ').title()}:")
        
        core_perf = results["core_performance"]
        scaling_metrics = results["scaling_metrics"]
        
        # Show performance by core count
        for cores in sorted(core_perf.keys()):
            perf = core_perf[cores]
            print(f"  {cores} Core(s): {perf['avg_throughput']:.1f} FPS, {perf['avg_power']:.1f}W, {perf['avg_efficiency']:.1f} FPS/W")
        
        # Show scaling efficiency
        for cores in sorted(scaling_metrics.keys()):
            metrics = scaling_metrics[cores]
            print(f"  {cores} Core Scaling: {metrics['scaling_factor']:.2f}x speedup ({metrics['scaling_efficiency_percent']:.1f}% efficiency)")
    
    return scaling_results

def generate_validation_report(data):
    """Generate comprehensive validation report"""
    
    measurements = extract_all_measurements(data)
    
    report = {
        "validation_timestamp": datetime.now().isoformat(),
        "original_dataset_info": {
            "total_measurements": data.get("summary_statistics", {}).get("total_measurements", 0),
            "extracted_valid_measurements": len(measurements),
            "success_rate": len(measurements) / data.get("summary_statistics", {}).get("total_measurements", 1)
        }
    }
    
    # Perform all validations
    print("🔍 Comprehensive Validation of Original Benchmark Results")
    print("=" * 60)
    
    # Mathematical consistency validation
    consistency_results = validate_mathematical_consistency(measurements)
    report["mathematical_consistency"] = consistency_results
    
    # Summary statistics reproduction
    stats_results = reproduce_summary_statistics(measurements)
    report["reproduced_statistics"] = stats_results
    
    # Peak configuration identification
    peak_results = identify_peak_configurations(measurements)
    report["peak_configurations"] = peak_results
    
    # Scaling analysis
    scaling_results = analyze_scaling_performance(measurements)
    report["scaling_analysis"] = scaling_results
    
    # Overall validation assessment
    math_success_rate = (consistency_results["consistency_checks"] - consistency_results["consistency_failures"]) / consistency_results["consistency_checks"] * 100
    
    report["overall_assessment"] = {
        "mathematical_consistency_rate": math_success_rate,
        "data_quality": "EXCELLENT" if math_success_rate >= 95 else "GOOD" if math_success_rate >= 90 else "POOR",
        "statistical_validity": "HIGH" if len(measurements) > 1000 else "MEDIUM" if len(measurements) > 100 else "LOW",
        "validation_status": "PASSED" if math_success_rate >= 95 and len(measurements) > 1000 else "FAILED"
    }
    
    # Key findings summary
    print(f"\n🎯 Validation Summary")
    print("=" * 30)
    print(f"Mathematical Consistency: {math_success_rate:.1f}%")
    print(f"Data Quality: {report['overall_assessment']['data_quality']}")
    print(f"Statistical Validity: {report['overall_assessment']['statistical_validity']}")
    print(f"Overall Status: {report['overall_assessment']['validation_status']}")
    
    # Key performance metrics
    print(f"\n📊 Key Performance Metrics (Validated)")
    print("=" * 40)
    power_stats = stats_results["power_consumption_watts"]
    throughput_stats = stats_results["throughput_fps"]
    efficiency_stats = stats_results["efficiency_fps_per_watt"]
    
    print(f"Power Consumption: {power_stats['mean']:.2f} ± {power_stats['std']:.2f}W")
    if power_stats.get("confidence_interval_95"):
        ci = power_stats["confidence_interval_95"]
        print(f"  95% CI: [{ci[0]:.2f}, {ci[1]:.2f}]W")
    
    print(f"Peak Throughput: {peak_results['peak_throughput']:.1f} FPS ({peak_results['peak_throughput_config']})")
    print(f"Peak Efficiency: {peak_results['peak_efficiency']:.2f} FPS/W ({peak_results['peak_efficiency_config']})")
    
    # Save detailed report
    with open('/home/ubuntu/voyager-sdk/comprehensive-axelera-hailo-comparison/VALIDATION_CALCULATIONS_REPORT.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Detailed validation report saved to: VALIDATION_CALCULATIONS_REPORT.json")
    
    return report

def main():
    """Main validation execution"""
    
    print("Axelera AI Metis Benchmark Data Validation")
    print("=" * 50)
    print("Reproducing and validating calculations from original measurements...")
    
    # Load original data
    data = load_original_benchmark_data()
    if not data:
        return False
    
    # Generate comprehensive validation report
    report = generate_validation_report(data)
    
    # Final assessment
    if report["overall_assessment"]["validation_status"] == "PASSED":
        print("\n✅ All validations PASSED - Original benchmark data is mathematically consistent and statistically valid")
        print("🎯 Results can be used with high confidence for comparative analysis")
        return True
    else:
        print("\n❌ Validation FAILED - Check data quality and methodology")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)