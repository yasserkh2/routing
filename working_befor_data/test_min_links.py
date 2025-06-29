from app.core.optimizer import RoutingOptimizer

def test_min_links():
    """Test the optimizer with minimum links constraint"""
    optimizer = RoutingOptimizer()
    
    # Example links data with different prices and SLAs
    links_data = {
        "link1": {"sla": 0.92, "price": 100, "provider": "Provider A"},
        "link2": {"sla": 0.90, "price": 120, "provider": "Provider B"},
        "link3": {"sla": 0.85, "price": 80, "provider": "Provider C"},
        "link4": {"sla": 0.95, "price": 150, "provider": "Provider D"},
        "link5": {"sla": 0.88, "price": 90, "provider": "Provider E"},
        "link6": {"sla": 0.93, "price": 130, "provider": "Provider F"},
    }
    target_sla = 90.0  # 90%
    
    # Test 1: Without minimum links constraint
    print("\n=== Test 1: Without minimum links constraint ===")
    result1 = optimizer.minimize_cost_with_target_sla(links_data, target_sla)
    
    print("Solver Status:", result1['status'])
    print("Optimal Allocation (fractions of total traffic):")
    active_links = 0
    for link_id, fraction in sorted(result1['allocation'].items(), key=lambda x: -x[1]):
        if fraction > 0.001:  # Only show links with significant traffic
            active_links += 1
            print(f"  {link_id}: {fraction:.3f} ({fraction*100:.1f}%)")
    print(f"Number of links used: {active_links}")
    print(f"Minimum Total Cost: {result1['min_cost']:.2f}")
    print(f"Achieved SLA: {result1['achieved_sla']*100:.2f}%")
    
    # Reset optimizer for next test
    optimizer.reset()
    
    # Test 2: With minimum links constraint (4 links) and minimum 5% traffic per link
    print("\n=== Test 2: With minimum 4 links constraint and minimum 5% traffic per link ===")
    result2 = optimizer.minimize_cost_with_target_sla(links_data, target_sla, min_links=4, min_traffic_per_link=0.05)
    
    print("Solver Status:", result2['status'])
    print("Optimal Allocation (fractions of total traffic):")
    active_links = 0
    for link_id, fraction in sorted(result2['allocation'].items(), key=lambda x: -x[1]):
        if fraction > 0.001:  # Only show links with significant traffic
            active_links += 1
            print(f"  {link_id}: {fraction:.3f} ({fraction*100:.1f}%)")
    print(f"Number of links used: {active_links}")
    print(f"Minimum Total Cost: {result2['min_cost']:.2f}")
    print(f"Achieved SLA: {result2['achieved_sla']*100:.2f}%")
    
    # Reset optimizer for next test
    optimizer.reset()
    
    # Test 3: With minimum links constraint (5 links) and minimum 5% traffic per link
    print("\n=== Test 3: With minimum 5 links constraint and minimum 5% traffic per link ===")
    result3 = optimizer.minimize_cost_with_target_sla(links_data, target_sla, min_links=5, min_traffic_per_link=0.05)
    
    print("Solver Status:", result3['status'])
    print("Optimal Allocation (fractions of total traffic):")
    active_links = 0
    for link_id, fraction in sorted(result3['allocation'].items(), key=lambda x: -x[1]):
        if fraction > 0.001:  # Only show links with significant traffic
            active_links += 1
            print(f"  {link_id}: {fraction:.3f} ({fraction*100:.1f}%)")
    print(f"Number of links used: {active_links}")
    print(f"Minimum Total Cost: {result3['min_cost']:.2f}")
    print(f"Achieved SLA: {result3['achieved_sla']*100:.2f}%")
    
    # Reset optimizer for next test
    optimizer.reset()
    
    # Test 4: With minimum links constraint (6 links) and minimum 5% traffic per link
    print("\n=== Test 4: With minimum 6 links constraint and minimum 5% traffic per link ===")
    result4 = optimizer.minimize_cost_with_target_sla(links_data, target_sla, min_links=6, min_traffic_per_link=0.05)
    
    print("Solver Status:", result4['status'])
    print("Optimal Allocation (fractions of total traffic):")
    active_links = 0
    for link_id, fraction in sorted(result4['allocation'].items(), key=lambda x: -x[1]):
        if fraction > 0.001:  # Only show links with significant traffic
            active_links += 1
            print(f"  {link_id}: {fraction:.3f} ({fraction*100:.1f}%)")
    print(f"Number of links used: {active_links}")
    print(f"Minimum Total Cost: {result4['min_cost']:.2f}")
    print(f"Achieved SLA: {result4['achieved_sla']*100:.2f}%")
    
    # Compare the results
    print("\n=== Comparison ===")
    print("No constraint:")
    print(f"  Cost: {result1['min_cost']:.2f}")
    print(f"  SLA: {result1['achieved_sla']*100:.2f}%")
    print(f"  Links used: {sum(1 for f in result1['allocation'].values() if f > 0.001)}")
    
    print("\n4 links constraint:")
    cost_diff_2 = result2['min_cost'] - result1['min_cost']
    print(f"  Cost: {result2['min_cost']:.2f} (Diff: {cost_diff_2:.2f}, {(cost_diff_2/result1['min_cost'])*100:.2f}% increase)")
    print(f"  SLA: {result2['achieved_sla']*100:.2f}%")
    print(f"  Links used: {sum(1 for f in result2['allocation'].values() if f > 0.001)}")
    
    print("\n5 links constraint:")
    cost_diff_3 = result3['min_cost'] - result1['min_cost']
    print(f"  Cost: {result3['min_cost']:.2f} (Diff: {cost_diff_3:.2f}, {(cost_diff_3/result1['min_cost'])*100:.2f}% increase)")
    print(f"  SLA: {result3['achieved_sla']*100:.2f}%")
    print(f"  Links used: {sum(1 for f in result3['allocation'].values() if f > 0.001)}")
    
    print("\n6 links constraint:")
    cost_diff_4 = result4['min_cost'] - result1['min_cost']
    print(f"  Cost: {result4['min_cost']:.2f} (Diff: {cost_diff_4:.2f}, {(cost_diff_4/result1['min_cost'])*100:.2f}% increase)")
    print(f"  SLA: {result4['achieved_sla']*100:.2f}%")
    print(f"  Links used: {sum(1 for f in result4['allocation'].values() if f > 0.001)}")

if __name__ == "__main__":
    test_min_links()