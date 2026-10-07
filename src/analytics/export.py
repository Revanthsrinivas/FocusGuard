# src/analytics/export.py
"""
Export data to CSV and PDF formats
"""

import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


class DataExporter:
    """Export focus data to various formats"""

    def __init__(self):
        self.data_file = Path("data/training_data.json")

    def export_csv(self, output_path="reports/focus_data.csv"):
        """Export to CSV"""
        if not self.data_file.exists():
            print("No data to export")
            return False

        with open(self.data_file, "r") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        Path(output_path).parent.mkdir(exist_ok=True)
        df.to_csv(output_path, index=False)

        print(f"✅ Exported {len(data)} records to {output_path}")
        return True

    def export_summary(self, output_path="reports/summary.txt"):
        """Export summary statistics"""
        if not self.data_file.exists():
            print("No data to export")
            return False

        with open(self.data_file, "r") as f:
            data = json.load(f)

        df = pd.DataFrame(data)

        if "focus_score" not in df.columns:
            print("No focus score present in data")
            return False

        summary = f"""
FOCUSGUARD DATA SUMMARY
=======================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Samples: {len(data)}

Focus Score Statistics:
- Mean: {df['focus_score'].mean():.1f}%
- Median: {df['focus_score'].median():.1f}%
- Std Dev: {df['focus_score'].std():.1f}%
- Min: {df['focus_score'].min():.0f}%
- Max: {df['focus_score'].max():.0f}%

Top 10 Apps:
{df['app_name'].value_counts().head(10).to_string()}

Time of Day Analysis:
- Morning (6-12): {df[df['hour'].between(6,12)]['focus_score'].mean():.1f}%
- Afternoon (12-18): {df[df['hour'].between(12,18)]['focus_score'].mean():.1f}%
- Evening (18-24): {df[df['hour'].between(18,24)]['focus_score'].mean():.1f}%
- Night (0-6): {df[df['hour'].between(0,6)]['focus_score'].mean():.1f}%
"""

        Path(output_path).parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            f.write(summary)

        print(f"✅ Summary saved to {output_path}")
        return True

    def export_weekly_report(self, output_path="reports/weekly_report.html"):
        """Export weekly report as HTML"""
        if not self.data_file.exists():
            print("No data to export")
            return False

        with open(self.data_file, "r") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        daily_stats = (
            df.groupby("date")
            .agg(
                {
                    "focus_score": ["mean", "count"],
                    "app_name": lambda x: (
                        x.value_counts().index[0] if len(x) > 0 else "None"
                    ),
                }
            )
            .round(2)
        )

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>FocusGuard Weekly Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #0f172a; color: #f1f5f9; }}
        h1 {{ color: #3b82f6; }}
        .stats {{ background: #1e293b; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #3b82f6; }}
        .good {{ color: #10b981; }}
        .warning {{ color: #f59e0b; }}
        .bad {{ color: #ef4444; }}
    </style>
</head>
<body>
    <h1>📊 FocusGuard Weekly Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="stats">
        <h2>Summary</h2>
        <p>Total Samples: {len(data)}</p>
        <p>Average Focus: <span class="{'good' if df['focus_score'].mean() > 70 else 'warning' if df['focus_score'].mean() > 40 else 'bad'}">{df['focus_score'].mean():.1f}%</span></p>
        <p>Best Day: {daily_stats['focus_score']['mean'].idxmax()} ({daily_stats['focus_score']['mean'].max():.1f}%)</p>
        <p>Worst Day: {daily_stats['focus_score']['mean'].idxmin()} ({daily_stats['focus_score']['mean'].min():.1f}%)</p>
    </div>
    
    <div class="stats">
        <h2>Daily Breakdown</h2>
        {daily_stats.to_html()}
    </div>
    
    <div class="stats">
        <h2>Recommendations</h2>
        <ul>
            <li>✓ Your best focus time: {df.groupby('hour')['focus_score'].mean().idxmax()}:00</li>
            <li>✓ Your most distracting app: {df[df['focus_score'] < 30]['app_name'].value_counts().index[0] if len(df[df['focus_score'] < 30]) > 0 else 'None'}</li>
            <li>✓ Keep up the momentum on {daily_stats['focus_score']['mean'].idxmax()}!</li>
        </ul>
    </div>
</body>
</html>
"""

        Path(output_path).parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html)

        print(f"✅ Weekly report saved to {output_path}")
        return True


if __name__ == "__main__":
    exporter = DataExporter()
    exporter.export_csv()
    exporter.export_summary()
    exporter.export_weekly_report()
