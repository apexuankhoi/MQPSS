"""
Benchmark Runner & Scientific Plotting Script for MQPSS
Executes Discrete Event Simulation comparing FCFS vs Pure Priority vs MQPSS
Saves high-resolution figures for scientific publication & final report.
GVHD: ThS. Lê Văn Phong
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np
from simulations.des_simulator import EmergencyDepartmentSimulation

OUTPUT_DIR = os.path.dirname(__file__)

def run_comparative_benchmark(sim_hours: float = 48.0):
    """Chạy mô phỏng 48 giờ liên tục (khoảng 1.000+ lượt bệnh nhân) trên cả 3 giải thuật"""
    print(f"=== BẮT ĐẦU CHẠY BENCHMARK MÔ PHỎNG SỰ KIỆN RỜI RẠC ({sim_hours} GIỜ) ===")
    
    sim_duration = sim_hours * 60.0
    algorithms = ["FCFS", "PURE_PRIORITY", "MQPSS"]
    results = {}

    for algo in algorithms:
        print(f"--> Đang chạy mô phỏng thuật toán: {algo}...")
        sim = EmergencyDepartmentSimulation(
            algorithm=algo,
            num_doctors=5,
            sim_duration_minutes=sim_duration,
            seed=42 # Cố định seed để đảm bảo cùng 1 dòng bệnh nhân nhập viện
        )
        res = sim.run()
        results[algo] = res
        print(f"    + Tổng ca xử lý: {res['total_treated']}")
        print(f"    + Thời gian chờ TB: {res['overall_avg_wait_minutes']} phút")
        print(f"    + Tỷ lệ Starvation: {res['starvation_rate_percent']}%")
        print(f"    + Thời gian chờ ca ESI-1: {res['esi_1_avg_wait_minutes']} phút")

    # Lưu kết quả JSON
    json_path = os.path.join(OUTPUT_DIR, "benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"--> Đã lưu dữ liệu định lượng vào: {json_path}")

    # Vẽ và lưu biểu đồ
    plot_waiting_time_by_esi(results)
    plot_starvation_rate_by_esi(results)
    plot_overall_kpis(results)
    print("=== HOÀN TẤT TẠO TOÀN BỘ BIỂU ĐỒ KHOA HỌC ===")
    return results

def plot_waiting_time_by_esi(results):
    """Biểu đồ 1: So sánh thời gian chờ trung bình theo từng cấp độ ESI"""
    plt.figure(figsize=(10, 6))
    esi_levels = [1, 2, 3, 4, 5]
    x = np.arange(len(esi_levels))
    width = 0.25

    fcfs_waits = [results["FCFS"]["waiting_time_by_esi"].get(l, 0) for l in esi_levels]
    prio_waits = [results["PURE_PRIORITY"]["waiting_time_by_esi"].get(l, 0) for l in esi_levels]
    mqpss_waits = [results["MQPSS"]["waiting_time_by_esi"].get(l, 0) for l in esi_levels]

    plt.bar(x - width, fcfs_waits, width, label='FCFS Thuần Túy', color='#94a3b8')
    plt.bar(x, prio_waits, width, label='Pure Priority (Không Aging)', color='#f97316')
    plt.bar(x + width, mqpss_waits, width, label='MQPSS (Đề tài đề xuất)', color='#10b981')

    plt.xlabel('Mức Độ Nguy Kịch ESI (1: Nguy kịch -> 5: Không cấp)', fontsize=11, fontweight='bold')
    plt.ylabel('Thời Gian Chờ Trung Bình (Phút)', fontsize=11, fontweight='bold')
    plt.title('So Sánh Thời Gian Chờ Theo Từng Cấp Độ ESI\n(MQPSS giảm thiểu tối đa trễ nợ ca nguy kịch ESI 1-2)', fontsize=12, fontweight='bold')
    plt.xticks(x, ['ESI-1 (Đỏ)', 'ESI-2 (Cam)', 'ESI-3 (Vàng)', 'ESI-4 (Xanh)', 'ESI-5 (Ghi)'])
    plt.legend(frameon=True)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    out_path = os.path.join(OUTPUT_DIR, "benchmark_waiting_time_by_esi.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"--> Đã lưu biểu đồ: {out_path}")

def plot_starvation_rate_by_esi(results):
    """Biểu đồ 2: So sánh tỷ lệ đói tài nguyên (Starvation Rate %)"""
    plt.figure(figsize=(9, 5.5))
    esi_levels = [1, 2, 3, 4] # ESI 5 chuyển ngoại trú
    x = np.arange(len(esi_levels))
    width = 0.25

    fcfs_starv = [results["FCFS"]["starvation_rate_by_esi"].get(l, 0) for l in esi_levels]
    prio_starv = [results["PURE_PRIORITY"]["starvation_rate_by_esi"].get(l, 0) for l in esi_levels]
    mqpss_starv = [results["MQPSS"]["starvation_rate_by_esi"].get(l, 0) for l in esi_levels]

    plt.bar(x - width, fcfs_starv, width, label='FCFS Thuần Túy', color='#94a3b8')
    plt.bar(x, prio_starv, width, label='Pure Priority (Starvation cao ở ca 3-4)', color='#ef4444')
    plt.bar(x + width, mqpss_starv, width, label='MQPSS (Có Dynamic Aging)', color='#10b981')

    plt.xlabel('Mức Độ Nguy Kịch ESI', fontsize=11, fontweight='bold')
    plt.ylabel('Tỷ Lệ Bệnh Nhân Chờ Quá Hạn An Toàn (%)', fontsize=11, fontweight='bold')
    plt.title('Tỷ Lệ Bỏ Rơi Bệnh Nhân (Starvation Rate %)\n(Dynamic Aging trong MQPSS loại bỏ hiệu ứng bỏ rơi ca nhẹ)', fontsize=12, fontweight='bold')
    plt.xticks(x, ['ESI-1 (>2p)', 'ESI-2 (>15p)', 'ESI-3 (>60p)', 'ESI-4 (>120p)'])
    plt.legend(frameon=True)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    out_path = os.path.join(OUTPUT_DIR, "benchmark_starvation_rate.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"--> Đã lưu biểu đồ: {out_path}")

def plot_overall_kpis(results):
    """Biểu đồ 3: Tổng hợp các chỉ số KPI then chốt"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    algos = ['FCFS', 'Pure Priority', 'MQPSS']
    colors = ['#94a3b8', '#f97316', '#10b981']

    # KPI 1: ESI-1 Response Time (phút)
    esi1_waits = [results[a]["esi_1_avg_wait_minutes"] for a in ["FCFS", "PURE_PRIORITY", "MQPSS"]]
    axes[0].bar(algos, esi1_waits, color=colors)
    axes[0].set_title('Thời Gian Chờ Ca Nguy Kịch ESI-1 (phút)\n(Càng thấp càng tốt - Cứu mạng)', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('Phút')
    axes[0].grid(axis='y', linestyle='--', alpha=0.5)
    for i, v in enumerate(esi1_waits):
        axes[0].text(i, v + 0.5, f"{v:.1f}p", ha='center', fontweight='bold')

    # KPI 2: Overall Starvation Rate (%)
    starv_rates = [results[a]["starvation_rate_percent"] for a in ["FCFS", "PURE_PRIORITY", "MQPSS"]]
    axes[1].bar(algos, starv_rates, color=colors)
    axes[1].set_title('Tỷ Lệ Quá Hạn Toàn Viện (%)\n(Càng thấp càng tốt)', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('Phần trăm (%)')
    axes[1].grid(axis='y', linestyle='--', alpha=0.5)
    for i, v in enumerate(starv_rates):
        axes[1].text(i, v + 1.0, f"{v:.1f}%", ha='center', fontweight='bold')

    # KPI 3: Throughput (Bệnh nhân / Giờ)
    throughputs = [results[a]["throughput_per_hour"] for a in ["FCFS", "PURE_PRIORITY", "MQPSS"]]
    axes[2].bar(algos, throughputs, color=colors)
    axes[2].set_title('Năng Suất Xử Lý (Ca / Giờ)\n(Càng cao càng tốt)', fontsize=11, fontweight='bold')
    axes[2].set_ylabel('Ca/giờ')
    axes[2].grid(axis='y', linestyle='--', alpha=0.5)
    for i, v in enumerate(throughputs):
        axes[2].text(i, v + 0.3, f"{v:.1f}", ha='center', fontweight='bold')

    out_path = os.path.join(OUTPUT_DIR, "benchmark_summary_kpis.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"--> Đã lưu biểu đồ: {out_path}")

if __name__ == "__main__":
    run_comparative_benchmark(sim_hours=48.0)

