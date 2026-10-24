# Reproduce the analysis and publication charts

From the project root, after the experiment and capped-rate follow-up:

```bash
python3 analysis/summarize.py
```

The script requires all 12 main runs and all three capped-rate runs, computes per-group medians/minima/maxima, and derives container CPU consumption and throttling-period counters from before/after snapshots. It writes results/analysis.json. It does not pool percentiles or average p99 values.

The recorded Mongo shell output serializes some BSON integers as high/low objects; the analysis converts these before calculating elapsed time. CPU deltas include diagnostic process overhead. A throttled-period fraction is not a fraction of wall time spent throttled.

Charts use standard JFreeChart 1.5.5 and the complete runs.csv. For example:

```bash
mkdir -p .tools/chart
curl -fsSL https://repo.maven.apache.org/maven2/org/jfree/jfreechart/1.5.5/jfreechart-1.5.5.jar \
  -o .tools/chart/jfreechart-1.5.5.jar
javac -cp .tools/chart/jfreechart-1.5.5.jar analysis/PlotResults.java
mkdir -p figures
java -Djava.awt.headless=true -cp 'analysis:.tools/chart/jfreechart-1.5.5.jar' \
  PlotResults results/experiment-1/runs.csv figures/concurrency-results.png
```

This writes the combined figure and separate throughput-by-threads.png and latency-by-threads.png. Lines connect medians and dots show every repetition. The images are generated from captured data, not image generation. The article's conceptual cover was generated separately and is not performance evidence.
