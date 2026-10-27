import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ReactECharts from 'echarts-for-react';
import { datasetService } from '../services/datasetService';
import { 
  BarChart2, 
  Save, 
  Sparkles, 
  AlertCircle, 
  CheckCircle2, 
  Download,
  Trash2
} from 'lucide-react';

export default function VisualizationPage() {
  const { datasetId } = useParams();
  const [dataset, setDataset] = useState(null);
  const [columns, setColumns] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [savedCharts, setSavedCharts] = useState([]);

  // Chart configuration state
  const [chartType, setChartType] = useState('bar');
  const [chartTitle, setChartTitle] = useState('My Chart');
  const [xAxis, setXAxis] = useState('');
  const [yAxis, setYAxis] = useState('');
  const [aggregation, setAggregation] = useState('count');
  const [topN, setTopN] = useState(20);

  // Rendered Chart Option for ECharts
  const [chartOption, setChartOption] = useState(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    loadDatasetAndRecs();
    loadSavedCharts();
  }, [datasetId]);

  useEffect(() => {
    if (xAxis) {
      renderChartData();
    }
  }, [chartType, xAxis, yAxis, aggregation, topN]);

  const loadDatasetAndRecs = async () => {
    try {
      const [dRes, pRes, rRes] = await Promise.all([
        datasetService.getDataset(datasetId),
        datasetService.getProfile(datasetId),
        datasetService.getRecommendations(datasetId),
      ]);
      setDataset(dRes.data);
      setRecommendations(rRes.data);
      const cols = pRes.data.columns.map((c) => c.column_name);
      setColumns(cols);

      // Auto-populate from top recommendation if available
      if (rRes.data && rRes.data.length > 0) {
        applyRecommendation(rRes.data[0]);
      } else if (cols.length > 0) {
        setXAxis(cols[0]);
      }
    } catch (err) {
      setErrorMsg('Failed to load dataset visualization settings.');
    }
  };

  const loadSavedCharts = async () => {
    try {
      const res = await datasetService.getCharts(datasetId);
      setSavedCharts(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const applyRecommendation = (rec) => {
    setChartType(rec.chart_type);
    setChartTitle(rec.title || 'Recommended Chart');
    setXAxis(rec.x_axis || '');
    setYAxis(rec.y_axis || '');
    setAggregation(rec.aggregation || 'count');
  };

  const renderChartData = async () => {
    try {
      setLoadingChart(true);
      setErrorMsg(null);
      const res = await datasetService.getChartData(datasetId, {
        chart_type: chartType,
        x_axis: xAxis,
        y_axis: yAxis || null,
        aggregation,
        top_n: topN,
        title: chartTitle,
      });

      const data = res.data;
      buildEChartsOption(data);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to aggregate chart data.');
      setChartOption(null);
    } finally {
      setLoadingChart(false);
    }
  };

  const buildEChartsOption = (data) => {
    if (chartType === 'pie') {
      setChartOption({
        title: { text: chartTitle, left: 'center', textStyle: { fontSize: 15, fontWeight: '600' } },
        tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c} ({d}%)' },
        legend: { bottom: '0%', left: 'center' },
        series: data.series,
      });
      return;
    }

    if (chartType === 'scatter') {
      setChartOption({
        title: { text: chartTitle, textStyle: { fontSize: 15, fontWeight: '600' } },
        tooltip: { trigger: 'item', formatter: (p) => `${xAxis}: ${p.value[0]}<br/>${yAxis}: ${p.value[1]}` },
        xAxis: { name: xAxis, type: 'value', splitLine: { lineStyle: { type: 'dashed' } } },
        yAxis: { name: yAxis, type: 'value', splitLine: { lineStyle: { type: 'dashed' } } },
        series: data.series,
      });
      return;
    }

    // Bar / Line / Histogram
    setChartOption({
      title: { text: chartTitle, textStyle: { fontSize: 15, fontWeight: '600' } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.categories || [],
        axisLabel: { rotate: data.categories?.length > 8 ? 30 : 0 },
      },
      yAxis: { type: 'value', name: yAxis ? `${aggregation.toUpperCase()}` : 'Count' },
      series: data.series.map((s) => ({
        ...s,
        itemStyle: { color: chartType === 'line' ? '#0284c7' : '#38bdf8' },
        smooth: chartType === 'line',
      })),
    });
  };

  const handleSaveChart = async () => {
    try {
      setErrorMsg(null);
      await datasetService.saveChart({
        dataset_id: datasetId,
        title: chartTitle,
        chart_type: chartType,
        configuration: {
          x_axis: xAxis,
          y_axis: yAxis,
          aggregation,
          top_n: topN,
        },
      });
      setStatusMsg('Chart successfully saved to project.');
      await loadSavedCharts();
    } catch (err) {
      setErrorMsg('Failed to save chart.');
    }
  };

  const handleDeleteChart = async (id) => {
    try {
      await datasetService.deleteChart(id);
      await loadSavedCharts();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Interactive Visualization Studio</h1>
          <p className="text-sm text-slate-500 mt-1">
            Server-side aggregations, rule-based chart recommendations, and Apache ECharts rendering.
          </p>
        </div>
        <button
          onClick={handleSaveChart}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs transition shadow-sm"
        >
          <Save className="w-3.5 h-3.5" />
          Save Chart
        </button>
      </div>

      {statusMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg text-xs flex items-center justify-between">
          <span>{statusMsg}</span>
          <button onClick={() => setStatusMsg(null)} className="hover:underline">Dismiss</button>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="hover:underline">Dismiss</button>
        </div>
      )}

      {/* Automatic Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-gradient-to-r from-sky-50 to-indigo-50 p-4 rounded-xl border border-sky-100 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-sky-900">
            <Sparkles className="w-4 h-4 text-sky-600" />
            Rule-Based Automatic Suggestions (Based on Data Profile):
          </div>
          <div className="flex flex-wrap gap-2">
            {recommendations.map((rec, i) => (
              <button
                key={i}
                onClick={() => applyRecommendation(rec)}
                className="px-3 py-1.5 bg-white hover:bg-sky-100/70 border border-sky-200 rounded-lg text-xs font-semibold text-slate-800 transition shadow-xs text-left"
              >
                {rec.title} <span className="text-[10px] text-sky-600 uppercase">({rec.chart_type})</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Workspace: Controls + Chart Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Controls (1 Col) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900">Configuration</h2>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Title</label>
            <input
              type="text"
              value={chartTitle}
              onChange={(e) => setChartTitle(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Chart Type</label>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
            >
              <option value="bar">Bar Chart</option>
              <option value="line">Line Chart</option>
              <option value="pie">Pie Chart</option>
              <option value="histogram">Histogram</option>
              <option value="scatter">Scatter Plot</option>
              <option value="area">Area Chart</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {chartType === 'histogram' ? 'Target Column' : 'X-Axis / Category'}
            </label>
            <select
              value={xAxis}
              onChange={(e) => setXAxis(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
            >
              {columns.map((col) => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>

          {!['histogram'].includes(chartType) && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Y-Axis / Metric {chartType !== 'pie' && <span className="text-slate-400 font-normal">(Optional for Count)</span>}
              </label>
              <select
                value={yAxis}
                onChange={(e) => setYAxis(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
              >
                <option value="">None (Count rows)</option>
                {columns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            </div>
          )}

          {yAxis && !['histogram', 'scatter'].includes(chartType) && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Aggregation</label>
              <select
                value={aggregation}
                onChange={(e) => setAggregation(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
              >
                <option value="avg">Average (Mean)</option>
                <option value="sum">Sum</option>
                <option value="min">Minimum</option>
                <option value="max">Maximum</option>
                <option value="count">Count</option>
              </select>
            </div>
          )}
        </div>

        {/* Chart Canvas (3 Cols) */}
        <div className="lg:col-span-3 space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm min-h-[440px] flex flex-col justify-center">
            {loadingChart ? (
              <div className="text-center text-sm text-slate-400">Aggregating dataset on server...</div>
            ) : chartOption ? (
              <ReactECharts option={chartOption} style={{ height: '400px', width: '100%' }} />
            ) : (
              <div className="text-center text-sm text-slate-400">Select valid columns to generate chart.</div>
            )}
          </div>

          {/* Saved Charts Gallery */}
          {savedCharts.length > 0 && (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900">Saved Charts for Dataset</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {savedCharts.map((sc) => {
                  const cfg = JSON.parse(sc.configuration_json || '{}');
                  return (
                    <div key={sc.id} className="p-3 border border-slate-200 rounded-lg flex items-center justify-between text-xs hover:border-sky-300 transition">
                      <div>
                        <p className="font-semibold text-slate-800">{sc.title}</p>
                        <p className="text-[10px] text-slate-400 uppercase mt-0.5">
                          {sc.chart_type} • {cfg.x_axis}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteChart(sc.id)}
                        className="text-slate-400 hover:text-red-600 p-1 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
